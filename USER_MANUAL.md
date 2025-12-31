 Timetable Generator: User Manual

Welcome to the Timetable Generator! This guide will help you understand what this tool does and how to use it, even if you're not a tech expert.

 1. What is the Timetable Generator?

Imagine the complicated puzzle of scheduling all the classes, teachers, and rooms at a school or university. The Timetable Generator is a smart computer program that helps solve this puzzle automatically.

It takes all the information – like courses, student groups, teacher availability, and classroom sizes – and creates an optimized timetable. This means it tries to make the best schedule possible, avoiding clashes (like a teacher being in two places at once) and considering everyone's needs.

 2. Who is it For?

This tool is designed for educational institutions and has different features for:

   Administrators: The people who manage the school's schedule. They set up the system, input all the data, and generate the main timetables.
   Lecturers/Teachers: They can view their personal teaching schedules.
   Students: They can view and download their individual class timetables.

 3. Getting Started

To use the Timetable Generator, it needs to be run on a computer. If it's already set up for you, you'll usually access it through a web browser (like Chrome, Firefox, or Edge).

If you're setting it up for the first time (this part might need some technical help):

1.  Make sure Python (a programming language) is installed on the computer.
2.  Download the project files.
3.  Install the necessary helper programs by running a command like pip install -r requirements.txt in a terminal or command prompt.
4.  Start the application by running the command streamlit run app.py.
5.  Your web browser should open, or you'll be given a web address (like http://localhost:8501) to open manually.

 4. Using the Application

When you open the application, the first thing you'll see is a login page.

 4.1. Logging In

   You'll need a username and password to log in.
   The system knows if you are an Administrator, Lecturer, or Student based on your login details, and will show you options relevant to your role.
   There are also options to register for a new account (if enabled) or reset your password if you forget it.

 4.2. For Administrators

Administrators have the most control and are responsible for setting up and generating timetables.

A. Main Dashboard & Navigation:
   After logging in, you'll see a sidebar on the left with navigation options.
   The "Home" button usually takes you to the main timetable generation interface.

B. Setting Up Your Institution's Data (in the "Generate Timetable" section):
This is the most important part for admins. You'll need to provide all the details for the timetable. The interface usually has sections for:

1.  Departments: You can select an existing department (e.g., Computer Science, Business Studies) or add new ones.
2.  Session Title: Give your timetable a name, like "Spring Semester 2025 Timetable."
3.  Programs: Add or select the study programs (e.g., Bachelor of Science in CS, Diploma in Marketing).
4.  Levels: Define student year levels (e.g., Year 1.1, Year 2.2).
5.  Modules/Courses:
       Add all the courses that need to be scheduled.
       For each course, you'll specify:
           Course code and name.
           How many hours per week it needs.
           Which student groups (program and level) take this course.
           How many students are in each group.
           Any preferred rooms or types of rooms (e.g., Lab, Lecture Hall).
6.  Lecturers/Teachers:
       Add all the lecturers.
       For each lecturer, specify:
           Which courses they can teach.
           Their availability (days/times they cannot teach).
           Their maximum teaching load.
7.  Rooms:
       Add all available classrooms, labs, and lecture halls.
       For each room, specify:
           Its name or number.
           Its capacity (how many students it can hold).
           Its type (e.g., Lab, General Classroom).

C. Generating the Timetable:
   Once all the data is entered, you'll find a button like "Generate Timetable."
   Clicking this starts the process. The system will use its smart algorithm to try and create the best possible schedule.
   This might take a few minutes, and you'll often see a progress bar.
   When it's done, the generated timetable will be displayed.
   You can usually view it by room, by lecturer, or by student group.
   There will be options to save or download the timetable (e.g., as a PDF or Excel file).

D. Viewing History:
   There's usually a section to view previously generated timetables.

E. Admin Management (Advanced):
   Admins might have extra options to:
       Manage user accounts (approve new lecturer registrations, reset passwords).
       Adjust settings for the timetable generation algorithm (e.g., how hard it tries to find a perfect solution).

 4.3. For Lecturers/Teachers

   Login: Log in with your lecturer credentials.
   View/Download Timetable: You'll typically have an option in the sidebar like "Download Lecturer Timetable" or a similar view on your home page.
       This will show you your personal teaching schedule: which courses you're teaching, when, and where.
       You can usually download this schedule.
   Registration (if applicable): New lecturers might need to register first, and an administrator will approve their account.

 4.4. For Students

   Login: Log in with your student credentials (if required, some systems might allow public viewing or student ID lookup).
   Download My Timetable: Look for an option in the sidebar or on the main page.
       You'll likely need to select your Program (e.g., Computer Science) and Level (e.g., 1.1).
       You might also need to enter your Student ID.
       The system will then generate and show your personalized class schedule.
       You can usually download this schedule (often as a Word document or PDF).

 4.5. Feedback

   Most pages will have a "Feedback" button in the sidebar.
   If you encounter any issues or have suggestions, you can use this to send a message to the administrators.

 5. What You Get (The Output)

The main output of the Timetable Generator is, of course, the timetable! This can be presented in various ways:

   Overall Timetable: Showing all classes, for all rooms, for all student groups.
   Room-wise Timetable: Showing what's scheduled in each room throughout the week.
   Lecturer-wise Schedule: A personal schedule for each teacher.
   Student Group Timetable: A schedule for a specific group of students (e.g., all Year 1 Computer Science students).
   Downloadable Formats: Timetables can often be downloaded as PDF files, Excel spreadsheets, or Word documents for easy printing and sharing.

 6. Troubleshooting (Simple Tips)

   Incorrect Timetable? If the generated timetable has errors, the most common reason is incorrect or incomplete data entered by the administrator. Double-check all course details, lecturer availability, room capacities, etc.
   Slow Generation? Creating a complex timetable can take time. Be patient. If it's very slow, the administrator might need to adjust some advanced settings or the computer running it might be overloaded.
   Login Issues? Double-check your username and password. If you forgot your password, use the reset option. If you're a new lecturer, your account might need admin approval.

We hope this guide helps you use the Timetable Generator effectively!
