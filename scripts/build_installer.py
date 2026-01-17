"""
Inno Setup Installation Builder Script
Generates Windows installer packages
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# Set UTF-8 encoding output (Windows compatibility)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Import unified version information
sys.path.insert(0, str(Path(__file__).parent.parent))
from version import VERSION, YEAR, AUTHOR, PRODUCT_NAME, COMPANY_NAME, DESCRIPTION, PRODUCT_WEB_SITE, EXE_NAME

# Directory configuration
PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
MAIN_DIST_DIR = DIST_DIR / "main.dist"
OUTPUT_DIR = PROJECT_ROOT / "output"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Inno Setup configuration
TEMPLATE_FILE = SCRIPTS_DIR / "install.template.iss"
ISS_FILE = SCRIPTS_DIR / "install.iss"

# Application specific configuration (can be modified for other projects)
APP_GUID = "8F4A2B1C-9A3D-4E5F-6B7C-8D9E0F1A2B3C4D"  # Unique GUID identifier
REG_KEY_ID = "IMAGECONVERT"  # Registry key name (short identifier, no braces)
DIST_SUBDIR = "main.dist"  # Distribution subdirectory containing built files
SETUP_FILENAME_BASE = "ImageConvert-Setup"  # Setup file base name (without version and .exe)

# Build expected installer file name
INSTALLER_NAME = f"{SETUP_FILENAME_BASE}-{VERSION}.exe"
EXPECTED_INSTALLER = OUTPUT_DIR / INSTALLER_NAME

# Inno Setup executable path (ISCC.exe)
# Common installation locations
INNO_SETUP_PATHS = [
    r"D:\App\Code\Tools\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    r"C:\Inno Setup 6\ISCC.exe",
]


def find_inno_setup():
    """Find Inno Setup installation path"""
    # First check PATH environment variable
    for path in os.environ.get("PATH", "").split(os.pathsep):
        iscc_path = Path(path) / "ISCC.exe"
        if iscc_path.exists():
            return iscc_path

    # Check common installation locations
    for iscc_path in INNO_SETUP_PATHS:
        if Path(iscc_path).exists():
            return Path(iscc_path)

    return None


def check_prerequisites():
    """Check prerequisites"""
    print("Checking prerequisites...")

    # Check if compiled program exists
    if not MAIN_DIST_DIR.exists():
        print(f"✗ Error: Cannot find compiled program directory")
        print(f"  Expected path: {MAIN_DIST_DIR}")
        print(f"  Please run scripts/build.py to compile first")
        return False

    print(f"✓ Found compiled program: {MAIN_DIST_DIR}")

    # Check if executable file exists
    main_exe = MAIN_DIST_DIR / EXE_NAME
    if not main_exe.exists():
        print(f"✗ Error: Cannot find {EXE_NAME}")
        print(f"  Expected path: {main_exe}")
        return False

    print(f"✓ Found executable: {main_exe}")

    # Check if template file exists
    if not TEMPLATE_FILE.exists():
        print(f"✗ Error: Cannot find Inno Setup template file")
        print(f"  Expected path: {TEMPLATE_FILE}")
        return False

    print(f"✓ Found Inno Setup template: {TEMPLATE_FILE}")

    # Check if Inno Setup is installed
    iscc_path = find_inno_setup()
    if not iscc_path:
        print(f"✗ Error: Inno Setup 6 not found")
        print(f"  Please download and install Inno Setup from:")
        print(f"  https://jrsoftware.org/isdl.php")
        print(f"  Checked paths:")
        for path in INNO_SETUP_PATHS:
            print(f"    - {path}")
        return False

    print(f"✓ Found Inno Setup: {iscc_path}")

    return True


def generate_iss_file():
    """Generate .iss file from template"""
    print("\nGenerating .iss file from template...")

    # Read template
    template_content = TEMPLATE_FILE.read_text(encoding='utf-8')

    # Replace placeholders
    replacements = {
        '__APP_GUID__': APP_GUID,
        '__REG_KEY_ID__': REG_KEY_ID,
        '__PRODUCT_VERSION__': VERSION,
        '__YEAR__': YEAR,
        '__AUTHOR__': AUTHOR,
        '__COMPANY_NAME__': COMPANY_NAME,
        '__PRODUCT_NAME__': PRODUCT_NAME,
        '__DESCRIPTION__': DESCRIPTION,
        '__PRODUCT_WEB_SITE__': PRODUCT_WEB_SITE,
        '__EXE_NAME__': EXE_NAME,
        '__DIST_DIR__': DIST_SUBDIR,
        '__OUTPUT_FILENAME__': SETUP_FILENAME_BASE,
    }

    for placeholder, value in replacements.items():
        template_content = template_content.replace(placeholder, value)

    # Write generated .iss file
    ISS_FILE.write_text(template_content, encoding='utf-8')
    print(f"✓ Generated .iss file: {ISS_FILE}")

    return True


def build_installer():
    """Build installer"""
    print("\nStarting installer build...")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory: {OUTPUT_DIR}")

    # Delete old installer if exists
    if EXPECTED_INSTALLER.exists():
        print(f"✓ Deleting old installer...")
        EXPECTED_INSTALLER.unlink()

    # Find Inno Setup compiler
    iscc_path = find_inno_setup()

    # Build Inno Setup command
    cmd = [
        str(iscc_path),
        str(ISS_FILE)
    ]

    print(f"\nExecuting command:")
    print(f"  {' '.join(cmd)}")
    print()

    try:
        # Execute Inno Setup compilation
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding='gbk',  # Inno Setup uses GBK encoding
            errors='ignore'
        )

        # Display output
        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # Check result
        if result.returncode == 0 and EXPECTED_INSTALLER.exists():
            file_size = EXPECTED_INSTALLER.stat().st_size / (1024 * 1024)  # MB
            print("\n")
            print("✓ Installer built successfully!")
            print(f"File path: {EXPECTED_INSTALLER}")
            print(f"File size: {file_size:.2f} MB")
            print(f"\nYou can now:")
            print(f"1. Distribute this installer to other users")
            print(f"2. Double-click to run installation test")
            return True
        else:
            print("\n")
            print("✗ Installer build failed")
            print(f"Return code: {result.returncode}")
            if EXPECTED_INSTALLER.exists():
                print(f"Warning: Installer file generated despite non-zero return code")
                return True
            return False

    except Exception as e:
        print(f"\n✗ Error during build: {e}")
        return False


def main():
    """Main function"""
    print(f"Inno Setup Installation Builder")
    print(f"Product: {PRODUCT_NAME}")
    print(f"Version: {VERSION}")
    print(f"Description: {DESCRIPTION}")
    print(f"Website: {PRODUCT_WEB_SITE}")

    # Check prerequisites
    if not check_prerequisites():
        print("\n✗ Prerequisites check failed, exiting")
        sys.exit(1)

    # Generate .iss file from template
    if not generate_iss_file():
        print("\n✗ Failed to generate .iss file, exiting")
        sys.exit(1)

    # Build installer
    if build_installer():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
