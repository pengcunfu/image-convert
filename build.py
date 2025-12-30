import os
import sys

VERSION = "1.0.0"
YEAR = "2025"
AUTHOR = "pengcunfu"

if sys.platform == "win32":
    args = [
        'nuitka',
        '--standalone',
        '--windows-console-mode=disable',
        '--plugin-enable=pyside6',
        '--assume-yes-for-downloads',
        '--msvc=latest',
        # '--mingw64',
        # '--show-memory',
        # '--show-progress',
        '--windows-icon-from-ico=resources/logo.ico',
        '--company-name=ImageConverter',
        '--product-name="图片格式转换工具"',
        f'--file-version={VERSION}',
        f'--product-version={VERSION}',
        '--file-description="图片格式转换工具 - 支持多种格式相互转换"',
        f'--copyright="Copyright(C) {YEAR} {AUTHOR}"',
        '--output-dir=dist',
        '--include-data-files=converter.py=converter.py',
        'main.py',
    ]

    if "--onefile" in sys.argv:
        args.pop(args.index("--standalone"))
        args.insert(1, "--onefile")
        args.insert(1, "--onefile-cache-mode=cached")

elif sys.platform == "darwin":
    args = [
        'python3 -m nuitka',
        '--standalone',
        '--plugin-enable=pyside6',
        # '--show-memory',
        # '--show-progress',
        '--static-libpython=no',
        "--macos-create-app-bundle",
        "--assume-yes-for-download",
        "--macos-app-mode=gui",
        f"--macos-app-version={VERSION}",
        "--macos-app-icon=resources/logo.icns",
        f'--copyright="Copyright(C) {YEAR} {AUTHOR}"',
        '--output-dir=dist',
        '--include-data-files=converter.py=converter.py',
        'main.py',
    ]
else:
    args = [
        'nuitka',
        '--standalone',
        '--plugin-enable=pyside6',
        '--include-qt-plugins=platforms',
        '--assume-yes-for-downloads',
        # '--show-memory',
        # '--show-progress',
        '--linux-icon=resources/logo.png',
        '--output-dir=dist',
        '--include-data-files=converter.py=converter.py',
        'main.py',
    ]

print('Executing:', ' '.join(args))
os.system(' '.join(args))
