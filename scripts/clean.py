"""
Clean Build Artifacts Script
Remove generated files and directories from build process
"""
import os
import sys
import shutil
from pathlib import Path

# Set UTF-8 encoding output (Windows compatibility)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Directory configuration
PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
OUTPUT_DIR = PROJECT_ROOT / "output"
BUILD_DIR = PROJECT_ROOT / "build"


def clean_directory(directory: Path, description: str) -> bool:
    """Clean a directory if it exists"""
    if directory.exists():
        try:
            shutil.rmtree(directory)
            print(f"✓ Removed {description}: {directory}")
            return True
        except Exception as e:
            print(f"✗ Failed to remove {description}: {directory}")
            print(f"  Error: {e}")
            return False
    else:
        print(f"⊘ {description} not found: {directory}")
        return False


def clean_file(file_path: Path, description: str) -> bool:
    """Clean a file if it exists"""
    if file_path.exists():
        try:
            file_path.unlink()
            print(f"✓ Removed {description}: {file_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to remove {description}: {file_path}")
            print(f"  Error: {e}")
            return False
    else:
        print(f"⊘ {description} not found: {file_path}")
        return False


def clean_nuitka_cache():
    """Clean Nuitka build cache"""
    nuitka_cache_dirs = []

    # Check for common Nuitka cache locations
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if '__nuitka__' in dirs:
            nuitka_cache_dirs.append(Path(root) / '__nuitka__')

    if nuitka_cache_dirs:
        print("\nCleaning Nuitka cache directories...")
        for cache_dir in nuitka_cache_dirs:
            clean_directory(cache_dir, "Nuitka cache")
    else:
        print("\n⊘ No Nuitka cache directories found")


def clean_python_cache():
    """Clean Python bytecode cache"""
    cache_dirs = []
    cache_files = []

    # Find __pycache__ directories and .pyc files
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Skip virtual environments and node_modules
        if 'venv' in root or 'env' in root or '.venv' in root or 'node_modules' in root:
            continue

        if '__pycache__' in dirs:
            cache_dirs.append(Path(root) / '__pycache__')

        for file in files:
            if file.endswith('.pyc') or file.endswith('.pyo'):
                cache_files.append(Path(root) / file)

    if cache_dirs or cache_files:
        print("\nCleaning Python cache...")
        for cache_dir in cache_dirs:
            clean_directory(cache_dir, "Python cache directory")
        for cache_file in cache_files:
            clean_file(cache_file, "Python cache file")
    else:
        print("\n⊘ No Python cache found")


def main():
    """Main function"""
    print("Clean Build Artifacts")
    print("=" * 50)
    print(f"Project root: {PROJECT_ROOT}")
    print()

    # Parse command line arguments
    clean_all = '--all' in sys.argv or '-a' in sys.argv
    clean_cache = '--cache' in sys.argv or '-c' in sys.argv or clean_all

    # Clean build output directories
    print("Cleaning build output directories...")
    removed_count = 0
    if clean_directory(DIST_DIR, "distribution directory"):
        removed_count += 1
    if clean_directory(OUTPUT_DIR, "output directory"):
        removed_count += 1
    if clean_directory(BUILD_DIR, "build directory"):
        removed_count += 1

    # Clean generated .iss file (it's generated from template)
    iss_file = PROJECT_ROOT / "scripts" / "install.iss"
    if clean_file(iss_file, "generated install.iss"):
        removed_count += 1

    # Clean cache if requested
    if clean_cache:
        clean_nuitka_cache()
        clean_python_cache()

    # Summary
    print()
    print("=" * 50)
    if removed_count > 0:
        print(f"✓ Cleaned {removed_count} build artifact(s)")
    else:
        print("⊘ No build artifacts to clean")
    print()
    print("You can now run a fresh build with:")
    print("  python scripts/build.py          # Build application")
    print("  python scripts/build_installer.py  # Build installer")


if __name__ == "__main__":
    main()
