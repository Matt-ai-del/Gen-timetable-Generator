"""UI helpers for lecturer timetable download experience."""

import json
import traceback

import streamlit as st

from constants import DAYS, TIME_SLOTS
from database import get_all_timetables, get_timetable_by_id
import database


def _build_timetable_options(timetables):
    timetable_options = []
    timetable_id_map = {}
    for timetable in timetables:
        tid = timetable['id']
        dept = timetable.get('department', 'Unknown Department')
        session = timetable.get('session_title', 'Unknown Session')
        date = timetable.get('created_at', 'Unknown Date')
        display = f"ID {tid}: {dept} - {session} ({date})"
        timetable_options.append(display)
        timetable_id_map[display] = tid
    return timetable_options, timetable_id_map


def _extract_lecturers_from_slots(slots):
    lecturers_in_slots = set()
    for day in slots:
        for slot in slots[day]:
            entries = slots[day][slot]
            if isinstance(entries, list):
                for entry in entries:
                    name = entry.get('lecturer') or entry.get('instructor')
                    if isinstance(name, str) and name.strip():
                        lecturers_in_slots.add(name.strip())
                    elif name is not None:
                        lecturers_in_slots.add(str(name))
            elif isinstance(entries, dict) and entries:
                name = entries.get('lecturer') or entries.get('instructor')
                if isinstance(name, str) and name.strip():
                    lecturers_in_slots.add(name.strip())
                elif name is not None:
                    lecturers_in_slots.add(str(name))
    return sorted(lecturers_in_slots)


def render_lecturer_download_section():
    """Render the lecturer download workflow previously in app.py."""
    st.title("Download Lecturer Timetable")
    st.info(
        """
        Please select a timetable to download your teaching schedule.
        The timetable will include your classes, module information, and important notes.
        """
    )

    timetables = get_all_timetables()
    if not timetables:
        st.warning("No timetables have been generated yet. Please contact the administrator.")
        _render_back_button()
        return

    timetable_options, timetable_id_map = _build_timetable_options(timetables)

    if 'selected_timetable_display' not in st.session_state:
        st.session_state.selected_timetable_display = timetable_options[0]

    st.subheader("Select Timetable")
    selected_display = st.selectbox(
        "Choose a Timetable (ID shown for clarity)",
        timetable_options,
        help="Select the timetable you want to download",
        key="timetable_selector",
        index=timetable_options.index(st.session_state.selected_timetable_display)
    )
    st.session_state.selected_timetable_display = selected_display
    selected_timetable_id = timetable_id_map[selected_display]

    timetable_data = get_timetable_by_id(selected_timetable_id)
    lecturers_in_slots = []
    slots = None

    if timetable_data and 'timetable_data' in timetable_data:
        raw_slots = timetable_data['timetable_data']
        if isinstance(raw_slots, str):
            slots = json.loads(raw_slots)['slots']
        else:
            slots = raw_slots['slots']
        lecturers_in_slots = _extract_lecturers_from_slots(slots)
        st.info(
            f"""
            **Timetable Information:**
            - Department: {timetable_data['department']}
            - Session: {timetable_data['session_title']}
            - Found {len(lecturers_in_slots)} lecturers in this timetable
            """
        )

    search_term = st.text_input(
        "🔍 Search Lecturer",
        help="Type to filter the lecturer list",
        key="lecturer_search"
    )

    filtered_lecturers = lecturers_in_slots
    if search_term:
        lowered = search_term.lower()
        filtered_lecturers = [name for name in lecturers_in_slots if lowered in name.lower()]
        if not filtered_lecturers:
            st.warning(f"No lecturers found matching '{search_term}'")
        else:
            st.success(f"Found {len(filtered_lecturers)} matching lecturers")

    selected_lecturer = None
    submitted = False

    with st.form(key="lecturer_timetable_form", clear_on_submit=False):
        if not lecturers_in_slots:
            st.warning("No lecturers found in this timetable's slots.")
            submitted = st.form_submit_button("Generate Timetable", disabled=True)
        else:
            st.subheader("Select Your Name")
            if 'selected_lecturer' not in st.session_state:
                st.session_state.selected_lecturer = lecturers_in_slots[0]
            display_list = filtered_lecturers if search_term else lecturers_in_slots
            selected_index = (
                display_list.index(st.session_state.selected_lecturer)
                if st.session_state.selected_lecturer in display_list
                else 0
            )
            selected_lecturer = st.selectbox(
                "Select your Name (only those scheduled in this timetable are shown)",
                display_list,
                help="Choose your name from the list of lecturers scheduled in this timetable",
                key="lecturer_name_selector",
                index=selected_index
            )
            st.session_state.selected_lecturer = selected_lecturer

            if selected_lecturer and slots:
                _render_quick_preview(selected_lecturer, slots, timetable_data)

            st.subheader("Timetable Options")
            col1, col2 = st.columns(2)
            with col1:
                st.checkbox(
                    "Include Module Information",
                    value=True,
                    help="Add a section with detailed module information"
                )
                st.checkbox(
                    "Include Important Notes",
                    value=True,
                    help="Add a section with important notes and guidelines"
                )
            with col2:
                st.checkbox(
                    "Show Room Numbers",
                    value=True,
                    help="Include room numbers in the timetable"
                )
                show_student_groups = st.checkbox(
                    "Show Student Groups",
                    value=True,
                    help="Include student groups in the timetable"
                )
            submitted = st.form_submit_button("Generate Timetable")

    if submitted and selected_lecturer:
        _handle_generation(selected_lecturer, selected_timetable_id, timetable_data, show_student_groups)

    _render_back_button()


