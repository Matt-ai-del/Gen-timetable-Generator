 Timetable Generator Web Application

This is a web-based timetable generator for educational institutions, built using Streamlit. The application helps in creating optimal timetables while considering various constraints like faculty availability, room requirements, and course schedules.

 Features

- Interactive web interface for timetable generation
- Support for multiple programs and levels
- Course type classification (Core, Program-Specific, Level-Specific)
- Faculty workload management
- Room and lab allocation
- Comprehensive reporting and visualization

 Setup Instructions

1. Install Python 3.8 or higher
2. Install the required dependencies:
   bash
   pip install -r requirements.txt
   
3. Run the application:
   bash
   streamlit run app.py
   

 Usage

1. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)
2. Configure your department structure by selecting programs and levels
3. Add courses with their respective attributes
4. Input faculty information and their specializations
5. Configure room and lab availability
6. Click "Generate Timetable" to create an optimal schedule

 Output

The application provides:
- Room-wise timetable view
- Faculty-wise schedule
- Course coverage report
- Faculty workload analysis

 Requirements

- Python 3.8+
- Streamlit
- Pandas
- NumPy 

 Create virtual environment
python -m venv venv

 Activate virtual environment (in PowerShell)
.\venv\Scripts\Activate.ps1

 If you get a security error in PowerShell, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

 Install requirements
pip install -r requirements.txt 

