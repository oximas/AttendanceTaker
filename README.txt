═══════════════════════════════════════════════════════════════
   ATTENDANCETRACKER v0.9-beta - USER MANUAL
═══════════════════════════════════════════════════════════════

WHAT IS ATTENDANCETRACKER?
═══════════════════════════════════════════════════════════════
AttendanceTracker is an automated student attendance system using
real-time face recognition technology. It eliminates manual
attendance taking and provides accurate tracking through facial
recognition.


SYSTEM REQUIREMENTS
═══════════════════════════════════════════════════════════════
• Windows 10 or higher (64-bit)
• Webcam or IP camera
• 4GB RAM minimum (8GB recommended)
• 2GB free disk space
• Internet connection (for Google Drive downloads)


FIRST TIME SETUP
═══════════════════════════════════════════════════════════════

1. EXTRACT AND RUN
   • Extract all files from ZIP to a folder
   • Run AttendanceTracker.exe
   • Welcome dialog will appear - follow instructions

2. CONFIGURE CAMERA
   • Go to: Settings → Preferences → Camera tab
   • Select camera:
     - 0 = Default webcam
     - 1 = External camera
     - Or enter IP camera URL (e.g., rtsp://192.168.1.100:554)
   • Click "Test Camera" to verify
   • Enable "Flip Horizontally" for webcams (mirror mode)
   • Click "Save Settings" and restart

3. SET GOOGLE DRIVE FOLDER
   • Create a Google Drive folder for student images
   • Make folder PUBLIC:
     - Right-click folder → Share
     - Change to "Anyone with the link can view"
     - Copy the folder URL
   • Go to: Settings → Preferences → Google Drive tab
   • Paste the folder URL
   • Click "Save Settings"

4. ADD STUDENTS TO DATABASE
   Option A - Manual Entry:
   • Go to: Students → Manage Students
   • Click "Add Student"
   • Enter Student ID (numeric) and Name
   • Click "Add"
   
   Option B - Import CSV:
   • Create CSV file with columns: ID,Name
   • Example:
     ID,Name
     12345,Ahmed Mohamed
     12346,Sara Ali
   • Go to: Students → Manage Students
   • Click "Import from CSV"
   • Select your CSV file


COLLECTING STUDENT IMAGES
═══════════════════════════════════════════════════════════════

1. PREPARE IMAGES
   • Each student needs 5-10 clear photos
   • Requirements:
     - Face clearly visible
     - Good lighting
     - No sunglasses/masks
     - Different angles recommended
     - One face per photo

2. CREATE ZIP FILES
   • Create one ZIP file per student
   • Naming format: StudentName_StudentID.zip
   • Examples:
     ✓ Ahmed-Mohamed_12345.zip
     ✓ Sara_Ali_12346.zip
     ✗ Ahmed Mohamed 12345.zip (wrong - no underscore)
     ✗ AhmedMohamed12345.zip (wrong - no separation)

3. UPLOAD TO GOOGLE DRIVE
   • Upload all ZIP files to your Google Drive folder
   • Make sure folder is PUBLIC

4. DOWNLOAD AND PROCESS
   • In app, click "Download & Process Images"
   • Wait for:
     - Download from Google Drive
     - Face extraction from images
     - Automatic model training
   • Check status: Model Status should show "Ready ✓"


TAKING ATTENDANCE
═══════════════════════════════════════════════════════════════

1. DAILY ATTENDANCE
   • Make sure model is trained (status bar shows green)
   • Students stand in front of camera
   • Click "Capture and Detect"
   • App recognizes faces and opens result window
   • Review recognized students
   • Go to: Students → Take Attendance
   • Select date (or use today's date)
   • Click "Confirm"

2. HANDLING UNKNOWN FACES
   • If unknown faces detected, app will prompt
   • Enter Student ID and Name
   • Face is saved for future recognition
   • Model trains automatically with new faces

3. VIEW ATTENDANCE RECORDS
   • Go to: Students → View Attendance Records
   • Select "Single Date View" or "Multiple Dates View"
   • Choose date from dropdown
   • Click "View"
   • See attendance status and statistics
   • Export reports as needed


MANAGING STUDENTS
═══════════════════════════════════════════════════════════════

ADD STUDENT
• Students → Manage Students → Add Student
• Enter ID and Name → Click Add

EDIT STUDENT
• Students → Manage Students
• Double-click student or select and click "Edit Selected"
• Change name → Click Save

DELETE STUDENT
• Students → Manage Students
• Select student → Click "Delete Selected"
• Confirm deletion (attendance records preserved)

IMPORT/EXPORT
• Import from CSV: Bulk add students from file
• Export to CSV: Backup student list


VIEWING & EXPORTING REPORTS
═══════════════════════════════════════════════════════════════

ATTENDANCE REPORTS
• Students → View Attendance Records
• Click "Export Report"
• Choose format: CSV or Excel
• Select save location

STUDENT LIST
• Students → Manage Students
• Click "Export to CSV"
• Select save location


FILE LOCATIONS
═══════════════════════════════════════════════════════════════

All data stored in application folder:

Faces/                     - Student face images
Models/                    - Trained recognition models
Downloaded_Faces/          - Downloaded images (temp)
Attendance_Data/           - Excel attendance database
  students_attendance.xlsx - Main attendance file
  wrong_student_name_format.txt - Invalid file names log
app.log                    - Application activity log
settings.json              - Your settings


TROUBLESHOOTING
═══════════════════════════════════════════════════════════════

CAMERA NOT WORKING
→ Check camera is plugged in and working in other apps
→ Try different camera index (0, 1, 2) in Settings
→ Close other apps using camera
→ Restart application

DOWNLOAD FAILS
→ Check internet connection
→ Verify Google Drive folder is PUBLIC
→ Check folder URL is correct
→ Try opening folder URL in browser

FACES NOT RECOGNIZED
→ Ensure model is trained (check status bar)
→ Need 5-10 clear training photos per student
→ Check lighting - needs to be good
→ Try adjusting confidence threshold in Settings
→ Lower = more lenient, Higher = stricter

SLOW PERFORMANCE
→ Settings → Recognition → Increase "Frame Skip"
→ Close other programs
→ Use lower resolution camera if possible

ATTENDANCE NOT SAVING
→ Close Excel file if open
→ Check file permissions
→ Verify students exist in database first


SETTINGS REFERENCE
═══════════════════════════════════════════════════════════════

CAMERA SETTINGS
• Camera Source: 0 (webcam), 1 (external), or URL
• Flip Horizontally: Mirror mode for webcams
• Capture Frame Count: Frames captured (1-10)

RECOGNITION SETTINGS
• Confidence Threshold: 0.4-0.6 recommended
  - Lower = More lenient matching
  - Higher = Stricter matching
• Min Face Size: Minimum face pixels to detect (20-40)
• Frame Skip: Higher = less CPU usage (50-150)

GENERAL SETTINGS
• Attendance Mark: Symbol used in Excel (✓, P, X)
• Window Size: Main window dimensions


SUPPORT & HELP
═══════════════════════════════════════════════════════════════

Built-in Help:
• Help → Quick Start Guide
• Help → Troubleshooting

Contact Support:
• Email: oximas2004@gmail.com
• Include app.log file when reporting issues

Check Logs:
• Open app.log in application folder
• Look for [ERROR] lines
• Include in support emails


VERSION INFORMATION
═══════════════════════════════════════════════════════════════
Version: 0.9-beta
Last Updated: December 2024

Powered by:
• FaceNet (Face Recognition)
• MTCNN (Face Detection)
• OpenCV (Computer Vision)
• TensorFlow (Machine Learning)


═══════════════════════════════════════════════════════════════
           END OF USER MANUAL - Thank you for using
                    AttendanceTracker!
═══════════════════════════════════════════════════════════════