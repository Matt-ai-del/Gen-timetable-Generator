"""
Timetable Generator Web Application

A comprehensive Streamlit-based application for generating optimal timetables
in educational institutions using genetic algorithms.

Features:
- Interactive web interface for timetable configuration
- Genetic algorithm optimization for schedule generation
- Faculty workload management and room allocation
- Comprehensive reporting and export capabilities
- Multi-user authentication and session management

Author: Timetable Generator Team
Version: 2.0.0
"""

import streamlit as st
from database import get_student_timetable, get_all_timetables, get_timetable_by_id
from services.email_service import send_feedback_email
from ui.lecturer_timetable import render_lecturer_download_section
import logging
import database


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('timetable.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Timetable Generator",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

def set_bg():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url('msu_bg.jpg');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg()

import login
#import matt

def main():
    # Initialize session state
    login.initialize_session_state()
    
    if not st.session_state['authenticated']:
        login.login_page()
    else:
        # Check if user needs to change password
        if st.session_state.get('needs_password_change', False):
            login.force_password_change_page(st.session_state['username'])
            return # Stop further execution to only show password change page

        st.sidebar.success(f"Logged in as {st.session_state['username']} ({st.session_state.get('role', 'student').capitalize()})")
        
        # Home button at the top of sidebar
        if st.sidebar.button("🏠 Home"):
            # Reset all view states
            st.session_state['show_feedback'] = False
            st.session_state['show_admin_dashboard'] = False
            st.session_state['show_admin_management'] = False
            st.session_state['show_student_timetable'] = False
            st.session_state['show_lecturer_timetable'] = False
            st.session_state['show_lecturer_accounts'] = False
            # Import and show main timetable interface
            from matt import main as timetable_main
            timetable_main(st.session_state.get('role', 'student'))
            st.rerun()
        
        # Feedback button
        if st.sidebar.button("Feedback"):
            st.session_state['show_feedback'] = True
            st.rerun()
        
        # Only show these buttons if not admin
        if st.session_state.get('role') != 'admin':
            # Only show the relevant download button for each role
            role = st.session_state.get('role')
            if role == 'student':
                if st.sidebar.button("Download My Timetable"):
                    st.session_state['show_student_timetable'] = True
                    st.rerun()
            elif role == 'lecturer':
                if st.sidebar.button("Download Lecturer Timetable"):
                    st.session_state['show_lecturer_timetable'] = True
                    st.rerun()
        
        # Add Admin Dashboard button for admin users only
        if st.session_state.get('role') == 'admin':
            if st.sidebar.button("Admin Dashboard"):
                st.session_state['show_admin_dashboard'] = True
                st.session_state['show_admin_management'] = False
                st.session_state['show_lecturer_accounts'] = False
                st.rerun()
            if st.sidebar.button("Admin Management"):
                st.session_state['show_admin_dashboard'] = False
                st.session_state['show_admin_management'] = True
                st.session_state['show_lecturer_accounts'] = False
                st.rerun()
            if st.sidebar.button("Algorithm Settings"):
                st.session_state['show_admin_dashboard'] = True
                st.session_state['admin_active_tab'] = 'Algorithm Configuration'
                st.rerun()
            if st.sidebar.button("View Lecturer Accounts"):
                st.session_state['show_admin_dashboard'] = False
                st.session_state['show_admin_management'] = False
                st.session_state['show_lecturer_accounts'] = True
                st.rerun()
        
        if st.sidebar.button("Logout"):
            st.session_state['authenticated'] = False
            st.session_state['username'] = None
            st.session_state['is_admin'] = False
            st.session_state['role'] = None
            st.rerun()
            
        # Show feedback form if requested
        if st.session_state.get('show_feedback', False):
            st.title("Feedback / Report a Problem")
            with st.form("feedback_form"):
                user_email = st.text_input("Your Email (optional)")
                message = st.text_area("Your Feedback or Issue", help="Describe your feedback or the problem you encountered.")
                submit = st.form_submit_button("Send Feedback")
                if submit:
                    if not message.strip():
                        st.error("Please enter your feedback or issue.")
                    else:
                        sent = send_feedback_email(user_email, message)
                        if sent:
                            st.success("Thank you for your feedback! It has been sent to the admin.")
                            st.session_state['show_feedback'] = False
                        else:
                            st.error("Failed to send feedback. Please try again later.")
            if st.button("Back to App"):
                st.session_state['show_feedback'] = False
                st.rerun()
            return
            
        # Only show download sections if not admin
        if st.session_state.get('role') != 'admin':
            # Show student timetable download section
            if st.session_state.get('show_student_timetable', False):
                if st.session_state.get('role') != 'student':
                    st.error("This section is only available to students.")
                    return
                st.title("Download My Timetable")
                
                # Add instructions
                st.info("""
                Please enter your details below to download your personalized timetable. 
                The timetable will include your class schedule, module information, and important notes.
                """)
                
                # Get all timetables from database
                timetables = get_all_timetables()
                
                if not timetables:
                    st.warning("No timetables have been generated yet. Please contact the administrator.")
                else:
                    # Get the most recent timetable
                    latest_timetable = get_timetable_by_id(timetables[0]['id'])
                    if latest_timetable:
                        # Extract programs and levels from the latest timetable
                        programs = latest_timetable['programs']
                        levels = latest_timetable['levels']
                        department = latest_timetable['department']
                        session_title = latest_timetable['session_title']
                        
                        # Show department and session information
                        st.subheader("Department Information")
                        st.write(f"**Department:** {department}")
                        st.write(f"**Academic Session:** {session_title}")
                        
                        # Show available programs and levels
                        st.subheader("Available Programs and Levels")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Programs:**")
                            for prog in programs:
                                st.write(f"- {prog}")
                        with col2:
                            st.write("**Levels:**")
                            for lvl in levels:
                                st.write(f"- {lvl}")
                        
                        st.markdown("---")
                        
                        # Create form for input
                        with st.form("student_timetable_form"):
                            st.subheader("Enter Your Details")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                student_id = st.text_input("Student ID", help="Enter your student ID number")
                            with col2:
                                # Create program and level selection dropdowns
                                selected_program = st.selectbox(
                                    "Select your Program",
                                    programs,
                                    help="Choose your program (e.g., CS, CSE)"
                                )
                                selected_level = st.selectbox(
                                    "Select your Level",
                                    levels,
                                    help="Choose your level (e.g., 1.1, 1.2)"
                                )
                            
                            # Add options for timetable format
                            st.subheader("Timetable Options")
                            col3, col4 = st.columns(2)
                            
                            with col3:
                                include_module_info = st.checkbox(
                                    "Include Module Information",
                                    value=True,
                                    help="Add a section with detailed module information"
                                )
                                
                                include_notes = st.checkbox(
                                    "Include Important Notes",
                                    value=True,
                                    help="Add a section with important notes and guidelines"
                                )
                            
                            with col4:
                                show_lecturers = st.checkbox(
                                    "Show Lecturer Names",
                                    value=True,
                                    help="Include lecturer names in the timetable"
                                )
                                
                                show_rooms = st.checkbox(
                                    "Show Room Numbers",
                                    value=True,
                                    help="Include room numbers in the timetable"
                                )
                            
                            submit = st.form_submit_button("Generate Timetable")
                        
                        # Handle form submission outside the form
                        if submit:
                            if not student_id.strip():
                                st.error("Please enter your Student ID.")
                            elif not selected_program or not selected_level:
                                st.error("Please select both a program and level.")
                            else:
                                # Get the student's timetable
                                timetable, docx_buffer, error = get_student_timetable(student_id, selected_program, selected_level)
                                if timetable:
                                    st.success("Timetable generated successfully!")
                                    
                                    # Show timetable preview
                                    st.subheader("Timetable Preview")
                                    st.write(f"**Student ID:** {student_id}")
                                    st.write(f"**Program:** {selected_program}")
                                    st.write(f"**Level:** {selected_level}")
                                    st.write(f"**Department:** {department}")
                                    st.write(f"**Session:** {session_title}")
                                    
                                    # Download button outside the form
                                    key=f"download_combined_timetable_{department}_{session_title}"
                                    st.download_button(
                                        label="Download Timetable (DOCX)",
                                        data=docx_buffer,
                                        file_name=f"timetable_{student_id}_{selected_program}_{selected_level}.docx",
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        key=key,
                                        use_container_width=True
                                    )
                                else:
                                    st.error(error)
                
                if st.button("Back to App"):
                    st.session_state['show_student_timetable'] = False
                    st.rerun()
                return
            
            # Show lecturer timetable download section
            if st.session_state.get('show_lecturer_timetable', False):
                render_lecturer_download_section()
                return
        
        # Show admin dashboard if requested
        if st.session_state.get('show_admin_dashboard', False) or st.session_state.get('show_admin_management', False) or st.session_state.get('show_lecturer_accounts', False):
            # Initialize active tab if not set
            if 'admin_active_tab' not in st.session_state:
                if st.session_state.get('show_admin_management'):
                    st.session_state['admin_active_tab'] = 'User Management'
                elif st.session_state.get('show_lecturer_accounts'):
                    st.session_state['admin_active_tab'] = 'Lecturer Accounts'
                else:
                    st.session_state['admin_active_tab'] = 'Overview'
            
            # Display the admin dashboard with tabs
            login.admin_dashboard(st.session_state.get('admin_active_tab', 'Overview'))
            return
        
        # Show admin management, lecturer accounts, or timetable based on state
        if st.session_state.get('show_admin_management', False) and st.session_state.get('role') == 'admin':
            login.admin_management()
        elif st.session_state.get('show_lecturer_accounts', False) and st.session_state.get('role') == 'admin':
            st.title("Lecturer Accounts")
            
            # Add sync button at the top
            if st.button("🔄 Sync Lecturer Accounts"):
                from database import sync_lecturer_accounts_from_timetables
                created = sync_lecturer_accounts_from_timetables()
                st.success(f"Created {created} lecturer accounts with default password.")
                st.rerun()
            
            # Get and display lecturer accounts
            from database import get_all_lecturer_accounts
            lecturers = get_all_lecturer_accounts()
            
            if not lecturers:
                st.warning("No lecturer accounts found. Click the 'Sync Lecturer Accounts' button to create accounts from timetables.")
            else:
                # Add search and filter options
                col1, col2 = st.columns(2)
                with col1:
                    search = st.text_input("🔍 Search by name or department", "")
                with col2:
                    departments = sorted(list(set(l['department'] for l in lecturers)))
                    selected_department = st.selectbox("Filter by department", ["All Departments"] + departments)
                
                # Filter lecturers based on search and department
                filtered_lecturers = lecturers
                if search:
                    search = search.lower()
                    filtered_lecturers = [l for l in filtered_lecturers 
                                       if search in l['username'].lower() or search in l['department'].lower()]
                if selected_department != "All Departments":
                    filtered_lecturers = [l for l in filtered_lecturers if l['department'] == selected_department]
                
                # Display results
                st.write(f"Found {len(filtered_lecturers)} lecturer accounts")
                
                # Create a table with lecturer information
                for lecturer in filtered_lecturers:
                    with st.expander(f"{lecturer.get('username', 'Unknown')} ({lecturer.get('department', 'Not specified')})"):
                        cols = st.columns(len(lecturer))
                        for i, (key, value) in enumerate(lecturer.items()):
                            with cols[i]:
                                st.write(f"**{key.capitalize()}:**")
                                st.write(value or 'Not specified')
                
                # Add export option
                if st.button("📥 Export Lecturer List"):
                    import pandas as pd
                    df = pd.DataFrame(filtered_lecturers)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="lecturer_accounts.csv",
                        mime="text/csv"
                    )
        else:
            # Pass role to matt.main if needed for further permission checks
          #  matt.main(user_role=st.session_state.get('role', 'student'))
        
        # Add footer
        st.markdown("---")  # Add a horizontal line
        st.markdown(
            '<div style="text-align: center; color: gray;">Empowering Education Through Technology | Midlands State University</div>',
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main() 
