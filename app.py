import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "attendance.db"

st.set_page_config(
    page_title="Student Attendance Management System",
    page_icon="📚",
    layout="wide",
)

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                year TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                attendance_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late')),
                UNIQUE(student_id, attendance_date),
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """)
        conn.execute("PRAGMA foreign_keys = ON")

def query_df(sql, params=()):
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)

def add_student(roll_no, name, department, year):
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """INSERT INTO students (roll_no, name, department, year, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (roll_no.strip(), name.strip(), department.strip(), year, date.today().isoformat()),
        )

def save_attendance(records, selected_date):
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executemany(
            """INSERT INTO attendance (student_id, attendance_date, status)
               VALUES (?, ?, ?)
               ON CONFLICT(student_id, attendance_date)
               DO UPDATE SET status = excluded.status""",
            [(int(student_id), selected_date.isoformat(), status)
             for student_id, status in records],
        )

def attendance_summary():
    return query_df("""
        SELECT s.id, s.roll_no, s.name, s.department, s.year,
               SUM(CASE WHEN a.status IN ('Present', 'Late') THEN 1 ELSE 0 END) AS attended,
               SUM(CASE WHEN a.status IS NOT NULL THEN 1 ELSE 0 END) AS marked_days,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absent_days
        FROM students s
        LEFT JOIN attendance a ON a.student_id = s.id
        GROUP BY s.id, s.roll_no, s.name, s.department, s.year
        ORDER BY s.roll_no
    """)

init_db()

st.title("📚 Student Attendance Management System")
st.caption("A simple local attendance tracker built with Python, Streamlit, and SQLite.")

with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Choose a section",
        ["Dashboard", "Manage Students", "Mark Attendance", "Attendance Reports"],
    )
    st.divider()
    st.caption("Data is stored locally in attendance.db.")

if page == "Dashboard":
    students = query_df("SELECT * FROM students")
    attendance = query_df("SELECT * FROM attendance")
    total_students = len(students)
    total_sessions = attendance["attendance_date"].nunique() if not attendance.empty else 0
    total_present = int(attendance["status"].isin(["Present", "Late"]).sum()) if not attendance.empty else 0
    total_absent = int((attendance["status"] == "Absent").sum()) if not attendance.empty else 0
    total_marked = len(attendance)
    overall_pct = (100 * total_present / total_marked) if total_marked else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Students", total_students)
    c2.metric("Attendance Dates", total_sessions)
    c3.metric("Present / Late", total_present)
    c4.metric("Overall Attendance", f"{overall_pct:.1f}%")

    st.subheader("Recent attendance records")
    recent = query_df("""
        SELECT a.attendance_date AS Date, s.roll_no AS 'Roll Number',
               s.name AS Student, s.department AS Department, a.status AS Status
        FROM attendance a
        JOIN students s ON s.id = a.student_id
        ORDER BY a.attendance_date DESC, s.roll_no
        LIMIT 15
    """)
    if recent.empty:
        st.info("No attendance records yet. Add students and mark attendance to populate the dashboard.")
    else:
        st.dataframe(recent, use_container_width=True, hide_index=True)

    st.subheader("Attendance status overview")
    if attendance.empty:
        st.info("The chart will appear after attendance has been recorded.")
    else:
        counts = attendance["status"].value_counts().reindex(["Present", "Late", "Absent"], fill_value=0)
        st.bar_chart(counts)

