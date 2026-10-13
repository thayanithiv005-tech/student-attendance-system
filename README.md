# Student Attendance Management System

A local web-based attendance application built with Python, Streamlit, and SQLite.

## Features
- Add, search, list, and remove students
- Mark attendance as Present, Absent, or Late by date
- Edit an existing attendance entry by saving again for the same student/date
- Dashboard metrics and attendance status chart
- Student attendance percentages and low-attendance highlighting
- CSV export for summary and detailed attendance records
- SQLite database created automatically on first run

## Requirements
- Python 3.10 or newer
- VS Code (recommended)
- Internet connection for the initial package installation

## Run on Windows (VS Code terminal)

1. Extract the project folder.
2. Open the folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:

   ```powershell
   py -m venv .venv
   ```

5. Activate it:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt terminal instead:

   ```bat
   .venv\Scripts\activate.bat
   ```

6. Install packages:

   ```powershell
   python -m pip install -r requirements.txt
   ```

7. Start the app:

   ```powershell
   python -m streamlit run app.py
   ```

8. The app opens in your browser, usually at `http://localhost:8501`.

SQLite is part of Python, so you do not need to install it separately. The `attendance.db` file is created beside `app.py`.

## Quick demo
1. Open **Manage Students**.
2. Add sample students with unique roll numbers, such as `CS001`, `CS002`, and `CS003`.
3. Open **Mark Attendance**, select a date, choose statuses, and click **Save Attendance**.
4. Open **Dashboard** to see metrics.
5. Open **Attendance Reports** to review percentages and download CSV files.

Use fictional sample data in screenshots and demos. Do not upload real student personal information to a public repository.

## Project structure
- `app.py` — application and interface
- `requirements.txt` — Python dependencies
- `PROJECT_REPORT.md` — editable project report
- `attendance.db` — created automatically when the app runs

## Notes
This is a small academic project intended for local demonstration. It does not include user login, role permissions, cloud hosting, or automated backups. A percentage is calculated from the attendance records entered into the app; it is only as accurate as the data recorded.
