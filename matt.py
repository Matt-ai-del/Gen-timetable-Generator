import streamlit as st
import pandas as pd
from timetable import (
    generate_timetable,
    display_timetable,
    DAYS,
    TIME_SLOTS,
    WEEKLY_MODULE_HOURS,
    SESSIONS_PER_MODULE
)
from collections import defaultdict
import database
import io
from fpdf import FPDF
from utils import safe_latin1
import json
from docx import Document
import time
import psutil
import os

# Constants
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = ["08:00-10:00", "10:00-12:00", "12:00-14:00", "14:00-16:00"]  #MSUs' Standardized format

# Tandem scheduling constants
#TANDEM_SLOTS = {
 #   "08:00-10:00": "10:00-12:00",
 #   "10:00-12:00": "12:00-14:00",
 #   "12:00-14:00": "14:00-16:00"
#}

def initialize_department():
    return {
        'programs': ["CS", "CSE", "SWE", "CSEC"],
        'modules': [],
        'lecturers': [],
        'rooms': ["Lab 30"],
        'levels': ["1.1", "1.2", "2.1", "2.2", "4.1", "4.2"],
        'module_types': ["Core", "Program-Specific", "Level-Specific"],
        'lecturer_slots': defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None))),
    }

def main(user_role='student'):
    # Initialize database
    database.init_db()
    
    st.title("Timetable Generator")
    
    # Tabs based on role
    if user_role == 'admin' or user_role == 'lecturer':
        tab1, tab2 = st.tabs(["Generate Timetable", "View History"])
        with tab1:
            generate_timetable_section(user_role)
        with tab2:
            view_history_section()
    else:  # student
        # Create tabs for student view
        tab1, tab2 = st.tabs(["Download My Timetable", "View History"])
        
        with tab1:
            st.info("Download your personalized timetable by entering your details below.")
            
            # Get all timetables from database
            timetables = database.get_all_timetables()
            if not timetables:
                st.error("No timetables have been generated yet. Please contact the administrator.")
                return
            
            # Show available programs and levels from the latest timetable
            latest_timetable = database.get_timetable_by_id(timetables[0]['id'])
            if latest_timetable:
                st.info(f"Available programs: {', '.join(latest_timetable['programs'])}")
                st.info(f"Available levels: {', '.join(latest_timetable['levels'])}")
            
            with st.form("student_timetable_form"):
                student_id = st.text_input("Student ID", help="Enter your student ID number")
                
                # Create program and level selection dropdowns
                program = st.selectbox(
                    "Select your Program",
                    latest_timetable['programs'],
                    help="Choose your program (e.g., CS, CSE)"
                )
                
                level = st.selectbox(
                    "Select your Level",
                    latest_timetable['levels'],
                    help="Choose your level (e.g., 1.1, 1.2)"
                )
                
                # Add options for timetable format
                st.subheader("Timetable Options")
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
                
                submit = st.form_submit_button("Generate Timetable")
            
            if submit:
                if not student_id:
                    st.error("Please enter your Student ID.")
                else:
                    try:
                        with st.spinner("Generating your timetable..."):
                            timetable, docx_buffer, error = database.get_student_timetable(student_id, program, level)
                            if error:
                                st.error(error)
                            elif timetable:
                                st.success("Timetable generated successfully!")

                                # Show timetable preview in combined format
                                st.subheader("Timetable Preview")
                                st.write(f"**Student ID:** {student_id}")
                                st.write(f"**Program:** {program}")
                                st.write(f"**Level:** {level}")
                                st.write(f"**Department:** {latest_timetable['department']}")
                                st.write(f"**Session:** {latest_timetable['session_title']}")

                                # Build table
                                table_data = []
                                for day in DAYS:
                                    row = [day]
                                    for slot in TIME_SLOTS:
                                        entries = timetable['slots'][day][slot]
                                        if entries:
                                            cell_text = []
                                            for entry in entries:
                                                cell_text.append(f"{entry['module']}<br>Room: {entry['room']}<br>Lecturer: {entry['lecturer']}")
                                            row.append("<br><br>".join(cell_text))
                                        else:
                                            row.append("")
                                    table_data.append(row)
                                # Custom HTML table with fixed cell size
                                html = """
                                <style>
                                .fixed-table { border-collapse: collapse; width: 100%; }
                                .fixed-table th, .fixed-table td {
                                    border: 1px solid #ccc;
                                    text-align: left;
                                    vertical-align: top;
                                    width: 180px;
                                    height: 80px;
                                    min-width: 120px;
                                    min-height: 60px;
                                    max-width: 220px;
                                    max-height: 120px;
                                    padding: 6px;
                                    font-size: 14px;
                                    word-break: break-word;
                                }
                                .fixed-table th { background: #f5f5f5; }
                                </style>
                                <table class='fixed-table'>
                                    <thead>
                                        <tr>
                                            <th>Day</th>
                                """
                                for slot in TIME_SLOTS:
                                    html += f"<th>{slot}</th>"
                                html += "</tr></thead><tbody>"
                                for row in table_data:
                                    html += "<tr>"
                                    for cell in row:
                                        html += f"<td>{cell}</td>"
                                    html += "</tr>"
                                html += "</tbody></table>"
                                st.markdown(html, unsafe_allow_html=True)

                                # Add important notes for students
                                st.markdown('---')
                                st.subheader("Important Notes")
                                st.markdown("""
- Please arrive at least 5 minutes before each class.
- Bring your student ID card to all classes.
- Notify your lecturer in advance if you need to miss a class.
- Check the university website regularly for timetable changes.
- Contact your department office for any timetable-related queries.
""")

                                # Download button outside the form
                                st.download_button(
                                    label="Download Timetable (DOCX)",
                                    data=docx_buffer.getvalue() if docx_buffer else None,
                                    file_name=f"timetable_{student_id}_{program}_{level}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    use_container_width=True
                                )
                            else:
                                st.error("No timetable found for your details. Please check your program and level, or contact the administrator.")
                    except Exception as e:
                        st.error(f"Error generating timetable: {str(e)}")
                        import traceback
                        st.error("Technical details:")
                        st.code(traceback.format_exc())
        
        with tab2:
            view_history_section()