def _render_quick_preview(selected_lecturer, slots, timetable_data):
    st.subheader("Quick Preview")
    preview_col1, preview_col2 = st.columns(2)
    with preview_col1:
        st.write(f"**Selected Lecturer:** {selected_lecturer}")
        st.write(f"**Department:** {timetable_data['department']}")
    with preview_col2:
        class_count = 0
        for day in slots:
            for slot in slots[day]:
                entries = slots[day][slot]
                if isinstance(entries, list):
                    for entry in entries:
                        if (
                            entry.get('lecturer') == selected_lecturer
                            or entry.get('instructor') == selected_lecturer
                        ):
                            class_count += 1
                elif isinstance(entries, dict) and entries:
                    if (
                        entries.get('lecturer') == selected_lecturer
                        or entries.get('instructor') == selected_lecturer
                    ):
                        class_count += 1
        st.write(f"**Total Classes:** {class_count}")


def _handle_generation(selected_lecturer, selected_timetable_id, timetable_data, show_student_groups):
    try:
        with st.spinner("Generating lecturer timetable..."):
            timetable, docx_buffer, error = database.get_lecturer_timetable(
                selected_lecturer, selected_timetable_id
            )
            if error:
                st.error(error)
                return
            if not timetable:
                st.error("No timetable found for this lecturer. Please check the timetable selection.")
                return

            st.success("Timetable generated successfully!")
            _render_timetable_preview(selected_lecturer, timetable_data, timetable, show_student_groups)
            st.download_button(
                label="Download Timetable (DOCX)",
                data=docx_buffer.getvalue() if docx_buffer else None,
                file_name=f"timetable_{selected_lecturer}_{selected_timetable_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
    except Exception as exc:
        st.error(f"Error generating timetable: {exc}")
        st.error("Technical details:")
        st.code(traceback.format_exc())


def _render_timetable_preview(selected_lecturer, timetable_data, timetable, show_student_groups):
    st.subheader("Timetable Preview")
    st.write(f"**Lecturer:** {selected_lecturer}")
    st.write(f"**Department:** {timetable_data['department']}")
    st.write(f"**Session:** {timetable_data['session_title']}")

    table_data = []
    for day in DAYS:
        row = [day]
        for slot in TIME_SLOTS:
            entries = timetable['slots'][day][slot]
            if entries:
                cell_text = []
                for entry in entries:
                    details = [f"{entry['module']}<br>Room: {entry['room']}"]
                    if show_student_groups and timetable_data.get('original_data'):
                        module = next(
                            (
                                m for m in timetable_data['original_data']['modules']
                                if m['code'] == entry['module']
                            ),
                            None
                        )
                        if module and 'target_groups' in module:
                            groups = [f"{prog} {lvl}" for prog, lvl in module['target_groups']]
                            if groups:
                                details.append(f"Groups: {', '.join(groups)}")
                    cell_text.append("<br>".join(details))
                row.append("<br><br>".join(cell_text))
            else:
                row.append("")
        table_data.append(row)

    html = [
        "<style>",
        ".fixed-table { border-collapse: collapse; width: 100%; }",
        ".fixed-table th, .fixed-table td {",
        "    border: 1px solid #ccc;",
        "    text-align: left;",
        "    vertical-align: top;",
        "    width: 180px;",
        "    height: 80px;",
        "    min-width: 120px;",
        "    min-height: 60px;",
        "    max-width: 220px;",
        "    max-height: 120px;",
        "    padding: 6px;",
        "    font-size: 14px;",
        "    word-break: break-word;",
        "}",
        ".fixed-table th { background: #f5f5f5; }",
        "</style>",
        "<table class='fixed-table'><thead><tr><th>Day</th>"
    ]
    for slot in TIME_SLOTS:
        html.append(f"<th>{slot}</th>")
    html.append("</tr></thead><tbody>")
    for row in table_data:
        html.append("<tr>")
        for cell in row:
            html.append(f"<td>{cell}</td>")
        html.append("</tr>")
    html.append("</tbody></table>")
    st.markdown("".join(html), unsafe_allow_html=True)

    st.markdown('---')
    st.subheader("Important Notes")
    st.markdown(
        """
- Please arrive at least 5 minutes before each class.
- Ensure all teaching materials are prepared in advance.
- Notify the department office if you need to reschedule any classes.
- Keep track of your teaching hours and report any discrepancies.
- Contact the department office for any timetable-related queries.
        """
    )


def _render_back_button():
    if st.button("Back to App"):
        st.session_state['show_lecturer_timetable'] = False
        st.rerun()
