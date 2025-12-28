"""
ui/AttendanceViewerDialog.py
Attendance viewer dialog with search functionality.
Allows viewing attendance records with date-based and student-based filtering.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from services.StudentDatabase import StudentDatabase
from logger import log_info
from config import (
    COLOR_PRIMARY_BG, COLOR_SECONDARY_BG, COLOR_TEXT_PRIMARY,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_INFO,
    FONT_DIALOG_TITLE, FONT_LABEL, FONT_BUTTON, ATTENDANCE_MARK
)


class AttendanceViewerDialog:
    """Dialog for viewing attendance records with search."""
    
    def __init__(self, parent):
        self.parent = parent
        self.db = StudentDatabase()
        self.view_mode = "single"
        self.selected_date = None
        self.all_data = []  # Store all data for filtering
        
        self._create_dialog()
        self._create_widgets()
        self._load_dates()
    
    def _create_dialog(self):
        """Create main dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Attendance Records")
        self.dialog.geometry("900x700")
        self.dialog.configure(bg=COLOR_PRIMARY_BG)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
    
    def _create_widgets(self):
        """Create all dialog widgets."""
        # Title
        tk.Label(
            self.dialog,
            text="Attendance Records",
            font=FONT_DIALOG_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            pady=15
        ).pack()
        
        # Controls frame
        self._create_controls()
        
        # Search bar (NEW)
        self._create_search_bar()
        
        # View mode toggle
        self._create_view_toggle()
        
        # Table
        self._create_table()
        
        # Statistics
        self._create_statistics()
        
        # Buttons
        self._create_buttons()
    
    def _create_controls(self):
        """Create date selection controls."""
        controls_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        controls_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(
            controls_frame,
            text="Select Date:",
            font=FONT_LABEL,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.date_var = tk.StringVar()
        self.date_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.date_var,
            state="readonly",
            width=15
        )
        self.date_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            controls_frame,
            text="View",
            command=self._view_attendance,
            font=FONT_BUTTON,
            bg=COLOR_INFO,
            fg=COLOR_TEXT_PRIMARY,
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=10)
    
    def _create_search_bar(self):
        """Create search bar for filtering results."""
        search_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        search_frame.pack(pady=5, padx=20, fill=tk.X)
        
        tk.Label(
            search_frame,
            text="Search:",
            font=FONT_LABEL,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._filter_results())
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=FONT_LABEL,
            width=30
        )
        search_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(
            search_frame,
            text="(Search by ID or Name)",
            font=("Helvetica", 9),
            bg=COLOR_PRIMARY_BG,
            fg="#95a5a6"
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_view_toggle(self):
        """Create view mode toggle buttons."""
        toggle_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        toggle_frame.pack(pady=5)
        
        tk.Label(
            toggle_frame,
            text="View Mode:",
            font=FONT_LABEL,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.view_mode_var = tk.StringVar(value="single")
        
        tk.Radiobutton(
            toggle_frame,
            text="Single Date",
            variable=self.view_mode_var,
            value="single",
            command=self._change_view_mode,
            font=FONT_LABEL,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_SECONDARY_BG,
            activebackground=COLOR_PRIMARY_BG,
            activeforeground=COLOR_TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(
            toggle_frame,
            text="Multiple Dates",
            variable=self.view_mode_var,
            value="multi",
            command=self._change_view_mode,
            font=FONT_LABEL,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_SECONDARY_BG,
            activebackground=COLOR_PRIMARY_BG,
            activeforeground=COLOR_TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_table(self):
        """Create attendance table with scrollbar."""
        table_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        table_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview (table)
        self.tree = ttk.Treeview(
            table_frame,
            show='headings',
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            height=12
        )
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
    
    def _create_statistics(self):
        """Create statistics display."""
        self.stats_frame = tk.Frame(self.dialog, bg=COLOR_SECONDARY_BG, relief=tk.SUNKEN, bd=2)
        self.stats_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.stats_label = tk.Label(
            self.stats_frame,
            text="Select a date to view attendance",
            font=("Helvetica", 11),
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            pady=10
        )
        self.stats_label.pack()
    
    def _create_buttons(self):
        """Create action buttons."""
        button_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="Export Report",
            command=self._export_report,
            font=FONT_BUTTON,
            bg=COLOR_SUCCESS,
            fg=COLOR_TEXT_PRIMARY,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy,
            font=FONT_BUTTON,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)
    
    def _load_dates(self):
        """Load all dates from database."""
        dates = self.db.get_all_dates()
        
        if dates:
            self.date_combo['values'] = dates
            self.date_combo.current(0)
        else:
            self.date_combo['values'] = ["No attendance records"]
            messagebox.showinfo(
                "No Records",
                "No attendance records found.\n\nTake attendance first to view records.",
                parent=self.dialog
            )
    
    def _change_view_mode(self):
        """Change view mode between single and multi-date."""
        self.view_mode = self.view_mode_var.get()
        
        if self.view_mode == "multi":
            self._show_multi_date_view()
        else:
            self._clear_table()
            self.stats_label.config(text="Select a date to view attendance")
    
    def _view_attendance(self):
        """View attendance for selected date."""
        selected = self.date_var.get()
        
        if not selected or selected == "No attendance records":
            return
        
        self.selected_date = selected
        
        if self.view_mode == "single":
            self._show_single_date_view(selected)
        else:
            self._show_multi_date_view()
    
    def _show_single_date_view(self, date_str):
        """Show attendance for a single date."""
        # Configure columns
        self.tree['columns'] = ('ID', 'Name', 'Status', 'Rate')
        
        self.tree.heading('ID', text='Student ID')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Status', text=date_str)
        self.tree.heading('Rate', text='Attendance Rate')
        
        self.tree.column('ID', width=100, anchor='center')
        self.tree.column('Name', width=250, anchor='w')
        self.tree.column('Status', width=100, anchor='center')
        self.tree.column('Rate', width=150, anchor='center')
        
        # Clear existing items
        self._clear_table()
        
        # Get attendance data
        attendance = self.db.get_attendance_for_date(date_str)
        
        present_count = 0
        total_count = len(attendance)
        
        # Store all data for filtering
        self.all_data = []
        
        # Add rows
        for student_id, (name, present) in attendance.items():
            status = ATTENDANCE_MARK if present else "-"
            if present:
                present_count += 1
            
            # Get attendance rate
            rate_data = self.db.get_student_attendance_rate(student_id)
            rate_str = f"{rate_data['present']}/{rate_data['total']} ({rate_data['rate']:.1f}%)"
            
            row_data = (student_id, name, status, rate_str)
            self.all_data.append(row_data)
            self.tree.insert('', 'end', values=row_data)
        
        # Update statistics
        if total_count > 0:
            percentage = (present_count / total_count * 100)
            stats_text = f"Date: {date_str}  |  Present: {present_count}/{total_count} ({percentage:.1f}%)"
        else:
            stats_text = "No students in database"
        
        self.stats_label.config(text=stats_text)
    
    def _show_multi_date_view(self):
        """Show attendance for multiple dates."""
        dates = self.db.get_all_dates()
        
        if not dates:
            messagebox.showinfo(
                "No Records",
                "No attendance records to display.",
                parent=self.dialog
            )
            return
        
        # Configure columns (ID, Name, Date1, Date2, ... Rate)
        columns = ['ID', 'Name'] + dates[-5:] + ['Rate']
        self.tree['columns'] = columns
        
        self.tree.heading('ID', text='ID')
        self.tree.heading('Name', text='Name')
        
        for date in dates[-5:]:
            display_date = date[-5:] if len(date) > 10 else date
            self.tree.heading(date, text=display_date)
            self.tree.column(date, width=70, anchor='center')
        
        self.tree.heading('Rate', text='Rate')
        
        self.tree.column('ID', width=80, anchor='center')
        self.tree.column('Name', width=200, anchor='w')
        self.tree.column('Rate', width=120, anchor='center')
        
        # Clear existing items
        self._clear_table()
        
        # Get all students
        students = self.db.get_all_students()
        
        # Store all data for filtering
        self.all_data = []
        
        # Add rows
        for student_id, name in students:
            row_data = [student_id, name]
            
            # Add attendance status for each date
            for date in dates[-5:]:
                attendance = self.db.get_attendance_for_date(date)
                _, present = attendance.get(student_id, (name, False))
                row_data.append(ATTENDANCE_MARK if present else "-")
            
            # Add attendance rate
            rate_data = self.db.get_student_attendance_rate(student_id)
            rate_str = f"{rate_data['rate']:.1f}%"
            row_data.append(rate_str)
            
            self.all_data.append(tuple(row_data))
            self.tree.insert('', 'end', values=row_data)
        
        # Update statistics
        stats_text = f"Viewing last {min(5, len(dates))} dates  |  Total students: {len(students)}"
        self.stats_label.config(text=stats_text)
    
    def _filter_results(self):
        """Filter displayed results based on search query."""
        query = self.search_var.get().lower()
        
        # Clear table
        self._clear_table()
        
        # If no query, show all data
        if not query:
            for row_data in self.all_data:
                self.tree.insert('', 'end', values=row_data)
            return
        
        # Filter and display matching rows
        for row_data in self.all_data:
            # Search in ID (first column) and Name (second column)
            student_id = str(row_data[0]).lower()
            name = str(row_data[1]).lower()
            
            if query in student_id or query in name:
                self.tree.insert('', 'end', values=row_data)
    
    def _clear_table(self):
        """Clear all items from table."""
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def _export_report(self):
        """Export attendance report."""
        # Ask user for format
        format_dialog = tk.Toplevel(self.dialog)
        format_dialog.title("Export Format")
        format_dialog.geometry("300x150")
        format_dialog.configure(bg=COLOR_PRIMARY_BG)
        format_dialog.transient(self.dialog)
        format_dialog.grab_set()
        
        tk.Label(
            format_dialog,
            text="Select Export Format:",
            font=FONT_LABEL,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            pady=20
        ).pack()
        
        result = {'format': None}
        
        def choose_csv():
            result['format'] = 'csv'
            format_dialog.destroy()
        
        def choose_excel():
            result['format'] = 'excel'
            format_dialog.destroy()
        
        button_frame = tk.Frame(format_dialog, bg=COLOR_PRIMARY_BG)
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="CSV",
            command=choose_csv,
            font=FONT_BUTTON,
            bg=COLOR_INFO,
            fg=COLOR_TEXT_PRIMARY,
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="Excel",
            command=choose_excel,
            font=FONT_BUTTON,
            bg=COLOR_SUCCESS,
            fg=COLOR_TEXT_PRIMARY,
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
        
        format_dialog.wait_window()
        
        if not result['format']:
            return
        
        # Get save path
        if result['format'] == 'csv':
            filepath = filedialog.asksaveasfilename(
                title="Save Attendance Report",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                parent=self.dialog
            )
        else:
            filepath = filedialog.asksaveasfilename(
                title="Save Attendance Report",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                parent=self.dialog
            )
        
        if not filepath:
            return
        
        # Export
        if self.db.export_attendance_report(filepath, result['format']):
            messagebox.showinfo(
                "Success",
                f"Attendance report exported to:\n{filepath}",
                parent=self.dialog
            )
    
    def show(self):
        """Show the dialog."""
        self.dialog.wait_window()