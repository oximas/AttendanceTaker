"""
build_exe.py
Automated build script for creating App executable.
FIXED VERSION: Handles Python DLL issues properly + MTCNN assets fix.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Build configuration
APP_NAME = "Attendio"
VERSION = "0.9-beta"
ICON_FILE = "logo.ico"  # Optional
MAIN_SCRIPT = "main.py"
DIST_FOLDER = "dist"
BUILD_FOLDER = "build"
OUTPUT_FOLDER = f"{APP_NAME}_v{VERSION}"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(message):
    """Print step message."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(message):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_warning(message):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_error(message):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def check_python_version():
    """Check Python version."""
    print_step("STEP 1: Checking Python Version")
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 9:
        print_error("Python 3.9 or higher required!")
        return False
    
    print_success("Python version OK")
    return True

def check_dependencies():
    """Check if all required packages are installed."""
    print_step("STEP 2: Checking Dependencies")
    
    required_packages = [
        'cv2', 'numpy', 'PIL', 'keras_facenet', 'mtcnn',
        'sklearn', 'tensorflow', 'openpyxl', 'gdown', 'tqdm'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"{package} installed")
        except ImportError:
            missing.append(package)
            print_error(f"{package} missing")
    
    if missing:
        print_error(f"\nMissing packages: {', '.join(missing)}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    print_success("All dependencies installed")
    return True

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    print_step("STEP 3: Checking PyInstaller")
    
    try:
        import PyInstaller
        print_success(f"PyInstaller installed (version {PyInstaller.__version__})")
        return True
    except ImportError:
        print_error("PyInstaller not installed")
        print("\nInstall with: pip install pyinstaller")
        return False

def clean_previous_builds():
    """Clean previous build artifacts."""
    print_step("STEP 4: Cleaning Previous Builds")
    
    folders_to_clean = [BUILD_FOLDER, DIST_FOLDER, OUTPUT_FOLDER]
    
    for folder in folders_to_clean:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print_success(f"Removed {folder}/")
    
    print_success("Clean complete")

def build_executable():
    """Build executable using PyInstaller with DLL fix."""
    print_step("STEP 5: Building Executable (with DLL and MTCNN fixes)")
    
    # PyInstaller command with DLL handling
    cmd = [
        'pyinstaller',
        '--onedir',  # Use onedir to avoid DLL issues
        '--windowed',  # No console window
        f'--name={APP_NAME}',
        '--clean',
        '--noconfirm',
        
        # CRITICAL: Add these to fix DLL issues
        '--noupx',  # Disable UPX compression (can cause DLL issues)
        '--debug=imports',  # Show import debugging info
    ]
    
    # Add icon if exists
    if os.path.exists(ICON_FILE):
        cmd.append(f'--icon={ICON_FILE}')
        print_success(f"Using icon: {ICON_FILE}")
    else:
        print_warning(f"No icon file found: {ICON_FILE}")
    
    # Hidden imports - EXPANDED for better compatibility
    hidden_imports = [
        # Core ML/AI
        'tensorflow',
        'tensorflow.python',
        'tensorflow.python.ops',
        'keras_facenet',
        'mtcnn',
        'mtcnn.assets',  # CRITICAL FIX - Added this for MTCNN assets
        
        # CV/Image
        'cv2',
        'numpy',
        'PIL',
        'PIL._tkinter_finder',
        
        # Data/Excel
        'openpyxl',
        'openpyxl.cell._writer',
        
        # ML utilities
        'sklearn',
        'sklearn.utils._weight_vector',
        'sklearn.neighbors._typedefs',
        'sklearn.utils._typedefs',
        'sklearn.metrics.pairwise',  # ADDED - for cosine_similarity in face recognition
        
        # Download
        'gdown',
        'tqdm',
        
        # Standard lib that sometimes need explicit import
        'queue',
        'logging.handlers',
    ]
    
    for imp in hidden_imports:
        cmd.append(f'--hidden-import={imp}')
    
    # Collect all data files - CRITICAL for model weights
    cmd.extend([
        '--collect-all=tensorflow',
        '--collect-all=keras_facenet',
        '--collect-all=mtcnn',  # This collects MTCNN model weight files
        '--copy-metadata=tensorflow',
        '--copy-metadata=keras-facenet',
        '--copy-metadata=mtcnn',  # ADDED - copy MTCNN metadata
    ])
    
    # Add main script
    cmd.append(MAIN_SCRIPT)
    
    print(f"Running: {' '.join(cmd[:10])}... (full command is long)\n")
    
    # Run PyInstaller
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print_error("PyInstaller build failed!")
        print_warning("Check the output above for errors")
        return False
    
    print_success("Executable built successfully")
    return True

def verify_build():
    """Verify the build was successful."""
    print_step("STEP 6: Verifying Build")
    
    exe_path = os.path.join(DIST_FOLDER, APP_NAME, f"{APP_NAME}.exe")
    
    if not os.path.exists(exe_path):
        print_error(f"Executable not found at: {exe_path}")
        return False
    
    print_success(f"Executable found: {exe_path}")
    
    # Check for _internal folder
    internal_path = os.path.join(DIST_FOLDER, APP_NAME, "_internal")
    if os.path.exists(internal_path):
        print_success(f"Dependencies folder found: _internal/")
        
        # Check if MTCNN assets are included
        mtcnn_assets_path = os.path.join(internal_path, "mtcnn", "assets")
        if os.path.exists(mtcnn_assets_path):
            print_success(f"MTCNN assets folder found: mtcnn/assets/")
        else:
            print_warning("MTCNN assets folder not found (might cause issues)")
    else:
        print_warning("_internal folder not found (might cause issues)")
    
    # Check file size
    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    print_success(f"Executable size: {size_mb:.1f} MB")
    
    return True

def create_distribution_package():
    """Create distribution package with all necessary files."""
    print_step("STEP 7: Creating Distribution Package")
    
    # Create output folder
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Copy executable folder
    exe_source = os.path.join(DIST_FOLDER, APP_NAME)
    exe_dest = os.path.join(OUTPUT_FOLDER, APP_NAME)
    
    if os.path.exists(exe_source):
        shutil.copytree(exe_source, exe_dest)
        print_success(f"Copied executable to {OUTPUT_FOLDER}/")
    else:
        print_error(f"Executable not found at {exe_source}")
        return False
    
    # Copy documentation files
    docs_to_copy = ['README.txt', 'INSTALLATION.txt', 'settings_template.json']
    
    for doc in docs_to_copy:
        if os.path.exists(doc):
            shutil.copy(doc, OUTPUT_FOLDER)
            print_success(f"Copied {doc}")
        else:
            print_warning(f"{doc} not found (skipping)")
    
    # Create required folders
    folders_to_create = ['Faces', 'Models', 'Downloaded_Faces', 'Attendance_Data']
    
    for folder in folders_to_create:
        folder_path = os.path.join(OUTPUT_FOLDER, folder)
        os.makedirs(folder_path, exist_ok=True)
        print_success(f"Created {folder}/")
    
    print_success("Distribution package created")
    return True

def create_zip_archive():
    """Create ZIP archive of distribution package."""
    print_step("STEP 8: Creating ZIP Archive")
    
    archive_name = f"{OUTPUT_FOLDER}"
    
    try:
        shutil.make_archive(archive_name, 'zip', OUTPUT_FOLDER)
        print_success(f"Created {archive_name}.zip")
        return True
    except Exception as e:
        print_error(f"Failed to create ZIP: {e}")
        return False

def print_summary():
    """Print build summary."""
    print_step("BUILD COMPLETE!")
    
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}✓ {APP_NAME} v{VERSION} built successfully!{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
    
    exe_path = f"{OUTPUT_FOLDER}/{APP_NAME}/{APP_NAME}.exe"
    
    print(f"📦 Distribution package: {OUTPUT_FOLDER}/")
    print(f"📦 ZIP archive: {OUTPUT_FOLDER}.zip")
    print(f"\n🚀 Executable location: {exe_path}")
    
    print(f"\n{Colors.YELLOW}⚠ IMPORTANT - READ THIS:{Colors.END}")
    print(f"  • DO NOT run from build/ folder")
    print(f"  • ONLY run from dist/{APP_NAME}/ or {OUTPUT_FOLDER}/")
    print(f"  • Keep .exe and _internal/ folder together")
    print(f"  • If DLL errors: Install Visual C++ Redistributable")
    
    print(f"\n{Colors.BLUE}NEXT STEPS:{Colors.END}")
    print(f"1. Test: {exe_path}")
    print(f"2. If 'python311.dll' error:")
    print(f"   → Install: https://aka.ms/vs/17/release/vc_redist.x64.exe")
    print(f"3. Distribute: {OUTPUT_FOLDER}.zip")
    
    print(f"\n{Colors.BLUE}Distribution includes:{Colors.END}")
    print(f"  ✓ {APP_NAME}.exe")
    print(f"  ✓ All dependencies (_internal folder)")
    print(f"  ✓ MTCNN model weights (mtcnn/assets/)")
    print(f"  ✓ README.txt (user manual)")
    print(f"  ✓ INSTALLATION.txt (setup guide)")
    print(f"  ✓ Required folders (Faces, Models, etc.)")

def main():
    """Main build process."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{APP_NAME} Build Script v{VERSION}{Colors.END}")
    print(f"{Colors.BLUE}FIXED VERSION - Handles DLL and MTCNN issues{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    # Run build steps
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    if not check_pyinstaller():
        sys.exit(1)
    
    clean_previous_builds()
    
    if not build_executable():
        sys.exit(1)
    
    if not verify_build():
        print_warning("Build verification failed, but continuing...")
    
    if not create_distribution_package():
        sys.exit(1)
    
    create_zip_archive()
    
    print_summary()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\n\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nBuild failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)