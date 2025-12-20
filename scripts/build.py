#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片格式转换工具 - PySide6版本打包脚本
使用 PyInstaller 将 PySide6 GUI 程序打包为可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def print_separator(char="=", length=60):
    """打印分隔线"""
    print(char * length)


def print_step(step_num, total_steps, message):
    """打印步骤信息"""
    print(f"\n[{step_num}/{total_steps}] {message}")


def run_command(command, shell=False):
    """运行命令并检查返回值"""
    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, check=True, 
                                   capture_output=False, text=True)
        else:
            result = subprocess.run(command, check=True, 
                                   capture_output=False, text=True, shell=shell)
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: 命令执行失败 (退出码: {e.returncode})")
        return False


def install_dependencies():
    """安装依赖"""
    print_step(1, 3, "检查并安装依赖...")
    
    if not Path("requirements.txt").exists():
        print("警告: requirements.txt 文件不存在")
        return False
    
    command = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    return run_command(command)


def clean_build_files():
    """清理旧的构建文件"""
    print_step(2, 3, "清理旧的构建文件...")
    
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = [
        "convert_images_gui.spec", 
        "图片格式转换工具.spec",
        "图片格式转换工具-PySide6.spec"
    ]
    
    # 删除目录
    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"  ✓ 已删除目录: {dir_name}")
            except Exception as e:
                print(f"  ✗ 删除目录失败 {dir_name}: {e}")
    
    # 删除文件
    for file_name in files_to_remove:
        file_path = Path(file_name)
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"  ✓ 已删除文件: {file_name}")
            except Exception as e:
                print(f"  ✗ 删除文件失败 {file_name}: {e}")
    
    print("  清理完成！")
    return True


def build_executable():
    """使用 PyInstaller 打包程序"""
    print_step(3, 3, "使用 PyInstaller 打包 PySide6 程序...")
    
    # PyInstaller 参数 - 优化版本
    pyinstaller_args = [
        "pyinstaller",
        "--name=图片格式转换工具-PySide6",
        "--onedir",  # 打包成文件夹，启动更快
        "--windowed",
        "--noconfirm",
        "--clean",
        "--optimize=2",  # Python 字节码优化级别
    ]
    
    # UPX 压缩（如果可用）- 减小文件体积
    pyinstaller_args.append("--upx-dir=upx")
    
    # 添加数据文件（如果存在）
    if Path("README.md").exists():
        separator = ";" if sys.platform == "win32" else ":"
        pyinstaller_args.append(f"--add-data=README.md{separator}.")
    
    # 添加隐藏导入 - 只导入必要的模块
    hidden_imports = [
        "cv2",
        "imageio",
        "imageio.plugins",
        "numpy",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets"
    ]
    for module in hidden_imports:
        pyinstaller_args.append(f"--hidden-import={module}")
    
    # 收集必要的数据文件和元数据
    pyinstaller_args.append("--collect-data=imageio")
    pyinstaller_args.append("--copy-metadata=imageio")
    pyinstaller_args.append("--copy-metadata=numpy")
    pyinstaller_args.append("--copy-metadata=opencv-python")
    
    # 排除不需要的模块以减小体积和提升性能
    exclude_modules = [
        "matplotlib",
        "scipy",
        "pandas",
        "tkinter",
        "test",
        "unittest",
        "distutils"
    ]
    for module in exclude_modules:
        pyinstaller_args.append(f"--exclude-module={module}")
    
    # 主程序文件
    pyinstaller_args.append("convert_images_gui.py")
    
    # 打印命令
    print(f"\n执行命令:")
    print(" ".join(pyinstaller_args))
    print()
    
    # 执行打包
    return run_command(pyinstaller_args)


def check_output():
    """检查输出文件"""
    dist_folder = Path("dist") / "图片格式转换工具-PySide6"
    exe_name = "图片格式转换工具-PySide6.exe" if sys.platform == "win32" else "图片格式转换工具-PySide6"
    exe_path = dist_folder / exe_name
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)  # 转换为 MB
        
        # 计算整个文件夹的大小
        total_size = sum(f.stat().st_size for f in dist_folder.rglob('*') if f.is_file())
        total_size_mb = total_size / (1024 * 1024)
        
        print(f"\n✓ 可执行文件已生成: {exe_path}")
        print(f"  主程序大小: {file_size:.2f} MB")
        print(f"  总文件夹大小: {total_size_mb:.2f} MB")
        print(f"  文件数量: {len(list(dist_folder.rglob('*')))}")
        return True
    else:
        print(f"\n✗ 未找到可执行文件: {exe_path}")
        return False


def main():
    """主函数"""
    print_separator()
    print("图片格式转换工具 - PySide6版本打包脚本")
    print_separator()
    
    # 检查主程序文件是否存在
    if not Path("convert_images_gui.py").exists():
        print("\n错误: 找不到 convert_images_gui.py 文件！")
        print("请确保在正确的目录中运行此脚本。")
        return 1
    
    try:
        # 步骤 1: 安装依赖
        if not install_dependencies():
            print("\n错误: 依赖安装失败！")
            return 1
        
        # 步骤 2: 清理旧文件
        if not clean_build_files():
            print("\n警告: 清理文件时出现问题，但继续执行...")
        
        # 步骤 3: 打包程序
        if not build_executable():
            print("\n错误: 打包失败！")
            return 1
        
        # 检查输出
        if not check_output():
            print("\n警告: 打包可能未成功完成")
            return 1
        
        # 成功完成
        print_separator()
        print("打包完成！")
        print_separator()
        if sys.platform == "win32":
            print("\n可执行文件位置: dist\\图片格式转换工具-PySide6\\图片格式转换工具-PySide6.exe")
            print("\n提示: 打包为文件夹模式，启动速度更快！")
            print("      如需分发，请将整个 'dist\\图片格式转换工具-PySide6' 文件夹打包")
        else:
            print("\n可执行文件位置: dist/图片格式转换工具-PySide6/图片格式转换工具-PySide6")
            print("\n提示: 打包为文件夹模式，启动速度更快！")
            print("      如需分发，请将整个 'dist/图片格式转换工具-PySide6' 文件夹打包")
        print()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n用户中断了打包过程。")
        return 1
    except Exception as e:
        print(f"\n发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    
    # Windows 下暂停以便查看输出
    if sys.platform == "win32":
        print("\n按回车键退出...")
        input()
    
    sys.exit(exit_code)