def generate_timetable_section(user_role='student'):
    # Only allow editors/admins to generate timetables
    if user_role not in ['admin']:
        st.warning("You do not have permission to generate timetables.")
        return

    # Check if user is authenticated
    if not st.session_state.get('authenticated', False):
        st.warning("Please log in to access the timetable generator.")
        return

    # Initialize session state for university data
    if 'university' not in st.session_state:
        st.session_state['university'] = {
            'departments': {
                'Computer Science': initialize_department()
            },
            'current_dept': 'Computer Science'
        }

    # DEPARTMENT MANAGEMENT 
    st.sidebar.header("University Management")
    
    # Department selection
    current_dept = st.sidebar.selectbox(
        "Select Department:",
        list(st.session_state['university']['departments'].keys()),
        index=list(st.session_state['university']['departments'].keys()).index(
            st.session_state['university']['current_dept']
        )
    )
    
    if current_dept != st.session_state['university']['current_dept']:
        st.session_state['university']['current_dept'] = current_dept
        st.rerun()

    # Add new department
    with st.sidebar.expander("➕ Add New Department"):
        new_dept_name = st.text_input("Department Name:")
        new_dept_programs = st.text_input("Initial Programs (comma separated):")
        
        # Room management in department creation
        st.subheader("Initial Rooms")
        num_rooms = st.number_input("Number of rooms to add:", min_value=1, value=1, step=1)
        room_base_name = st.text_input("Room base name (e.g., 'Lab' or 'Room'):", value="Lab")
        room_capacity = st.number_input("Default room capacity:", min_value=1, value=30, step=1)
        
        if st.button("Create Department"):
            if new_dept_name and new_dept_name not in st.session_state['university']['departments']:
                new_dept = initialize_department()
                programs_list = [p.strip() for p in new_dept_programs.split(",") if p.strip()]
                
                # Generate room list based on inputs
                rooms_list = []
                if num_rooms > 0 and room_base_name:
                    rooms_list = [
                        {"name": f"{room_base_name} {i+1}", "capacity": room_capacity}
                        for i in range(num_rooms)
                    ]
                
                if programs_list:
                    new_dept['programs'] = programs_list
                if rooms_list:
                    new_dept['rooms'] = rooms_list
                
                st.session_state['university']['departments'][new_dept_name] = new_dept
                st.session_state['university']['current_dept'] = new_dept_name
                st.rerun()
            elif new_dept_name in st.session_state['university']['departments']:
                st.error("Department already exists!")

    # Get current department data
    current_data = st.session_state['university']['departments'][current_dept]
    for module in current_data.get('modules', []):
        module['hours'] = WEEKLY_MODULE_HOURS
    
    # MAIN INTERFACE 
    st.title(f"Timetable Generator for {current_dept} Department")

    # SESSION/QUARTER TITLE INPUT
    session_title = st.text_input(
        "Enter session/quarter title (e.g., '2nd QUARTER TIMETABLE FEBRUARY TO JUNE 2025'):",
        value="2nd QUARTER TIMETABLE FEBRUARY TO JUNE 2025"
    )

    # PROGRAM MANAGEMENT 
    st.header("Programs Information")
    
    # Program selection
    selected_programs = st.multiselect(
        "Select programs to include:",
        current_data['programs'],
        default=current_data['programs']
    )

    # Add/Remove Programs
    with st.expander("Manage Programs", expanded=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            new_program = st.text_input("Add new program code:", help="e.g. 'CS' for Computer Science")
        with col2:
            st.write("")  # Vertical spacer
            if st.button("Add Program"):
                if new_program.strip():
                    if new_program not in current_data['programs']:
                        current_data['programs'].append(new_program.strip())
                        st.rerun()
                    else:
                        st.warning(f"Program '{new_program}' already exists!")
                else:
                    st.warning("Please enter a program code")

        if current_data['programs']:
            program_to_remove = st.selectbox(
                "Select program to remove:",
                current_data['programs'],
                index=None,
                key="remove_program_select"
            )
            if program_to_remove and st.button("Confirm Removal"):
                current_data['programs'].remove(program_to_remove)
                st.rerun()

    # Display current programs
    st.write("**Available Programs:**", ", ".join(current_data['programs']) if current_data['programs'] else st.warning("No programs added yet"))

    # Level selection
    st.header("Students Levels")
    selected_levels = st.multiselect(
        "Select levels to include:",
        current_data['levels'],
        default=current_data['levels']
    )

    # Add/Remove Levels
    with st.expander("Manage Levels", expanded=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            new_level = st.text_input("Add new level:", help="e.g. '1.1' for first year first semester")
        with col2:
            st.write("")  # Vertical spacer
            if st.button("Add Level"):
                if new_level.strip():
                    if new_level not in current_data['levels']:
                        current_data['levels'].append(new_level.strip())
                        st.rerun()
                    else:
                        st.warning(f"Level '{new_level}' already exists!")
                else:
                    st.warning("Please enter a level")

        if current_data['levels']:
            level_to_remove = st.selectbox(
                "Select level to remove:",
                current_data['levels'],
                index=None,
                key="remove_level_select"
            )
            if level_to_remove and st.button("Confirm Level Removal"):
                current_data['levels'].remove(level_to_remove)
                st.rerun()

    # STUDENT GROUP SIZES
    with st.expander("Student Group Sizes", expanded=True):
        st.warning("⚠️ Room capacity validation depends on these numbers. Please set accurate student counts for each group.")
        if 'students_per_group' not in current_data:
            current_data['students_per_group'] = {}
        for program in selected_programs:
            for level in selected_levels:
                key = f"students_{program}_{level}"
                # Ensure students_per_group is a dictionary
                if isinstance(current_data['students_per_group'], str):
                    try:
                        current_data['students_per_group'] = json.loads(current_data['students_per_group'])
                    except json.JSONDecodeError:
                        current_data['students_per_group'] = {}
                default_val = current_data['students_per_group'].get((program, level), 30)
                num_students = st.number_input(
                    f"Number of students in {program} Level {level}",
                    min_value=1,
                    value=default_val,
                    key=key,
                    help=f"This number will be used to check if rooms have sufficient capacity for {program} Level {level} classes"
                )
                current_data['students_per_group'][(program, level)] = num_students
    
    # ROOM MANAGEMENT
    st.header("Rooms Information")
    
    # Ensure rooms is a list of dictionaries with proper structure
    if not current_data.get('rooms'):
        current_data['rooms'] = []
    else:
        # Convert any string rooms to proper dictionary format
        formatted_rooms = []
        for room in current_data['rooms']:
            if isinstance(room, str):
                formatted_rooms.append({
                    'name': room,
                    'capacity': 30,
                    'allowed_programs': []
                })
            elif isinstance(room, dict):
                # Ensure all required fields exist
                if 'name' not in room:
                    continue  # Skip invalid room entries
                formatted_room = {
                    'name': room['name'],
                    'capacity': room.get('capacity', 30),
                    'allowed_programs': room.get('allowed_programs', [])
                }
                formatted_rooms.append(formatted_room)
        current_data['rooms'] = formatted_rooms
    
    # Room Management Section
    with st.expander("Manage Rooms", expanded=True):
        st.subheader("Add Multiple Rooms")
        
        # Input for multiple rooms
        col1, col2, col3 = st.columns(3)
        with col1:
            num_rooms = st.number_input(
                "Number of rooms:",
                min_value=1,
                value=5,  # Default to 5 rooms
                step=1,
                key="num_rooms_input"
            )
        with col2:
            room_prefix = st.text_input(
                "Room prefix:",
                value="Room",
                key="room_prefix_input"
            )
        with col3:
            default_capacity = st.number_input(
                "Default capacity:",
                min_value=1,
                value=500,  # Set default capacity to 500
                step=5,
                key="room_capacity_input"
            )
        
        # Add button
        if st.button("Add Rooms", key="add_rooms_btn"):
            if room_prefix.strip():
                # Clear existing rooms first
                current_data['rooms'] = []
                
                # Add new rooms
                for i in range(num_rooms):
                    room_name = f"{room_prefix} {i+1}"
                    current_data['rooms'].append({
                        'name': room_name,
                        'capacity': default_capacity,
                        'allowed_programs': []
                    })
            else:
                st.warning("Please enter a room prefix")
    
    # Display current rooms in a table-like format
    if current_data['rooms']:
        st.subheader("Current Rooms")
        
        # Display each room in a card-like format
        for idx, room in enumerate(current_data['rooms']):
            with st.container():
                cols = st.columns([2, 2, 5, 1])
                
                with cols[0]:
                    # Use index-based keys so editing doesn't require reruns
                    name_key = f"room_name_input_{idx}"
                    new_name = st.text_input(
                        "Room Name",
                        value=room['name'],
                        key=name_key
                    )
                    if new_name.strip():
                        room['name'] = new_name
                 
                with cols[1]:
                    room['capacity'] = st.number_input(
                        "Capacity",
                        min_value=1,
                        value=room.get('capacity', 30),
                        step=1,
                        key=f"capacity_{idx}"
                    )
                
                with cols[2]:
                    # Get available programs for the multiselect
                    available_programs = current_data.get('programs', [])
                    room['allowed_programs'] = st.multiselect(
                        "Allowed Programs",
                        options=available_programs,
                        default=room.get('allowed_programs', []),
                        key=f"programs_{idx}",
                        help="Select programs allowed to use this room"
                    )
                
                with cols[3]:
                    st.write("")
                    st.write("")
                    if st.button("❌", key=f"remove_{idx}"):
                        del current_data['rooms'][idx]
                        break

    # MODULE CONFIGURATION 
    st.header("Modules Information")

    # Module type classification
    module_types = st.multiselect(
        "Define module types:",
        current_data['module_types'],
        default=["Core", "Program-Specific", "Level-Specific"]
    )

    # Build all (program, level) pairs from Student Group Sizes
    group_options = []
    for k in current_data.get('students_per_group', {}):
        if isinstance(k, tuple) and len(k) == 2:
            group_options.append(k)
        elif isinstance(k, str) and '|' in k:
            parts = k.split('|')
            if len(parts) == 2:
                group_options.append(tuple(parts))
    group_labels = [f"{program} {level}" for (program, level) in group_options]

    # Remove duplicates while preserving order
    seen = set()
    unique_group_options = []
    unique_group_labels = []
    for opt, label in zip(group_options, group_labels):
        if label not in seen:
            unique_group_options.append(opt)
            unique_group_labels.append(label)
            seen.add(label)

    # Module input with enhanced attributes
    with st.expander("Add/Edit Modules", expanded=False):
        num_modules = st.number_input(
            "Number of modules:", 
            min_value=1, 
            value=len(current_data['modules']) if current_data['modules'] else 1
        )
        
        # Initialize modules if empty
        if not current_data['modules']:
            current_data['modules'] = [{
                "code": "",
                "name": "",
                "hours": WEEKLY_MODULE_HOURS,
                "type": "Core",
                "target_programs": [],
                "target_levels": [],
                "id": i
            } for i in range(num_modules)]
        elif len(current_data['modules']) < num_modules:
            # Add new modules if number increased
            for i in range(len(current_data['modules']), num_modules):
                current_data['modules'].append({
                    "code": "",
                    "name": "",
                    "hours": WEEKLY_MODULE_HOURS,
                    "type": "Core",
                    "target_programs": [],
                    "target_levels": [],
                    "id": i
                })
        elif len(current_data['modules']) > num_modules:
            # Remove modules if number decreased
            current_data['modules'] = current_data['modules'][:num_modules]
        
        for i, module in enumerate(current_data['modules']):
            st.subheader(f"Module {i+1}")
            cols = st.columns([2, 3, 1, 2, 2])
            
            with cols[0]:
                module['code'] = st.text_input(f"Code (e.g., HCSC1134)", value=module['code'], key=f"code_{i}")
            with cols[1]:
                module['name'] = st.text_input(f"Name", value=module['name'], key=f"name_{i}")
            with cols[2]:
                module_hours = st.number_input(
                    "Hours/week",
                    min_value=2,
                    max_value=4,
                    step=2,
                    value=min(module.get('hours', WEEKLY_MODULE_HOURS), 4),  # Cap at 4 hours
                    key=f"hours_{i}",
                    help="Enter hours per week (2 or 4 hours)"
                )
                module['hours'] = module_hours
            with cols[3]:
                module['type'] = st.selectbox(f"Type", module_types, index=module_types.index(module['type']) if module['type'] in module_types else 0, key=f"type_{i}")
            with cols[4]:
                # Replace multiselect with container of checkboxes
                st.write("Select student groups:")
                checked_groups = []
                for group_label, group_tuple in zip(unique_group_labels, unique_group_options):
                    if st.checkbox(
                        group_label,
                        value=(group_tuple in module.get('target_groups', []) or list(group_tuple) in module.get('target_groups', [])),
                        key=f"group_{i}_{group_label}"
                    ):
                        checked_groups.append(group_tuple)
                module['target_groups'] = checked_groups

    # LECTURER CONFIGURATION 
    st.header("Lecturers Information")
    with st.expander("Add/Edit Lecturers"):
        num_lecturers = st.number_input(
            "Number of lecturers:", 
            min_value=1, 
            value=len(current_data['lecturers']) if current_data['lecturers'] else 1
        )
        
        # Initialize lecturers if empty
        if not current_data['lecturers']:
            current_data['lecturers'] = [{
                "id": i,
                "name": "",
                "modules": [],
                "max_daily": 4,
                "max_weekly": 10  # 10 sessions = 20 hours
            } for i in range(num_lecturers)]
        elif len(current_data['lecturers']) < num_lecturers:
            # Add new lecturers if number increased
            for i in range(len(current_data['lecturers']), num_lecturers):
                current_data['lecturers'].append({
                    "id": i,
                    "name": "",
                    "modules": [],
                    "max_daily": 2,
                    "max_weekly": 10
                })
        elif len(current_data['lecturers']) > num_lecturers:
            # Remove lecturers if number decreased
            current_data['lecturers'] = current_data['lecturers'][:num_lecturers]
        
        for i, lecturer in enumerate(current_data['lecturers']):
            st.subheader(f"Lecturer {i+1}")
            lecturer['name'] = st.text_input(f"Name", value=lecturer['name'], key=f"lect_name_{i}")
            
            col1, col2 = st.columns(2)
            with col1:
                lecturer['max_daily'] = st.number_input(
                    f"Max classes/day", 
                    min_value=1, 
                    max_value=4, 
                    value=lecturer['max_daily'], 
                    key=f"lect_max_daily_{i}"
                )
            with col2:
                lecturer['max_weekly'] = st.number_input(
                    f"Max classes/week", 
                    min_value=1, 
                    max_value=20, 
                    value=lecturer.get('max_weekly', 10), 
                    key=f"lect_max_weekly_{i}"
                )
            
            # Lecturer specialization
            st.write("Select modules this lecturer can teach:")
            lecturer['modules'] = []
            for module in current_data['modules']:
                if st.checkbox(
                    f"{module['code']} - {module['name']}",
                    value=(module['code'] in lecturer['modules']),
                    key=f"lect_{i}_module_{module['id']}"
                ):
                    lecturer['modules'].append(module['code'])

    # ROOM CONFIGURATION 
    st.header("Rooms Information")
    with st.expander("Manage Rooms"):
        st.write("Current Rooms:")
        for i, room in enumerate(current_data['rooms']):
            if isinstance(room, dict):
                # Ensure capacity is at least 500 for existing rooms
                if 'capacity' in room and room['capacity'] < 500:
                    room['capacity'] = 500
                    
                col1, col2, col3, col4 = st.columns([3, 2, 3, 1])
                with col1:
                    room['name'] = st.text_input(f"Room {i+1} Name", value=room.get('name', f"Room {i+1}"), key=f"room_name_{i}")
                with col2:
                    room['capacity'] = st.number_input(f"Capacity", min_value=500, value=room.get('capacity', 500), key=f"room_cap_{i}")
                with col3:
                    # Initialize allowed_programs if it doesn't exist
                    if 'allowed_programs' not in room:
                        room['allowed_programs'] = []
                    # Allow selection of programs for this room
                    room['allowed_programs'] = st.multiselect(
                        f"Allowed Programs (Room {i+1})",
                        options=current_data['programs'],
                        default=room['allowed_programs'],
                        key=f"room_programs_{i}",
                        help="Select programs allowed to use this room. Leave empty to allow all programs."
                    )
                with col4:
                    if st.button("❌", key=f"remove_room_{i}"):
                        current_data['rooms'].pop(i)
                        st.rerun()
        
        if st.button("➕ Add Room"):
            current_data['rooms'].append({
                'name': f"Room {len(current_data['rooms'])+1}",
                'capacity': 500,
                'allowed_programs': []  # Empty list means all programs allowed
            })
            st.rerun()

    # Focused Configuration Summary Log with Capacity Check 
    with st.expander("Configuration Check & Summary", expanded=True):
        config_ok = True
        issues = []
        
        # Check room-program assignments
        st.subheader("Room-Program Assignments")
        rooms_with_restrictions = [r for r in current_data['rooms'] if isinstance(r, dict) and r.get('allowed_programs')]
        
        if rooms_with_restrictions:
            st.write("Rooms with program restrictions:")
            for room in rooms_with_restrictions:
                programs = ", ".join(room['allowed_programs']) if room['allowed_programs'] else "No programs assigned (will not be used)"
                st.write(f"- {room['name']}: {programs}")
        else:
            st.warning("No rooms have program restrictions. All rooms are available to all programs.")
        
        # Check module assignments
        st.subheader("Modules and Assigned Groups")
        # Get all room capacities
        room_capacities = [room['capacity'] if isinstance(room, dict) else 30 for room in current_data['rooms']]
        max_room_capacity = max(room_capacities) if room_capacities else 0
        for i, module in enumerate(current_data['modules']):
            group_labels = []
            total_students = 0
            for group in module.get('target_groups', []):
                group_labels.append(f"{group[0]} {group[1]}")
                total_students += current_data.get('students_per_group', {}).get((group[0], group[1]), 0)
            group_str = ', '.join(group_labels) if group_labels else 'No groups assigned'
            
            # Check if module has valid rooms available
            module_programs = {group[0] for group in module.get('target_groups', [])}
            if module_programs:
                valid_rooms = []
                for room in current_data['rooms']:
                    if isinstance(room, dict) and room.get('allowed_programs'):
                        if all(program in room['allowed_programs'] for program in module_programs):
                            valid_rooms.append(room['name'])
                    else:
                        # Room with no restrictions is not valid if module has programs
                        continue
                
                if not valid_rooms:
                    issues.append(f"No valid rooms found for {module.get('code', 'Unnamed module')} (Programs: {', '.join(module_programs)}). "
                                 f"Ensure there are rooms that allow all of these programs.")
                    config_ok = False
            
            st.write(f"{i+1}. {module.get('code', '')} - {module.get('name', '')}")
            st.caption(f"Assigned Groups: {group_str}")
            if module_programs:
                st.caption(f"Programs: {', '.join(module_programs)}")
                if valid_rooms:
                    st.caption(f"Eligible Rooms: {', '.join(valid_rooms) if len(valid_rooms) < 5 else f'{len(valid_rooms)} rooms available'}")
            if not module.get('code') or not module.get('name'):
                config_ok = False
                issues.append(f"Module {i+1} is missing a code or name.")
            if not module.get('target_groups'):
                config_ok = False
                issues.append(f"Module {module.get('code', 'Unknown')} has no assigned student groups.")
            if total_students > max_room_capacity:
                config_ok = False
                issues.append(f"Module {module.get('code', 'Unknown')} assigned to {total_students} students, which exceeds the largest room capacity ({max_room_capacity}).")
        # Check for modules not assigned to any lecturer 
        unassigned_modules = [m for m in current_data['modules'] if not any(l for l in current_data['lecturers'] if m['code'] in l.get('modules', []))]
        if unassigned_modules:
            config_ok = False
            issues.append('The following modules have not been assigned to any lecturer: ' + ', '.join(m['code'] for m in unassigned_modules))
        st.markdown("---")
        st.subheader("Rooms")
        for i, room in enumerate(current_data['rooms']):
            name = room['name'] if isinstance(room, dict) else room
            capacity = room.get('capacity', 30) if isinstance(room, dict) else 30
            st.write(f"{name}: Capacity {capacity}")
            if not capacity or capacity <= 0:
                config_ok = False
                issues.append(f"Room {name} has invalid capacity.")
        st.markdown("---")
        if config_ok:
            st.success("All configuration checks passed! You are ready to generate the timetable.")
        else:
            st.error("Configuration issues detected:")
            for issue in issues:
                st.write(f"- {issue}")

    # Add Cancel Generation button and logic
    if 'cancel_generation' not in st.session_state:
        st.session_state['cancel_generation'] = False

    colA, colB = st.columns([2, 1])
    with colA:
        generate_clicked = st.button("Generate Timetable")
    with colB:
        cancel_clicked = st.button("Cancel Generation")
        if cancel_clicked:
            st.session_state['cancel_generation'] = True
            st.warning("Timetable generation will be cancelled at the next opportunity.")

    if generate_clicked:
        st.session_state['cancel_generation'] = False

        # Efficiency Measurement Start 
        start_time = time.time()
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss
        cpu_before = process.cpu_times().user
        #  End Efficiency Measurement Start 

        with st.spinner("Generating optimal timetable... (this may take a minute or more)..."):
            best_timetable = generate_timetable(current_data)
            if best_timetable is None and st.session_state.get('cancel_generation'):
                st.warning("Timetable generation was cancelled.")
                return

        # Efficiency Measurement End ---
        end_time = time.time()
        mem_after = process.memory_info().rss
        cpu_after = process.cpu_times().user
        # End Efficiency Measurement End
        # Save timetable to database with original data
        if best_timetable is not None:
            # Before saving timetable to database, convert students_per_group keys to str
            if 'students_per_group' in current_data:
                current_data['students_per_group'] = tuple_keys_to_str(current_data['students_per_group'])

            database.save_timetable(
                current_dept,
                selected_programs,
                selected_levels,
                session_title,
                best_timetable,
                current_data  # Store the original data used to generate the timetable
            )

            display_timetable(
                best_timetable,
                current_data,
                current_dept,
                selected_programs,
                selected_levels,
                session_title
            )

            # After loading timetable_data
            assigned_groups = set()
            for module in current_data['modules']:
                for prog, lvl in module.get('target_groups', []):
                    assigned_groups.add((prog, lvl))
            assigned_programs = sorted({prog for prog, lvl in assigned_groups})
            assigned_levels = sorted({lvl for prog, lvl in assigned_groups}, key=lambda x: (float(x.split('.')[0]), float(x.split('.')[1])) if '.' in x else x)
            st.info(f"Available programs: {', '.join(assigned_programs) if assigned_programs else 'None'}")
            st.info(f"Available levels: {', '.join(assigned_levels) if assigned_levels else 'None'}")

            # Show Efficiency Metrics ---
            st.markdown("### Efficiency Metrics")
            st.info(f"**Computation Time:** {end_time - start_time:.2f} seconds")
            st.info(f"**Memory Used:** {(mem_after - mem_before) / 1024**2:.2f} MB")
            st.info(f"**CPU Time Used:** {cpu_after - cpu_before:.2f} seconds")

            # Solution Quality
            violations = validate_timetable(best_timetable, current_data)
            st.info(f"**Constraint Violations:** {len(violations)}")
            if violations:
                with st.expander("Show Violations"):
                    for v in violations:
                        st.write(f"- {v}")


            # All Modules Distribution Table ---
            st.markdown("### All Modules Distribution")

            all_distributions = []
            for m in current_data['modules']:
                module_code = m.get('code')
                if not module_code:
                    continue
                for day in DAYS:
                    for slot in TIME_SLOTS:
                        entries = best_timetable['slots'][day][slot]
                        if isinstance(entries, list):
                            for entry in entries:
                                if entry['module'] == module_code:
                                    all_distributions.append({
                                        "Module": module_code,
                                        "Module Name": m.get('name', ''),
                                        "Day": day,
                                        "Time Slot": slot,
                                        "Room": entry['room'],
                                        "Lecturer": entry['lecturer'],
                                        "Groups": ", ".join([f"{g[0]} {g[1]}" for g in entry.get('groups', [])]) if 'groups' in entry else ""
                                    })
                        elif isinstance(entries, dict) and entries and entries.get('module') == module_code:
                            all_distributions.append({
                                "Module": module_code,
                                "Module Name": m.get('name', ''),
                                "Day": day,
                                "Time Slot": slot,
                                "Room": entries['room'],
                                "Lecturer": entries['lecturer'],
                                "Groups": ", ".join([f"{g[0]} {g[1]}" for g in entries.get('groups', [])]) if 'groups' in entries else ""
                            })

            if all_distributions:
                st.dataframe(pd.DataFrame(all_distributions))
            else:
                st.info("No modules are scheduled in the current timetable.")

        else:
            if st.session_state.get('cancel_generation'):
                st.error("You cancelled the timetable generation.")
            else:
                # Specific error reporting
                unassigned_modules = [m['code'] for m in current_data['modules'] if not any(l for l in current_data['lecturers'] if m['code'] in l.get('modules', []))]
                if unassigned_modules:
                    st.error("Timetable generation failed because the following modules are not assigned to any lecturer:")
                    for code in unassigned_modules:
                        st.write(f"- {code}")
                else:
                    # Optionally, you can call validate_timetable here for more detailed issues
                    st.error("Timetable generation failed for other reasons. Please check your configuration.")

def validate_timetable(timetable, data):
    "Enhanced validation with detailed violation reports"
    # Track all violations
    violations = []
    
    # 1. Module constraints
    for module in data['modules']:
        if not module['code']:
            continue
            
        # Count scheduled sessions
        weekly_sessions = 0
        daily_counts = {day: 0 for day in DAYS}
        
        for day in DAYS:
            for slot in TIME_SLOTS:
                slot_entries = timetable['slots'][day][slot]
                if isinstance(slot_entries, list):
                    if any(t and t['module'] == module['code'] for t in slot_entries):
                        weekly_sessions += 1
                        daily_counts[day] += 1
                elif isinstance(slot_entries, dict) and slot_entries:
                    if slot_entries['module'] == module['code']:
                        weekly_sessions += 1
                        daily_counts[day] += 1
        
        # Check weekly requirement based on module hours
        required_sessions = module.get('hours', WEEKLY_MODULE_HOURS) // 2
        if weekly_sessions != required_sessions:
            violations.append(
                f"MODULE SCHEDULING: {module['code']} has {weekly_sessions*2}h/week "
                f"(must be {module.get('hours', WEEKLY_MODULE_HOURS)}h)"
            )
        
        # Check daily limit (2 hours = 1 session)
        for day, count in daily_counts.items():
            if count > 1:
                violations.append(
                    f"DAILY OVERLOAD: {module['code']} has {count*2}h "
                    f"on {day} (max 2h allowed)"
                )

    # 2. Faculty constraints
    for lecturer in data['lecturers']:
        weekly_hours = 0
        daily_hours = {day: 0 for day in DAYS}
        
        for day in DAYS:
            for slot in TIME_SLOTS:
                slot_entries = timetable['slots'][day][slot]
                if isinstance(slot_entries, list):
                    if any(t and t['lecturer'] == lecturer['name'] for t in slot_entries):
                        daily_hours[day] += 2
                        weekly_hours += 2
                elif isinstance(slot_entries, dict) and slot_entries:
                    if slot_entries['lecturer'] == lecturer['name']:
                        daily_hours[day] += 2
                        weekly_hours += 2
        
        # Check weekly limit (20 hours)
        if weekly_hours > lecturer.get('max_weekly', 10)*2:
            violations.append(
                f"FACULTY OVERLOAD: {lecturer['name']} teaches {weekly_hours}h/week "
                f"(max {lecturer.get('max_weekly', 10)*2}h allowed)"
            )
        
        # Check daily limit (4 hours)
        for day, hours in daily_hours.items():
            if hours > lecturer.get('max_daily', 2)*2:
                violations.append(
                    f"DAILY OVERLOAD: {lecturer['name']} teaches {hours}h "
                    f"on {day} (max {lecturer.get('max_daily', 2)*2}h allowed)"
                )

    # 3. Room constraints
    for day in DAYS:
        for slot in TIME_SLOTS:
            room_usage = {}
            slot_entries = timetable['slots'][day][slot]
            if isinstance(slot_entries, list):
                entries = slot_entries
            elif isinstance(slot_entries, dict) and slot_entries:
                entries = [slot_entries]
            else:
                entries = []
                
            for entry in entries:
                # Room double-booking
                room = entry['room']
                room_usage[room] = room_usage.get(room, 0) + 1
                if room_usage[room] > 1:
                    violations.append(f"Room {room} is double-booked on {day} {slot}")
                
                # Capacity check
                room_obj = next((r for r in data['rooms'] if (isinstance(r, dict) and r['name'] == room) or r == room), None)
                if room_obj:
                    capacity = room_obj['capacity'] if isinstance(room_obj, dict) else 30
                    module = next((m for m in data['modules'] if m['code'] == entry['module']), None)
                    if module:
                        total_students = sum(
                            data.get('students_per_group', {}).get((program, level), 0)
                            for (program, level) in module.get('target_groups', [])
                        )
                        if total_students > capacity:
                            violations.append(
                                f"CAPACITY EXCEEDED: Room {room} has {total_students} students "
                                f"(capacity: {capacity}) for {entry['module']} on {day} {slot}"
                            )

    # Display all violations
    if violations:
        st.error("Timetable Validation Issues:")
        for violation in violations:
            st.error(violation)
    else:
        st.success("No constraint violations detected!")
    return violations

def view_history_section():
    st.header("Previously Generated Timetables")
    timetables = database.get_all_timetables()
    if not timetables:
        st.info("No timetables have been generated yet.")
        return
    timetable_data = []
    for t in timetables:
        timetable_data.append({
            "ID": t['id'],
            "Department": t['department'],
            "Programs": ", ".join(t['programs']),
            "Levels": ", ".join(t['levels']),
            "Session": t['session_title'],
            "Generated": t['created_at']
        })
    df = pd.DataFrame(timetable_data)
    st.dataframe(df, use_container_width=True)
    selected_id = st.selectbox(
        "Select a timetable to view:",
        options=[t['id'] for t in timetables],
        format_func=lambda x: f"Timetable {x} - {next(t['session_title'] for t in timetables if t['id'] == x)}",
        help="Choose a timetable to view or download."
    )
    if 'show_selected_timetable' not in st.session_state:
        st.session_state['show_selected_timetable'] = False
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("View Selected Timetable"):
            st.session_state['show_selected_timetable'] = True
    with col2:
        if st.button("Download DOCX"):
            timetable = database.get_timetable_by_id(selected_id)
            if timetable and timetable['docx_data']:
                st.download_button(
                    label="Download Timetable DOCX",
                    data=timetable['docx_data'],
                    file_name=f"timetable_{selected_id}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
    with col4:
        if st.button("Delete Selected Timetable"):
            if st.session_state.get('is_admin', False):
                database.delete_timetable(selected_id)
                st.success("Timetable deleted successfully!")
                st.rerun()
            else:
                st.error("Only administrators can delete timetables.", icon="⚠️")
    if st.session_state.get('show_selected_timetable', False):
        timetable = database.get_timetable_by_id(selected_id)
        if timetable:
            display_timetable(
                timetable['timetable_data'],
                timetable['original_data'],
                timetable['department'],
                timetable['programs'],
                timetable['levels'],
                timetable['session_title']
            )

# Helper functions for JSON serialization of students_per_group 
def tuple_keys_to_str(d):
    new_d = {}
    for k, v in d.items():
        if isinstance(k, tuple):
            new_d['|'.join(map(str, k))] = v
        else:
            new_d[k] = v
    return new_d

def str_keys_to_tuple(d):
    new_d = {}
    for k, v in d.items():
        if isinstance(k, str) and '|' in k:
            new_d[tuple(k.split('|'))] = v
        else:
            new_d[k] = v
    return new_d

if __name__ == "__main__":
    import login
    login.main()