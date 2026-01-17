import sys
import subprocess
from pathlib import Path

# Import version information
sys.path.insert(0, str(Path(__file__).parent.parent))
from version import VERSION, YEAR, AUTHOR, COMPANY_NAME, PRODUCT_NAME, DESCRIPTION, EXE_NAME

if sys.platform == "win32":
    args = [
        sys.executable, '-m', 'nuitka',
        '--standalone',
        '--windows-console-mode=disable',
        '--plugin-enable=pyside6',
        '--assume-yes-for-downloads',
        '--msvc=latest',
        '--windows-icon-from-ico=resources/icon.ico',
        '--include-data-dir=app=app',
        f'--company-name={COMPANY_NAME}',
        f'--product-name={PRODUCT_NAME}',
        f'--file-version={VERSION}',
        f'--product-version={VERSION}',
        f'--file-description={DESCRIPTION}',
        f'--copyright=Copyright(C) {YEAR} {AUTHOR}',
        '--output-dir=dist',
        f'--output-filename={EXE_NAME}',
        'main.py',
    ]

    if "--onefile" in sys.argv:
        args.insert(1, "--onefile")
        args.insert(2, "--onefile-cache-mode=cached")

elif sys.platform == "darwin":
    args = [
        'python3', '-m', 'nuitka',
        '--standalone',
        '--plugin-enable=pyside6',
        '--static-libpython=no',
        '--macos-create-app-bundle',
        '--assume-yes-for-downloads',
        '--macos-app-mode=gui',
        f'--macos-app-version={VERSION}',
        '--macos-app-icon=resources/icon.icns',
        f'--copyright=Copyright(C) {YEAR} {AUTHOR}',
        '--output-dir=dist',
        'main.py',
    ]
else:
    args = [
        sys.executable, '-m', 'nuitka',
        '--standalone',
        '--plugin-enable=pyside6',
        '--include-qt-plugins=platforms',
        '--assume-yes-for-downloads',
        '--linux-icon=resources/icon.png',
        '--output-dir=dist',
        'main.py',
    ]

print('Executing command:', ' '.join(args))
subprocess.run(args, check=True)
