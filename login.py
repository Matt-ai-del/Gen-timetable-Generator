import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import sqlite3
import hashlib
import random
import string
import re
import logging
import shutil
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import register_lecturer, get_pending_registrations, approve_lecturer, reject_lecturer, get_departments

class RemyConnection:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RemyConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._connection is None:
            self._connection = sqlite3.connect('users.db', check_same_thread=False)
            self._connection.row_factory = sqlite3.Row

    def get_connection(self):
        return self._connection

    def get_cursor(self):
        return self._connection.cursor()

    def commit(self):
        self._connection.commit()

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def __del__(self):
        self.close()

# Set up audit logger
logging.basicConfig(
    filename='audit.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_audit(action, username=None, details=None):
    msg = f"ACTION: {action}"
    if username:
        msg += f" | USER: {username}"
    if details:
        msg += f" | DETAILS: {details}"
    logging.info(msg)

def initialize_session_state():
    "Initialize all session state variables"
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'is_admin' not in st.session_state:
        st.session_state['is_admin'] = False
    if 'show_registration' not in st.session_state:
        st.session_state['show_registration'] = False
    if 'show_reset' not in st.session_state:
        st.session_state['show_reset'] = False
    if 'show_admin_management' not in st.session_state:
        st.session_state['show_admin_management'] = False
    if 'reset_email' not in st.session_state:
        st.session_state['reset_email'] = None
    if 'role' not in st.session_state:
        st.session_state['role'] = None
    if 'show_register' not in st.session_state:
        st.session_state['show_register'] = False
    if 'show_forgot_password' not in st.session_state:
        st.session_state['show_forgot_password'] = False
    if 'show_lecturer_register' not in st.session_state:
        st.session_state['show_lecturer_register'] = False
    if 'needs_password_change' not in st.session_state:
        st.session_state['needs_password_change'] = False
    
    # Initialize database if needed
    print("Checking if database exists...")
    if not os.path.exists('users.db'):
        print("Database not found, initializing...")
        init_db()
    else:
        print("Database exists, verifying users...")
        remy = sqlite3.connect('users.db')
        remy = remy.cursor()
        remy.execute("SELECT username, is_admin FROM users")
        users = remy.fetchall()
        print("Current users:", users)
        remy.close()

def hash_password(password):
    return generate_password_hash(password)

def generate_reset_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def password_strength(password):
    if len(password) < 6:
        return 'Too short', 'red'
    score = 0
    if re.search(r'[a-z]', password):
        score += 1
    if re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'\d', password):
        score += 1
    if re.search(r'[^A-Za-z0-9]', password):
        score += 1
    if len(password) >= 12:
        score += 1
    if score <= 1:
        return 'Weak', 'orange'
    elif score == 2:
        return 'Moderate', 'gold'
    elif score == 3:
        return 'Strong', 'green'
    else:
        return 'Very Strong', 'darkgreen'