elif page == "Manage Students":
    st.subheader("Add a student")
    with st.form("add_student_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        roll_no = c1.text_input("Roll number / Student ID", placeholder="e.g. CS001")
        name = c2.text_input("Full name", placeholder="e.g. Ananya Kumar")
        department = c1.text_input("Department / Course", placeholder="e.g. CSE")
        year = c2.selectbox("Year of study", ["1st Year", "2nd Year", "3rd Year", "4th Year", "Other"])
        submitted = st.form_submit_button("Add Student", type="primary")
        if submitted:
            if not all([roll_no.strip(), name.strip(), department.strip()]):
                st.error("Please fill in roll number, name, and department.")
            else:
                try:
                    add_student(roll_no, name, department, year)
                    st.success(f"Student {name.strip()} added successfully.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("That roll number already exists. Use a unique roll number.")

    st.subheader("Student list")
    search = st.text_input("Search by roll number, name, or department")
    students = query_df("""
        SELECT id, roll_no AS 'Roll Number', name AS 'Name',
               department AS 'Department', year AS 'Year'
        FROM students ORDER BY roll_no
    """)
    if search:
        mask = students.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        students = students[mask]
    st.dataframe(students.drop(columns=["id"]) if not students.empty else students,
                 use_container_width=True, hide_index=True)

    all_students = query_df("SELECT id, roll_no, name FROM students ORDER BY roll_no")
    if not all_students.empty:
        st.subheader("Remove a student")
        student_options = {
            f"{row['roll_no']} — {row['name']}": int(row["id"])
            for _, row in all_students.iterrows()
        }
        selected_label = st.selectbox("Select student to remove", list(student_options.keys()))
        confirm = st.checkbox("I understand that removing a student also removes their attendance records.")
        if st.button("Remove selected student", disabled=not confirm):
            with get_connection() as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("DELETE FROM students WHERE id = ?", (student_options[selected_label],))
            st.success("Student and related attendance records removed.")
            st.rerun()

elif page == "Mark Attendance":
    st.subheader("Record attendance")
    students = query_df("SELECT id, roll_no, name, department FROM students ORDER BY roll_no")
    selected_date = st.date_input("Attendance date", value=date.today())

    if students.empty:
        st.warning("Add at least one student in Manage Students before marking attendance.")
    else:
        with get_connection() as conn:
            existing_rows = conn.execute(
                "SELECT student_id, status FROM attendance WHERE attendance_date = ?",
                (selected_date.isoformat(),),
            ).fetchall()
        existing = {int(row["student_id"]): row["status"] for row in existing_rows}
        st.caption("Choose a status for each student. Saving again for the same date updates existing entries.")
        with st.form("attendance_form"):
            selected_statuses = {}
            for _, student in students.iterrows():
                label = f"{student['roll_no']} — {student['name']} ({student['department']})"
                options = ["Present", "Absent", "Late"]
                default = existing.get(int(student["id"]), "Present")
                selected_statuses[int(student["id"])] = st.selectbox(
                    label, options, index=options.index(default),
                    key=f"attendance_{selected_date}_{int(student['id'])}",
                )
            save = st.form_submit_button("Save Attendance", type="primary")
            if save:
                save_attendance(list(selected_statuses.items()), selected_date)
                st.success(f"Attendance saved for {selected_date.strftime('%d %B %Y')}.")
                st.rerun()

elif page == "Attendance Reports":
    st.subheader("Student attendance summary")
    summary = attendance_summary()
    if summary.empty:
        st.info("No students found. Add students to generate reports.")
    else:
        summary["Attendance %"] = summary.apply(
            lambda row: (100 * row["attended"] / row["marked_days"])
            if row["marked_days"] else 0,
            axis=1,
        ).round(1)
        summary = summary.rename(columns={
            "roll_no": "Roll Number", "name": "Name", "department": "Department",
            "year": "Year", "attended": "Present / Late Days",
            "marked_days": "Marked Days", "absent_days": "Absent Days",
        })
        st.dataframe(
            summary[["Roll Number", "Name", "Department", "Year",
                     "Present / Late Days", "Absent Days", "Marked Days", "Attendance %"]],
            use_container_width=True, hide_index=True,
        )

        threshold = st.slider("Highlight students below this attendance percentage", 0, 100, 75)
        low = summary[summary["Attendance %"] < threshold]
        if low.empty:
            st.success(f"No students are below {threshold}% attendance.")
        else:
            st.warning(f"{len(low)} student(s) are below {threshold}% attendance.")
            st.dataframe(
                low[["Roll Number", "Name", "Attendance %"]],
                use_container_width=True, hide_index=True,
            )

        st.subheader("Export reports")
        export = summary[[
            "Roll Number", "Name", "Department", "Year",
            "Present / Late Days", "Absent Days", "Marked Days", "Attendance %"
        ]].copy()

        st.download_button(
            "Download student summary (CSV)",
            data=export.to_csv(index=False).encode("utf-8"),
            file_name="student_attendance_summary.csv",
            mime="text/csv",
        )

    records = query_df("""
        SELECT s.roll_no AS 'Roll Number', s.name AS Student,
               s.department AS Department, s.year AS Year,
               a.attendance_date AS Date, a.status AS Status
        FROM attendance a
        JOIN students s ON s.id = a.student_id
        ORDER BY a.attendance_date DESC, s.roll_no
    """)
    st.subheader("Detailed attendance records")
    if records.empty:
        st.info("No attendance records to export yet.")
    else:
        st.dataframe(records, use_container_width=True, hide_index=True)
        st.download_button(
            "Download detailed attendance (CSV)",
            data=records.to_csv(index=False).encode("utf-8"),
            file_name="detailed_attendance_records.csv",
            mime="text/csv",
        )

st.divider()
st.caption("Student Attendance Management System · Academic mini project · Keep the generated database file private if it contains real student information.")
