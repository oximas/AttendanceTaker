"""
services/StudentDatabase.py
Manages student attendance database in Excel format.
Handles student record creation, attendance marking, and database queries.
Logs all database operations for tracking and troubleshooting.
"""

import os
import openpyxl
from openpyxl import Workbook, load_workbook
from datetime import datetime
from logger import log_info, log_warning, log_error
from config import ATTENDANCE_EXCEL_FILE, ATTENDANCE_MARK


class StudentDatabase:
    """Manages student records and attendance in Excel."""
    
    def __init__(self, excel_path=ATTENDANCE_EXCEL_FILE):
        self.excel_path = excel_path
        self._ensure_excel_exists()
    
    def _ensure_excel_exists(self):
        """Create Excel file with headers if it doesn't exist."""
        if not os.path.exists(self.excel_path):
            wb = Workbook()
            ws = wb.active
            ws.title = "Attendance"
            
            # Create headers
            ws['A1'] = "ID"
            ws['B1'] = "Name"
            
            # Style headers
            for cell in ['A1', 'B1']:
                ws[cell].font = openpyxl.styles.Font(bold=True)
            
            wb.save(self.excel_path)
            log_info(f"Created new attendance database: {self.excel_path}")
    
    def add_student(self, student_id, student_name):
        """
        Add a student to the database if not exists.
        
        Args:
            student_id: Student ID (primary key)
            student_name: Student name
            
        Returns:
            bool: True if added, False if already exists
        """
        wb = load_workbook(self.excel_path)
        ws = wb.active
        
        # Check if student already exists
        for row in ws.iter_rows(min_row=2, max_col=1, values_only=True):
            if row[0] == student_id:
                wb.close()
                return False
        
        # Add new student
        ws.append([student_id, student_name])
        wb.save(self.excel_path)
        wb.close()
        log_info(f"Student added to database: ID={student_id}, Name={student_name}")
        return True
    
    def get_student_name(self, student_id):
        """
        Get student name by ID.
        
        Args:
            student_id: Student ID
            
        Returns:
            str: Student name or None if not found
        """
        wb = load_workbook(self.excel_path)
        ws = wb.active
        
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] == student_id:
                wb.close()
                return row[1]
        
        wb.close()
        return None
    
    def get_all_students(self):
        """
        Get all students from database.
        
        Returns:
            list: List of (id, name) tuples
        """
        wb = load_workbook(self.excel_path)
        ws = wb.active
        
        students = []
        for row in ws.iter_rows(min_row=2, max_col=2, values_only=True):
            if row[0] is not None:
                students.append((row[0], row[1]))
        
        wb.close()
        return students
    
    def student_exists(self, student_id):
        """
        Check if student exists in database.
        
        Args:
            student_id: Student ID
            
        Returns:
            bool: True if exists
        """
        return self.get_student_name(student_id) is not None
    
    def add_date_column(self, date_str):
        """
        Add or clear a date column for attendance.
        If column exists, clear it. If not, create it.
        
        Args:
            date_str: Date string (e.g., "2024-12-24")
            
        Returns:
            int: Column index of the date column
        """
        wb = load_workbook(self.excel_path)
        ws = wb.active
        
        # Find if date column exists
        date_col = None
        for col_idx, cell in enumerate(ws[1], start=1):
            if cell.value == date_str:
                date_col = col_idx
                break
        
        # If exists, clear the column (except header)
        if date_col:
            for row in range(2, ws.max_row + 1):
                ws.cell(row=row, column=date_col).value = None
            log_info(f"Cleared existing attendance column for date: {date_str}")
        else:
            # Create new column
            date_col = ws.max_column + 1
            ws.cell(row=1, column=date_col).value = date_str
            ws.cell(row=1, column=date_col).font = openpyxl.styles.Font(bold=True)
            log_info(f"Created new attendance column for date: {date_str}")
        
        wb.save(self.excel_path)
        wb.close()
        return date_col
    
    def mark_attendance(self, student_id, date_str):
        """
        Mark attendance for a student on a specific date.
        
        Args:
            student_id: Student ID
            date_str: Date string (e.g., "2024-12-24")
            
        Returns:
            bool: True if marked, False if student not found
        """
        wb = load_workbook(self.excel_path)
        ws = wb.active
        
        # Find date column
        date_col = None
        for col_idx, cell in enumerate(ws[1], start=1):
            if cell.value == date_str:
                date_col = col_idx
                break
        
        if not date_col:
            wb.close()
            log_error(f"Date column not found: {date_str}")
            return False
        
        # Find student row
        student_row = None
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, max_col=1, values_only=False), start=2):
            if row[0].value == student_id:
                student_row = row_idx
                break
        
        if not student_row:
            wb.close()
            log_warning(f"Student not found in database: {student_id}")
            return False
        
        # Mark attendance
        ws.cell(row=student_row, column=date_col).value = ATTENDANCE_MARK
        wb.save(self.excel_path)
        wb.close()
        return True
    
    def mark_multiple_attendance(self, student_ids, date_str):
        """
        Mark attendance for multiple students on a specific date.
        
        Args:
            student_ids: List of student IDs
            date_str: Date string (e.g., "2024-12-24")
            
        Returns:
            dict: {'marked': count, 'not_found': [ids]}
        """
        # Ensure date column exists (and is cleared)
        date_col = self.add_date_column(date_str)
        
        marked_count = 0
        not_found = []
        
        for student_id in student_ids:
            if self.mark_attendance(student_id, date_str):
                marked_count += 1
            else:
                not_found.append(student_id)
        
        log_info(f"Attendance marked for {date_str}: {marked_count} students present")
        if not_found:
            log_warning(f"Students not found in database: {not_found}")
        
        return {
            'marked': marked_count,
            'not_found': not_found
        }
    
    def get_student_count(self):
        """
        Get total number of students in database.
        
        Returns:
            int: Number of students
        """
        wb = load_workbook(self.excel_path)
        ws = wb.active
        count = ws.max_row - 1  # Subtract header row
        wb.close()
        return max(0, count)