# Database setup
def init_db():
    try:
        print("Initializing database...")
        remy = RemyConnection()
        cursor = remy.get_cursor()
        
        # Create users table with role and password change tracking
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, 
                      password TEXT, 
                      is_admin INTEGER DEFAULT 0,
                      email TEXT,
                      role TEXT DEFAULT 'student',
                      reset_code TEXT,
                      reset_code_timestamp TIMESTAMP,
                      password_changed INTEGER DEFAULT 0)''')
        
        # Insert default admin if not exists
        cursor.execute("SELECT username FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            print("Creating default admin user...")
            hashed_password = hash_password('admin123')
            cursor.execute('INSERT INTO users (username, password, is_admin, email, role) VALUES (?, ?, ?, ?, ?)',
                     ('admin', hashed_password, 1, 'admin@msu.ac.zw', 'admin'))
        
        # Insert Matt as admin if not exists
        cursor.execute("SELECT username FROM users WHERE username = 'Matt'")
        if not cursor.fetchone():
            print("Creating Matt admin user...")
            hashed_password = hash_password('remy11')
            cursor.execute('INSERT INTO users (username, password, is_admin, email, role) VALUES (?, ?, ?, ?, ?)',
                     ('Matt', hashed_password, 1, 'matt@msu.ac.zw', 'admin'))
        
        # Verify users were created
        cursor.execute("SELECT username, is_admin, role FROM users")
        users = cursor.fetchall()
        print("Current users in database:", users)
        
        remy.commit()
        print("Database initialization complete!")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def verify_user(username, password):
    try:
        print(f"Attempting login for user: {username}")
        db = RemyConnection()
        cursor = db.get_cursor()
        
        # First check if this is a lecturer
        cursor.execute("""
            SELECT u.password, u.is_admin, u.role, u.email 
            FROM users u 
            WHERE LOWER(u.username) = ? AND u.role = 'lecturer'
        """, (username.lower(),))
        result = cursor.fetchone()
        
        if result:
            stored_password, is_admin, role, email = result
            print(f"Found lecturer: {username}, email: {email}")
            
            # Check if using default password and if password has been changed before
            cursor.execute("SELECT password_changed FROM users WHERE username = ?", (username,))
            password_result = cursor.fetchone()
            
            if not password_result:
                print(f"User {username} not found in password check")
                log_audit('Login Error', username, 'User not found in password check')
                return False
                
            password_changed = password_result['password_changed']
            
            # Check if password matches either default or stored hash
            if (password == 'mathy11' and not password_changed) or check_password_hash(stored_password, password):
                print("Lecturer login successful")
                st.session_state['is_admin'] = False
                st.session_state['role'] = 'lecturer'
                # If using default password and it hasn't been changed, force password change
                if password == 'mathy11' and not password_changed:
                    st.session_state['needs_password_change'] = True
                elif password == 'mathy11' and password_changed:
                    print("Default password no longer valid")
                    log_audit('Login Failure - Default Password Used', username)
                    return False
                log_audit('Login Success', username)
                return True
            else:
                print(f"Password verification failed for lecturer {username}")
                log_audit('Login Failure - Invalid Password', username)
        else:
            # Check for admin accounts
            if username.lower() == 'admin' and password == 'admin123':
                print("Admin login successful")
                st.session_state['is_admin'] = True
                st.session_state['role'] = 'admin'
                log_audit('Login Success', 'admin')
                return True
            elif username.lower() == 'matt' and password == 'remy11':
                print("Matt login successful")
                st.session_state['is_admin'] = True
                st.session_state['role'] = 'admin'
                log_audit('Login Success', 'Matt')
                return True
            
            # Check for other users
            cursor.execute("SELECT password, is_admin, role FROM users WHERE LOWER(username) = ?", (username.lower(),))
            result = cursor.fetchone()
            
            if result:
                stored_password, is_admin, role = result
                print(f"Found user: {username}, is_admin: {is_admin}, role: {role}")
                
                if check_password_hash(stored_password, password):
                    print("Password verification successful")
                    st.session_state['is_admin'] = bool(is_admin)
                    st.session_state['role'] = role if role else ('admin' if is_admin else 'student')
                    log_audit('Login Success', username)
                    return True
                else:
                    print(f"Password verification failed for user {username}")
                    log_audit('Login Failure - Invalid Password', username)
            else:
                print(f"User {username} not found")
                log_audit('Login Failure - User Not Found', username)
        
        return False
    except Exception as e:
        print(f"Error during login verification: {e}")
        log_audit('Login Error', username, str(e))
        return False

def create_user(username, password, is_admin=False, email=None, role='student'):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, is_admin, email, role) VALUES (?, ?, ?, ?, ?)",
                 (username, generate_password_hash(password), 1 if is_admin or role=='admin' else 0, email, role))
        conn.commit()
        log_audit('Admin Added' if is_admin or role=='admin' else 'User Added', username, f"email={email}, role={role}")
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_email(username):
    remy = sqlite3.connect('users.db')
    remy = remy.cursor()
    remy.execute('SELECT email FROM users WHERE username = ?', (username,))
    result = remy.fetchone()
    remy.close()
    return result[0] if result else None

def update_reset_code(username, reset_code):
    remy = sqlite3.connect('users.db')
    remy = remy.cursor()
    remy.execute('''
        UPDATE users 
        SET reset_code = ?, reset_code_timestamp = CURRENT_TIMESTAMP 
        WHERE username = ?
    ''', (reset_code, username))
    remy.commit()
    remy.close()

def verify_reset_code(username, code):
    remy = sqlite3.connect('users.db')
    remy = remy.cursor()
    remy.execute('''
        SELECT reset_code, reset_code_timestamp 
        FROM users 
        WHERE username = ? AND reset_code = ?
    ''', (username, code))
    result = remy.fetchone()
    remy.close()
    return bool(result)

def update_password(username, new_password, is_admin_reset=False):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # If admin is resetting the password, set password_changed to 0
        # If user is changing their own password, set password_changed to 1
        password_changed = 0 if is_admin_reset else 1
        
        cursor.execute('''
            UPDATE users 
            SET password = ?, 
                reset_code = NULL, 
                reset_code_timestamp = NULL,
                password_changed = ?
            WHERE username = ?
        ''', (generate_password_hash(new_password), password_changed, username))
        
        conn.commit()
        log_audit('Password Updated', 
                 username, 
                 f'reset_by_admin={is_admin_reset}')
        return True
    except Exception as e:
        print(f"Error updating password: {e}")
        log_audit('Password Update Failed', 
                 username, 
                 f'error={str(e)}')
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def force_password_change_page(username):
    st.subheader("Create New Password")
    st.warning("You are using a default password. Please create a new password to continue.")
    with st.form("force_change_password_form"):
        new_password = st.text_input("New Password", type="password", key="fc_new_password")
        confirm_password = st.text_input("Confirm New Password", type="password", key="fc_confirm_password")

        # Password strength meter
        if new_password:
            strength, color = password_strength(new_password)
            st.markdown(f'<span style="color:{color}; font-weight:bold;">Password strength: {strength}</span>', unsafe_allow_html=True)

        submit_button = st.form_submit_button("Set New Password")

        if submit_button:
            if not new_password or not confirm_password:
                st.error("Both password fields are required.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 6: # Consistent with password_strength logic
                st.error("Password must be at least 6 characters long.")
            else:
                if update_password(username, new_password, is_admin_reset=False):
                    st.session_state['needs_password_change'] = False
                    log_audit('Forced Password Change Success', username)
                    st.success("Password updated successfully! The application will now reload.")
                    import time
                    time.sleep(2) # Allow user to see the message
                    st.rerun()
                else:
                    st.error("Failed to update password. Please try again or contact an administrator.")
                    log_audit('Forced Password Change Failed', username)


# Registration page
def registration_page():
    st.subheader("Create New Account")
    with st.form("registration_form"):
        new_username = st.text_input("Choose Username")
        new_email = st.text_input("Email Address")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        role = "student"  # Only allow student registration
        is_admin = False
        
        # Password strength meter
        if new_password:
            strength, color = password_strength(new_password)
            st.markdown(f'<span style="color:{color}; font-weight:bold;">Password strength: {strength}</span>', unsafe_allow_html=True)
        
        submit = st.form_submit_button("Register")
        
        if submit:
            if new_password != confirm_password:
                st.error("Passwords do not match!")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long!")
            elif not new_email or '@' not in new_email:
                st.error("Please enter a valid email address!")
            else:
                if create_user(new_username, new_password, is_admin, new_email, role):
                    st.success("Registration successful! Please log in.")
                    log_audit('User Added', new_username, f"email={new_email}, role={role}")
                else:
                    st.error("Username or email already exists!")
                st.session_state['show_registration'] = False
                st.rerun()
    
    # Add Back to Login button
    if st.button("⬅️ Back to Login"):
        st.session_state['show_registration'] = False
        st.rerun()

# Password reset page
def password_reset_page():
    st.subheader("Password Reset")
    with st.form("reset_form"):
        email = st.text_input("Enter your email address")
        submit = st.form_submit_button("Reset Password")
        
        if submit:
            remy = sqlite3.connect('users.db')
            remy = remy.cursor()
            remy.execute('SELECT username FROM users WHERE email = ? LIMIT 1', (email,))
            result = remy.fetchone()
            remy.close()
            if result:
                st.session_state['reset_email'] = email
                st.success("Email found. Please enter your new password below.")
            else:
                st.error("Email not found!")

    if st.session_state.get('reset_email'):
        with st.form("set_new_password_form"):
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            # Password strength meter
            if new_password:
                strength, color = password_strength(new_password)
                st.markdown(f'<span style="color:{color}; font-weight:bold;">Password strength: {strength}</span>', unsafe_allow_html=True)
            submit = st.form_submit_button("Set New Password")
            if submit:
                if new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters long!")
                else:
                    remy = RemyConnection()
                    cursor = remy.get_cursor()
                    cursor.execute('UPDATE users SET password = ? WHERE email = ?', (generate_password_hash(new_password), st.session_state['reset_email']))
                    remy.commit()
                    log_audit('Password Reset', None, f"email={st.session_state['reset_email']}")
                    st.success("Password has been reset successfully!")
                    st.session_state['reset_email'] = None
                    st.session_state['show_reset'] = False
                    st.rerun()

    # Add Back to Login button
    if st.button("⬅️ Back to Login"):
        st.session_state['show_reset'] = False
        st.rerun()

# Login page
def login_page():
    # Styled compact login form with icons
    st.markdown("""
        <style>
        .main, .stApp {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 0;
        }
        .login-container {
            background-color: #fff;
            padding: 1.2rem 1.5rem 1.2rem 1.5rem;
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(74,107,255,0.10);
            max-width: 340px;
            width: 100%;
            margin: auto;
            position: relative;
        }
        .login-title {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 0.7rem;
            text-align: center;
            color: #4a6bff;
            letter-spacing: 0.5px;
        }
        .login-form-row {
            display: flex;
            gap: 8px;
            margin-bottom: 0.7rem;
        }
        .login-icon-input {
            display: flex;
            align-items: center;
            background: #f5f7fa;
            border-radius: 8px;
            padding: 0.2rem 0.7rem;
            border: 1px solid #e5e7eb;
            width: 100%;
        }
        .login-icon-input input {
            border: none;
            background: transparent;
            outline: none;
            width: 100%;
            font-size: 1rem;
            padding: 0.5rem 0.2rem;
        }
        .login-icon {
            font-size: 1.2rem;
            margin-right: 0.5rem;
            color: #4a6bff;
        }
        .login-btn {
            width: 100%;
            margin-top: 0.5rem;
            background: linear-gradient(90deg, #4a6bff 0%, #6a82fb 100%);
            color: #fff;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            padding: 0.7rem 0;
            font-size: 1rem;
            box-shadow: 0 2px 8px 0 rgba(74, 107, 255, 0.13);
            transition: 0.2s;
        }
        .login-btn:hover {
            background: #6a82fb;
        }
        .login-links {
            display: flex;
            justify-content: space-between;
            margin-top: 0.7rem;
        }
        </style>
        <div class="login-container">
    """, unsafe_allow_html=True)
    st.markdown('<div class="login-title">MSU Timetable System</div>', unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="login-form-row"><span class="login-icon">👤</span>', unsafe_allow_html=True)
            username = st.text_input("Username", key="login_username", label_visibility="collapsed", placeholder="Username")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="login-form-row"><span class="login-icon">🔑</span>', unsafe_allow_html=True)
            password = st.text_input("Password", type="password", key="login_password", label_visibility="collapsed", placeholder="Password")
            st.markdown('</div>', unsafe_allow_html=True)
        submit = st.form_submit_button("Login", use_container_width=True)
        if submit:
            if verify_user(username, password):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.rerun()
            else:
                st.error("Invalid username or password.")
    st.markdown('<div class="login-links">', unsafe_allow_html=True)
    if st.button("Register"):
        st.session_state['show_registration'] = True
        st.session_state['show_reset'] = False
        st.rerun()
    if st.button("Forgot Password?"):
        st.session_state['show_reset'] = True
        st.session_state['show_registration'] = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.session_state.get('show_registration'):
        registration_page()
    if st.session_state.get('show_reset'):
        password_reset_page()

def admin_management():
    st.title("Admin Management")
    
    # Add New User
    st.subheader("Add New User")
    with st.form("add_user_form"):
        new_username = st.text_input("Username")
        new_email = st.text_input("Email Address")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Role", ["admin", "lecturer", "student"], index=0)
        is_admin = (role == 'admin')
        submit = st.form_submit_button("Add User")
        
        if submit:
            if new_password != confirm_password:
                st.error("Passwords do not match!")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long!")
            elif not new_email or '@' not in new_email:
                st.error("Please enter a valid email address!")
            elif create_user(new_username, new_password, is_admin, new_email, role):
                st.success(f"User {new_username} added successfully!")
                st.rerun()
            else:
                st.error("Username already exists!")
    
    # List and manage admins
    st.subheader("Current Admins")
    remy = sqlite3.connect('users.db')
    remy.row_factory = sqlite3.Row
    cursor = remy.cursor()
    cursor.execute("SELECT username, role, email FROM users WHERE is_admin = 1 OR role = 'admin'")
    admins = cursor.fetchall()
    
    if not admins:
        st.info("No admins found.")
    else:
        for admin in admins:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"👤 **{admin['username']}** ({admin['role']})")
                st.caption(f"Email: {admin['email']}")
            with col2:
                if admin['username'] != st.session_state['username']:  # Can't remove yourself
                    if st.button("Remove Admin", key=f"remove_{admin['username']}"):
                        cursor.execute("UPDATE users SET is_admin = 0, role = 'student' WHERE username = ?", (admin['username'],))
                        remy.commit()
                        log_audit('Admin Removed', st.session_state['username'], f"removed={admin['username']}")
                        st.success(f"Admin {admin['username']} removed successfully!")
                        st.rerun()
    
    # Manage Lecturer Accounts
    st.subheader("Lecturer Accounts")
    
    # Search functionality
    search_term = st.text_input("Search lecturers by name or email:")
    
    # Get all lecturer accounts
    query = """
        SELECT username, email, role 
        FROM users 
        WHERE role = 'lecturer' 
        AND (username LIKE ? OR email LIKE ?)
        ORDER BY username
    """
    search_param = f"%{search_term}%"
    cursor.execute(query, (search_param, search_param))
    lecturers = cursor.fetchall()
    
    if not lecturers:
        st.info("No lecturer accounts found.")
    else:
        for lecturer in lecturers:
            with st.expander(f"{lecturer['username']} - {lecturer['email']}"):
                st.write(f"**Role:** {lecturer['role'].title()}")
                
                # Password Reset Form
                with st.form(key=f"reset_form_{lecturer['username']}"):
                    new_password = st.text_input("New Password", type="password", 
                                              key=f"new_pass_{lecturer['username']}")
                    confirm_password = st.text_input("Confirm Password", type="password",
                                                  key=f"confirm_pass_{lecturer['username']}")
                    reset_btn = st.form_submit_button("Reset Password")
                    
                    if reset_btn:
                        if not new_password or not confirm_password:
                            st.error("Please fill in both password fields")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match!")
                        elif len(new_password) < 8:
                            st.error("Password must be at least 8 characters long!")
                        else:
                            if update_password(lecturer['username'], new_password, is_admin_reset=True):
                                log_audit('Password Reset by Admin', 
                                        st.session_state['username'], 
                                        f"reset_for={lecturer['username']}")
                                st.success(f"Password for {lecturer['username']} has been reset successfully! The user will be prompted to change it on next login.")
                                st.rerun()
                            else:
                                st.error("Failed to update password. Please try again.")
    
    remy.close()

def configure_algorithm():
    st.title("Algorithm Configuration")
    st.warning("Warning: Changing these parameters may affect the quality and performance of timetable generation.")
    
    # current constants and have the latest values
    import constants
    from importlib import reload
    reload(constants)  # Force reload to get the latest values
    
    # Create a form for all algorithm parameters
    with st.form("algorithm_config"):
        st.subheader("Genetic Algorithm Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            population_size = st.number_input(
                "Population Size", 
                min_value=10, 
                max_value=1000, 
                value=constants.POPULATION_SIZE,
                help="Number of candidate solutions in each generation"
            )
            
            generations = st.number_input(
                "Max Generations", 
                min_value=10, 
                max_value=10000, 
                value=constants.GENERATIONS,
                help="Maximum number of generations to run"
            )
            
        with col2:
            mutation_rate = st.slider(
                "Mutation Rate", 
                min_value=0.01, 
                max_value=0.5, 
                value=constants.INITIAL_MUTATION_RATE,
                step=0.01,
                help="Probability of a gene mutating"
            )
            
            min_faculty_hours = st.number_input(
                "Min Faculty Hours/Week", 
                min_value=1, 
                max_value=40, 
                value=constants.MIN_FACULTY_HOURS,
                help="Minimum teaching hours per faculty per week"
            )
            
        with col3:
            max_faculty_hours = st.number_input(
                "Max Faculty Hours/Week", 
                min_value=min_faculty_hours+1, 
                max_value=40, 
                value=constants.MAX_FACULTY_HOURS,
                help="Maximum teaching hours per faculty per week"
            )
            
            room_strategy = st.selectbox(
                "Room Allocation Strategy",
                constants.ROOM_ALLOCATION_STRATEGIES,
                index=constants.ROOM_ALLOCATION_STRATEGIES.index('balanced') if 'balanced' in constants.ROOM_ALLOCATION_STRATEGIES else 0,
                help="Strategy for allocating rooms to classes"
            )
        
        st.subheader("Stopping Criteria")
        col4, col5 = st.columns(2)
        
        with col4:
            early_stopping = st.number_input(
                "Early Stopping Generations", 
                min_value=10, 
                max_value=1000, 
                value=constants.EARLY_STOPPING_GENERATIONS,
                help="Stop if no improvement after this many generations"
            )
            
        with col5:
            min_improvement = st.number_input(
                "Minimum Improvement", 
                min_value=0.0001, 
                max_value=0.5, 
                value=constants.MIN_IMPROVEMENT,
                step=0.0001,
                format="%.4f",
                help="Minimum improvement to consider"
            )
        
        # Save button
        if st.form_submit_button("Save Configuration"):
            try:
                # Update the constants module
                with open("constants.py", "r") as f:
                    lines = f.readlines()
                
                # Update each constant
                updates = {
                    "POPULATION_SIZE": population_size,
                    "GENERATIONS": generations,
                    "INITIAL_MUTATION_RATE": mutation_rate,
                    "MIN_FACULTY_HOURS": min_faculty_hours,
                    "MAX_FACULTY_HOURS": max_faculty_hours,
                    "EARLY_STOPPING_GENERATIONS": early_stopping,
                    "MIN_IMPROVEMENT": min_improvement
                }
                
                for i, line in enumerate(lines):
                    for const, value in updates.items():
                        if line.strip().startswith(f"{const} = "):
                            lines[i] = f"{const} = {value}\n"
                
                # Update room strategy if needed
                for i, line in enumerate(lines):
                    if "ROOM_ALLOCATION_STRATEGIES" in line and "[" in line:
                        strategy_line = i
                        while "]" not in lines[i]:
                            i += 1
                        end_bracket = i
                        
                        # Rebuild the ROOM_ALLOCATION_STRATEGIES list
                        new_strategies = constants.ROOM_ALLOCATION_STRATEGIES.copy()
                        if room_strategy not in new_strategies:
                            new_strategies.append(room_strategy)
                        
                        # Move the selected strategy to the front
                        if room_strategy in new_strategies:
                            new_strategies.remove(room_strategy)
                            new_strategies.insert(0, room_strategy)
                        
                        # Update the lines
                        lines[strategy_line] = f"ROOM_ALLOCATION_STRATEGIES = {new_strategies}\n"
                        del lines[strategy_line+1:end_bracket]
                        break
                
                # Write the updated constants back
                with open("constants.py", "w") as f:
                    f.writelines(lines)
                
                # Reload the constants module
                reload(constants)
                
                st.success("Algorithm configuration updated successfully!")
                log_audit('Algorithm Config Updated', st.session_state['username'], 
                         f"population_size={population_size}, generations={generations}, mutation_rate={mutation_rate}")
                
            except Exception as e:
                st.error(f"Failed to update configuration: {str(e)}")
                log_audit('Algorithm Config Error', st.session_state['username'], f"error={str(e)}")
    
    # Display current configuration
    st.subheader("Current Configuration")
    
    # Create a dictionary to store the current values
    current_values = {
        "Parameter": [
            "Population Size", 
            "Max Generations", 
            "Mutation Rate",
            "Min Faculty Hours/Week", 
            "Max Faculty Hours/Week",
            "Room Allocation Strategy", 
            "Early Stopping Generations",
            "Minimum Improvement"
        ],
        "Value": [
            str(getattr(constants, 'POPULATION_SIZE', 'N/A')),
            str(getattr(constants, 'GENERATIONS', 'N/A')),
            str(getattr(constants, 'INITIAL_MUTATION_RATE', 'N/A')),
            str(getattr(constants, 'MIN_FACULTY_HOURS', 'N/A')),
            str(getattr(constants, 'MAX_FACULTY_HOURS', 'N/A')),
            str(constants.ROOM_ALLOCATION_STRATEGIES[0] if hasattr(constants, 'ROOM_ALLOCATION_STRATEGIES') and constants.ROOM_ALLOCATION_STRATEGIES else 'N/A'),
            str(getattr(constants, 'EARLY_STOPPING_GENERATIONS', 'N/A')),
            str(getattr(constants, 'MIN_IMPROVEMENT', 'N/A'))
        ]
    }
    
    # Create a DataFrame with explicit string dtypes
    df = pd.DataFrame(current_values)
    df = df.astype({'Parameter': 'string', 'Value': 'string'})
    
    # Display the current values in a table
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Debug information (can be removed in production)
    if st.checkbox("Show debug information"):
        st.write("Raw constants values:", {
            'POPULATION_SIZE': getattr(constants, 'POPULATION_SIZE', None),
            'GENERATIONS': getattr(constants, 'GENERATIONS', None),
            'INITIAL_MUTATION_RATE': getattr(constants, 'INITIAL_MUTATION_RATE', None),
            'MIN_FACULTY_HOURS': getattr(constants, 'MIN_FACULTY_HOURS', None),
            'MAX_FACULTY_HOURS': getattr(constants, 'MAX_FACULTY_HOURS', None),
            'ROOM_ALLOCATION_STRATEGIES': getattr(constants, 'ROOM_ALLOCATION_STRATEGIES', None),
            'EARLY_STOPPING_GENERATIONS': getattr(constants, 'EARLY_STOPPING_GENERATIONS', None),
            'MIN_IMPROVEMENT': getattr(constants, 'MIN_IMPROVEMENT', None)
        })

def admin_dashboard(active_tab="Overview"):
    st.title("Admin Dashboard")
    
    # Create tabs for different admin sections
    tabs = ["Overview", "User Management", "Algorithm Configuration"]
    
    # Set the active tab index based on the active_tab parameter
    active_tab_index = tabs.index(active_tab) if active_tab in tabs else 0
    
    # Create the tabs
    tab1, tab2, tab3 = st.tabs(tabs)
    
    # Store the active tab in session state
    st.session_state['admin_active_tab'] = tabs[active_tab_index]
    
    with tab1:
        # User stats
        remy = sqlite3.connect('users.db')
        remy = remy.cursor()
        remy.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
        user_counts = dict(remy.fetchall())
        remy.close()
        
        st.subheader("User Statistics")
        st.write({role.capitalize(): count for role, count in user_counts.items()})
        
        # Timetable stats
        timetable_count = 0
        try:
            import database
            timetable_count = len(database.get_all_timetables())
        except Exception:
            pass
        st.subheader("Timetables Generated")
        st.write(f"Total Timetables: {timetable_count}")
        
        # Recent activity from audit.log
        st.subheader("Recent Activity (Audit Log)")
        if os.path.exists('audit.log'):
            with open('audit.log', 'r') as f:
                lines = f.readlines()[-10:]
            for line in lines:
                st.code(line.strip())
        else:
            st.info("No audit log found.")
    
    with tab2:
        admin_management()
    
    with tab3:
        configure_algorithm()
        
    # Add a small script to maintain the active tab on page reload
    st.markdown("""
    <script>
    // This script helps maintain the active tab on page reload
    const activeTab = document.querySelector('button[data-baseweb="tab"][aria-selected="true"]');
    if (activeTab) {
        const tabName = activeTab.textContent.trim();
        window.parent.postMessage({
            type: 'streamlit:setSessionState',
            data: { key: 'admin_active_tab', value: tabName }
        }, '*');
    }
    </script>
    """, unsafe_allow_html=True)
    
    # Quick actions at the bottom
    st.subheader("Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sync Lecturer Accounts"):
            from database import sync_lecturer_accounts_from_timetables
            created = sync_lecturer_accounts_from_timetables()
            st.success(f"Created {created} lecturer accounts with default password.")
            st.rerun()
    with col2:
        if st.button("View All Users"):
            st.session_state['show_all_users'] = True
            st.rerun()
    # Backup Now button
    st.subheader("Database Backups")
    if st.button("Backup Now"):
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_files = []
        for db_file in ["users.db", "timetables.db"]:
            if os.path.exists(db_file):
                backup_path = os.path.join(backup_dir, f"{db_file.replace('.db','')}_backup_{timestamp}.db")
                shutil.copy2(db_file, backup_path)
                backup_files.append(backup_path)
        if backup_files:
            st.success(f"Backup completed! Files: {', '.join(backup_files)}")
        else:
            st.warning("No database files found to backup.")

# Main app
def main():
    # Initialize session state at the start
    initialize_session_state()
    
    params = st.experimental_get_query_params()
    page = params.get("page", ["login"])[0]
    if page == "register":
        registration_page()
        st.stop()
    elif page == "forgot":
        password_reset_page()
        st.stop()
    else:
        login_page()
        st.stop()
    
    if not st.session_state.get('authenticated', False):
        if st.session_state.get('show_registration', False):
            registration_page()
            st.stop()
        elif st.session_state.get('show_reset', False):
            password_reset_page()
            st.stop()
        else:
            login_page()
            st.stop()
    else:
        # Show password change form for lecturers using default password
        if st.session_state.get('needs_password_change', False):
            st.warning("Please change your default password.")
            with st.form("change_default_password"):
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                submit = st.form_submit_button("Change Password")
                
                if submit:
                    if new_password != confirm_password:
                        st.error("Passwords do not match!")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters long!")
                    else:
                        remy = sqlite3.connect('users.db')
                        remy = remy.cursor()
                        remy.execute('UPDATE users SET password = ? WHERE username = ?', 
                                   (generate_password_hash(new_password), st.session_state['username']))
                        remy.commit()
                        remy.close()
                        st.success("Password changed successfully!")
                        st.session_state['needs_password_change'] = False
                        log_audit('Password Changed', st.session_state['username'], "Changed default password")
                        st.rerun()
            st.stop()
        
        # Sidebar content
        st.sidebar.success(f"Logged in as {st.session_state['username']} ({st.session_state.get('role', 'student').capitalize()})")
        
        # Show admin management for admins
        if st.session_state.get('is_admin', False):
            if st.sidebar.button("Admin Management"):
                st.session_state['show_admin_management'] = not st.session_state.get('show_admin_management', False)
                st.rerun()
        
        if st.sidebar.button("Logout"):
            st.session_state['authenticated'] = False
            st.session_state['username'] = None
            st.session_state['is_admin'] = False
            st.session_state['role'] = None
            st.rerun()
        
        # Main content
        if st.session_state.get('show_admin_management', False) and st.session_state.get('is_admin', False):
            admin_management()
        else:
            # Import here to avoid circular imports
            from matt import main as timetable_main
            timetable_main()

if __name__ == "__main__":
    main() 