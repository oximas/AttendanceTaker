"""
services/StudentDatabase.py
Manages student attendance database in Excel format.
Handles student record creation, attendance marking, database queries, and reporting.
Logs all database operations for tracking and troubleshooting.
"""

import os
import csv
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
    
    def update_student(self, student_id, new_name):
        """
        Update student name.
        
        Args:
            student_id: Student ID
            new_name: New student name
            
        Returns:
            bool: True if updated, False if not found
        """
        wb = load_workbook(self.excel_path)
        ws = wb.active
        
        # Find and update student
        updated = False
        for row in ws.iter_rows(min_row=2):
            if row[0].value == student_id:
                old_name = row[1].value
                row[1].value = new_name
                updated = True
                log_info(f"Student updated: ID={student_id}, {old_name} → {new_name}")
                break
        
        if updated:
            wb.save(self.excel_path)
        
        wb.close()
        return updated
    
    def delete_student(self, student_id):
        """
        Delete a student from the database.
        
        Args:
            student_id: Student ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        wb = load_workbook(self.excel_path)
        ws = wb.active
        
        # Find and delete student row
        deleted = False
        for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
            if row[0].value == student_id:
                ws.delete_rows(row_idx)
                deleted = True
                log_info(f"Student deleted: ID={student_id}")
                break
        
        if deleted:
            wb.save(self.excel_path)
        
        wb.close()
        return deleted
    
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
    
    def get_all_dates(self):
        """
        Get all dates that have attendance recorded.
        
        Returns:
            list: List of date strings (from column headers)
        """
        wb = load_workbook(self.excel_path)
        ws = wb.active
        
        dates = []
        # Skip first 2 columns (ID, Name)
        for col_idx in range(3, ws.max_column + 1):
            date_value = ws.cell(row=1, column=col_idx).value
            if date_value:
                dates.append(str(date_value))
        
        wb.close()
        return dates
    
    def get_attendance_for_date(self, date_str):
        """
        Get attendance for a specific date.
        
        Args:
            date_str: Date string (e.g., "2024-12-27")
            
        Returns:
            dict: {student_id: (name, present), ...}
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
            return {}
        
        # Get attendance for all students
        attendance = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] is not None:  # Has student ID
                student_id = row[0]
                student_name = row[1] if len(row) > 1 else "Unknown"
                # Check if present (date_col-1 because enumerate starts at 1)
                present = len(row) >= date_col and row[date_col - 1] == ATTENDANCE_MARK
                attendance[student_id] = (student_name, present)
        
        wb.close()
        return attendance
    
    def get_student_attendance_rate(self, student_id):
        """
        Calculate attendance rate for a student.
        
        Args:
            student_id: Student ID
            
        Returns:
            dict: {'present': int, 'total': int, 'rate': float}
        """
        wb = load_workbook(self.excel_path)
        ws = wb.active
        
        # Find student row
        student_row = None
        for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
            if row[0].value == student_id:
                student_row = row_idx
                break
        
        if not student_row:
            wb.close()
            return {'present': 0, 'total': 0, 'rate': 0.0}
        
        # Count attendance (skip ID and Name columns)
        present_count = 0
        total_dates = 0
        
        for col_idx in range(3, ws.max_column + 1):
            cell_value = ws.cell(row=student_row, column=col_idx).value
            if ws.cell(row=1, column=col_idx).value:  # Date column exists
                total_dates += 1
                if cell_value == ATTENDANCE_MARK:
                    present_count += 1
        
        wb.close()
        
        rate = (present_count / total_dates * 100) if total_dates > 0 else 0.0
        
        return {
            'present': present_count,
            'total': total_dates,
            'rate': rate
        }
    
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
    
    def import_from_csv(self, csv_path):
        """
        Import students from CSV file.
        CSV format: ID,Name (with header row)
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            dict: {'added': count, 'skipped': count, 'errors': []}
        """
        stats = {'added': 0, 'skipped': 0, 'errors': []}
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)  # Skip header
                
                for row in reader:
                    if len(row) < 2:
                        stats['errors'].append(f"Invalid row: {row}")
                        continue
                    
                    student_id = row[0].strip()
                    student_name = row[1].strip()
                    
                    if self.add_student(student_id, student_name):
                        stats['added'] += 1
                    else:
                        stats['skipped'] += 1
            
            log_info(f"CSV import complete: {stats['added']} added, {stats['skipped']} skipped")
            
        except Exception as e:
            log_error("CSV import failed", e)
            stats['errors'].append(str(e))
        
        return stats
    
    def export_to_csv(self, csv_path):
        """
        Export students to CSV file.
        
        Args:
            csv_path: Path to save CSV file
            
        Returns:
            bool: True if successful
        """
        try:
            students = self.get_all_students()
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Name'])
                writer.writerows(students)
            
            log_info(f"Exported {len(students)} students to CSV: {csv_path}")
            return True
            
        except Exception as e:
            log_error("CSV export failed", e)
            return False
    
    def export_attendance_report(self, output_path, file_format='csv'):
        """
        Export complete attendance report.
        
        Args:
            output_path: Path to save file
            file_format: 'csv' or 'excel'
            
        Returns:
            bool: True if successful
        """
        try:
            if file_format == 'excel':
                # Copy the Excel file directly
                import shutil
                shutil.copy(self.excel_path, output_path)
                log_info(f"Attendance report exported to Excel: {output_path}")
                return True
            
            else:  # CSV
                wb = load_workbook(self.excel_path)
                ws = wb.active
                
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Write all rows
                    for row in ws.iter_rows(values_only=True):
                        writer.writerow(row)
                
                wb.close()
                log_info(f"Attendance report exported to CSV: {output_path}")
                return True
                
        except Exception as e:
            log_error("Attendance report export failed", e)
            return False