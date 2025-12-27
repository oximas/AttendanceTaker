"""
ui/StudentManagementDialog.py
Student management dialog for adding, editing, and deleting students.
Provides table view with search, import/export CSV functionality.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from services.StudentDatabase import StudentDatabase
from logger import log_info
from config import (
    COLOR_PRIMARY_BG, COLOR_SECONDARY_BG, COLOR_TEXT_PRIMARY,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_INFO,
    FONT_DIALOG_TITLE, FONT_LABEL, FONT_BUTTON
)


class StudentManagementDialog:
    """Dialog for managing students in the database."""
    
    def __init__(self, parent):
        self.parent = parent
        self.db = StudentDatabase()
        self.filtered_students = []
        
        self._create_dialog()
        self._create_widgets()
        self._load_students()
    
    def _create_dialog(self):
        """Create main dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Student Management")
        self.dialog.geometry("700x600")
        self.dialog.configure(bg=COLOR_PRIMARY_BG)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
    
    def _create_widgets(self):
        """Create all dialog widgets."""
        # Title
        tk.Label(
            self.dialog,
            text="Student Management",
            font=FONT_DIALOG_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            pady=15
        ).pack()
        
        # Search bar
        self._create_search_bar()
        
        # Student table
        self._create_table()
        
        # Buttons
        self._create_buttons()
    
    def _create_search_bar(self):
        """Create search bar."""
        search_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        search_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(
            search_frame,
            text="Search:",
            font=FONT_LABEL,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._filter_students())
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=FONT_LABEL,
            width=40
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_table(self):
        """Create student table with scrollbar."""
        table_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        table_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview (table)
        self.tree = ttk.Treeview(
            table_frame,
            columns=('ID', 'Name'),
            show='headings',
            yscrollcommand=scrollbar.set,
            height=15
        )
        
        # Configure columns
        self.tree.heading('ID', text='Student ID')
        self.tree.heading('Name', text='Name')
        
        self.tree.column('ID', width=150, anchor='center')
        self.tree.column('Name', width=400, anchor='w')
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Double-click to edit
        self.tree.bind('<Double-1>', lambda e: self._edit_student())
    
    def _create_buttons(self):
        """Create action buttons."""
        # Main buttons
        button_frame1 = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        button_frame1.pack(pady=10)
        
        tk.Button(
            button_frame1,
            text="Add Student",
            command=self._add_student,
            font=FONT_BUTTON,
            bg=COLOR_SUCCESS,
            fg=COLOR_TEXT_PRIMARY,
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame1,
            text="Edit Selected",
            command=self._edit_student,
            font=FONT_BUTTON,
            bg=COLOR_INFO,
            fg=COLOR_TEXT_PRIMARY,
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame1,
            text="Delete Selected",
            command=self._delete_student,
            font=FONT_BUTTON,
            bg=COLOR_ERROR,
            fg=COLOR_TEXT_PRIMARY,
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        # Import/Export buttons
        button_frame2 = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        button_frame2.pack(pady=5)
        
        tk.Button(
            button_frame2,
            text="Import from CSV",
            command=self._import_csv,
            font=FONT_BUTTON,
            bg=COLOR_WARNING,
            fg=COLOR_TEXT_PRIMARY,
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame2,
            text="Export to CSV",
            command=self._export_csv,
            font=FONT_BUTTON,
            bg=COLOR_WARNING,
            fg=COLOR_TEXT_PRIMARY,
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        # Close button
        tk.Button(
            self.dialog,
            text="Close",
            command=self.dialog.destroy,
            font=FONT_BUTTON,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            padx=30,
            pady=8
        ).pack(pady=10)
    
    def _load_students(self):
        """Load all students from database."""
        self.all_students = self.db.get_all_students()
        self.filtered_students = self.all_students.copy()
        self._refresh_table()
    
    def _refresh_table(self):
        """Refresh table display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered students
        for student_id, name in self.filtered_students:
            self.tree.insert('', 'end', values=(student_id, name))
    
    def _filter_students(self):
        """Filter students based on search query."""
        query = self.search_var.get().lower()
        
        if not query:
            self.filtered_students = self.all_students.copy()
        else:
            self.filtered_students = [
                (sid, name) for sid, name in self.all_students
                if query in str(sid).lower() or query in name.lower()
            ]
        
        self._refresh_table()
    
    def _add_student(self):
        """Open dialog to add new student."""
        dialog = AddStudentDialog(self.dialog, self.db)
        student_id, name = dialog.show()
        
        if student_id and name:
            if self.db.add_student(student_id, name):
                messagebox.showinfo(
                    "Success",
                    f"Student added:\n{student_id} - {name}",
                    parent=self.dialog
                )
                self._load_students()
            else:
                messagebox.showwarning(
                    "Warning",
                    f"Student ID {student_id} already exists!",
                    parent=self.dialog
                )
    
    def _edit_student(self):
        """Edit selected student."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning(
                "Warning",
                "Please select a student to edit.",
                parent=self.dialog
            )
            return
        
        item = self.tree.item(selection[0])
        student_id, old_name = item['values']
        
        # Open edit dialog
        dialog = EditStudentDialog(self.dialog, student_id, old_name)
        new_name = dialog.show()
        
        if new_name and new_name != old_name:
            if self.db.update_student(student_id, new_name):
                messagebox.showinfo(
                    "Success",
                    f"Student updated:\n{student_id} - {new_name}",
                    parent=self.dialog
                )
                self._load_students()
    
    def _delete_student(self):
        """Delete selected student."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning(
                "Warning",
                "Please select a student to delete.",
                parent=self.dialog
            )
            return
        
        item = self.tree.item(selection[0])
        student_id, name = item['values']
        
        # Confirm deletion
        response = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete:\n{student_id} - {name}?\n\n"
            f"This will NOT delete their attendance records.",
            parent=self.dialog
        )
        
        if response:
            if self.db.delete_student(student_id):
                messagebox.showinfo(
                    "Success",
                    f"Student deleted: {student_id}",
                    parent=self.dialog
                )
                self._load_students()
    
    def _import_csv(self):
        """Import students from CSV file."""
        filepath = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            parent=self.dialog
        )
        
        if not filepath:
            return
        
        stats = self.db.import_from_csv(filepath)
        
        message = f"Import complete!\n\n"
        message += f"Added: {stats['added']} students\n"
        message += f"Skipped (already exist): {stats['skipped']}\n"
        
        if stats['errors']:
            message += f"\nErrors: {len(stats['errors'])}"
        
        messagebox.showinfo("Import Complete", message, parent=self.dialog)
        self._load_students()
    
    def _export_csv(self):
        """Export students to CSV file."""
        filepath = filedialog.asksaveasfilename(
            title="Save CSV File",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            parent=self.dialog
        )
        
        if not filepath:
            return
        
        if self.db.export_to_csv(filepath):
            messagebox.showinfo(
                "Success",
                f"Exported {len(self.all_students)} students to:\n{filepath}",
                parent=self.dialog
            )
    
    def show(self):
        """Show the dialog."""
        self.dialog.wait_window()


class AddStudentDialog:
    """Dialog for adding a new student."""
    
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
        self.student_id = None
        self.name = None
        
        self._create_dialog()
        self._create_widgets()
    
    def _create_dialog(self):
        """Create dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add Student")
        self.dialog.geometry("400x250")
        self.dialog.configure(bg=COLOR_PRIMARY_BG)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        tk.Label(
            self.dialog,
            text="Add New Student",
            font=FONT_DIALOG_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            pady=20
        ).pack()
        
        # ID field
        id_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        id_frame.pack(pady=10, padx=30, fill=tk.X)
        
        tk.Label(
            id_frame,
            text="Student ID:",
            font=FONT_LABEL,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            width=12,
            anchor='w'
        ).pack(side=tk.LEFT)
        
        self.id_var = tk.StringVar()
        tk.Entry(
            id_frame,
            textvariable=self.id_var,
            font=FONT_LABEL,
            width=20
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Name field
        name_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        name_frame.pack(pady=10, padx=30, fill=tk.X)
        
        tk.Label(
            name_frame,
            text="Name:",
            font=FONT_LABEL,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            width=12,
            anchor='w'
        ).pack(side=tk.LEFT)
        
        self.name_var = tk.StringVar()
        tk.Entry(
            name_frame,
            textvariable=self.name_var,
            font=FONT_LABEL,
            width=20
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="Add",
            command=self._submit,
            font=FONT_BUTTON,
            bg=COLOR_SUCCESS,
            fg=COLOR_TEXT_PRIMARY,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
            font=FONT_BUTTON,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)
    
    def _submit(self):
        """Submit new student."""
        student_id = self.id_var.get().strip()
        name = self.name_var.get().strip()
        
        if not student_id or not name:
            messagebox.showwarning(
                "Warning",
                "Please enter both Student ID and Name.",
                parent=self.dialog
            )
            return
        
        if not student_id.isdigit():
            messagebox.showwarning(
                "Warning",
                "Student ID must be numeric.",
                parent=self.dialog
            )
            return
        
        self.student_id = student_id
        self.name = name
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel dialog."""
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and return result."""
        self.dialog.wait_window()
        return self.student_id, self.name


class EditStudentDialog:
    """Dialog for editing a student's name."""
    
    def __init__(self, parent, student_id, current_name):
        self.parent = parent
        self.student_id = student_id
        self.current_name = current_name
        self.new_name = None
        
        self._create_dialog()
        self._create_widgets()
    
    def _create_dialog(self):
        """Create dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Edit Student")
        self.dialog.geometry("400x220")
        self.dialog.configure(bg=COLOR_PRIMARY_BG)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        tk.Label(
            self.dialog,
            text=f"Edit Student: {self.student_id}",
            font=FONT_DIALOG_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            pady=20
        ).pack()
        
        # Name field
        name_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        name_frame.pack(pady=10, padx=30, fill=tk.X)
        
        tk.Label(
            name_frame,
            text="New Name:",
            font=FONT_LABEL,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            width=12,
            anchor='w'
        ).pack(side=tk.LEFT)
        
        self.name_var = tk.StringVar(value=self.current_name)
        tk.Entry(
            name_frame,
            textvariable=self.name_var,
            font=FONT_LABEL,
            width=20
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="Save",
            command=self._submit,
            font=FONT_BUTTON,
            bg=COLOR_SUCCESS,
            fg=COLOR_TEXT_PRIMARY,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
            font=FONT_BUTTON,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)
    
    def _submit(self):
        """Submit updated name."""
        name = self.name_var.get().strip()
        
        if not name:
            messagebox.showwarning(
                "Warning",
                "Please enter a name.",
                parent=self.dialog
            )
            return
        
        self.new_name = name
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel dialog."""
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and return result."""
        self.dialog.wait_window()
        return self.new_name