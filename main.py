#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片格式转换工具 - PySide6图形界面版本
将指定文件夹中的所有图片转换为 JPG 格式
"""

import os
import sys
import traceback
from pathlib import Path
import cv2
import numpy as np
import imageio
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QIcon


class ConversionWorker(QThread):
    """后台转换线程"""
    log_signal = Signal(str)
    progress_signal = Signal(int, int)  # current, total
    finished_signal = Signal(int, int, int)  # total, success, failed
    
    def __init__(self, source_folder, target_folder):
        super().__init__()
        self.source_folder = source_folder
        self.target_folder = target_folder
        self.is_running = True
    
    def run(self):
        """执行转换任务"""
        try:
            self.log_signal.emit("=" * 60)
            self.log_signal.emit("开始图片格式转换...")
            self.log_signal.emit(f"源文件夹: {self.source_folder}")
            self.log_signal.emit(f"目标文件夹: {self.target_folder}")
            self.log_signal.emit("=" * 60)
            
            source_path = Path(self.source_folder)
            target_path = Path(self.target_folder)
            
            # 创建目标文件夹
            target_path.mkdir(exist_ok=True, parents=True)
            self.log_signal.emit(f"已创建目标文件夹: {self.target_folder}")
            
            # 支持的图片格式
            supported_formats = {
                '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif',
                '.webp', '.jfif', '.avif', '.heic', '.heif', '.svg', '.ico'
            }
            
            # 统计信息
            total_files = 0
            converted_files = 0
            failed_files = 0
            
            # 获取所有文件
            all_files = [f for f in source_path.iterdir() if f.is_file()]
            total_count = len(all_files)
            
            # 遍历源文件夹中的所有文件
            for idx, file_path in enumerate(all_files, 1):
                if not self.is_running:
                    self.log_signal.emit("转换已取消")
                    break
                
                total_files += 1
                file_extension = file_path.suffix.lower()
                
                target_file_path = target_path / f"{file_path.stem}.jpg"
                
                if target_file_path.exists():
                    self.log_signal.emit(f"覆盖已存在的文件: {target_file_path.name}")
                
                if file_extension in supported_formats or file_extension == '':
                    success = self.convert_single_image(file_path, target_file_path)
                    if success:
                        converted_files += 1
                    else:
                        self.log_signal.emit(f"✗ 转换失败: {file_path.name}")
                        failed_files += 1
                else:
                    self.log_signal.emit(f"未知格式，尝试转换: {file_path.name}")
                    success = self.convert_single_image(file_path, target_file_path)
                    if success:
                        converted_files += 1
                    else:
                        self.log_signal.emit(f"✗ 无法转换: {file_path.name}")
                        failed_files += 1
                
                # 发送进度信号
                self.progress_signal.emit(idx, total_count)
            
            # 输出统计信息
            self.log_signal.emit("=" * 60)
            self.log_signal.emit("转换完成！统计信息：")
            self.log_signal.emit(f"总文件数: {total_files}")
            self.log_signal.emit(f"成功转换: {converted_files}")
            self.log_signal.emit(f"转换失败: {failed_files}")
            if total_files > 0:
                self.log_signal.emit(f"成功率: {(converted_files/total_files*100):.1f}%")
            self.log_signal.emit("=" * 60)
            
            # 发送完成信号
            self.finished_signal.emit(total_files, converted_files, failed_files)
            
        except Exception as e:
            self.log_signal.emit(f"发生错误: {str(e)}")
            self.log_signal.emit(traceback.format_exc())
            self.finished_signal.emit(0, 0, -1)
    
    def convert_with_opencv(self, file_path, target_path):
        """使用OpenCV转换图片"""
        try:
            img = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
            if img is None:
                return False
            
            # 处理透明通道
            if len(img.shape) == 3 and img.shape[2] == 4:  # BGRA
                bg = np.ones((img.shape[0], img.shape[1], 3), dtype=np.uint8) * 255
                alpha = img[:, :, 3] / 255.0
                for c in range(3):
                    bg[:, :, c] = bg[:, :, c] * (1 - alpha) + img[:, :, c] * alpha
                img = bg
            elif len(img.shape) == 2:  # 灰度图
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            
            cv2.imwrite(str(target_path), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            return True
        except Exception as e:
            self.log_signal.emit(f"OpenCV转换失败：{e}")
            return False
    
    def convert_with_imageio(self, file_path, target_path):
        """使用imageio转换图片"""
        try:
            img = imageio.v2.imread(str(file_path))
            
            # 处理透明通道
            if len(img.shape) == 3 and img.shape[2] == 4:  # RGBA
                bg = np.ones((img.shape[0], img.shape[1], 3), dtype=img.dtype) * 255
                alpha = img[:, :, 3] / 255.0
                for c in range(3):
                    bg[:, :, c] = bg[:, :, c] * (1 - alpha) + img[:, :, c] * alpha
                img = bg.astype(img.dtype)
            elif len(img.shape) == 2:  # 灰度图
                img = np.stack([img] * 3, axis=-1)
            
            imageio.v2.imwrite(str(target_path), img, format='JPEG', quality=100)
            return True
        except Exception as e:
            self.log_signal.emit(f"imageio转换失败：{e}")
            return False
    
    def convert_single_image(self, file_path, target_path):
        """尝试多种方法转换单个图片"""
        methods = [
            ("OpenCV", self.convert_with_opencv),
            ("imageio", self.convert_with_imageio)
        ]
        
        for method_name, convert_func in methods:
            try:
                if convert_func(file_path, target_path):
                    self.log_signal.emit(f"✓ {method_name} 成功转换: {file_path.name}")
                    return True
            except Exception:
                continue
        
        return False
    
    def stop(self):
        """停止转换"""
        self.is_running = False


class ImageConverterGUI(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("图片格式转换工具")
        self.setGeometry(100, 100, 900, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("图片格式转换工具")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 源文件夹选择
        source_group = QGroupBox("源文件夹")
        source_layout = QHBoxLayout()
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("选择包含图片的源文件夹...")
        source_browse_btn = QPushButton("浏览...")
        source_browse_btn.clicked.connect(self.browse_source)
        source_browse_btn.setMinimumWidth(100)
        source_layout.addWidget(self.source_edit)
        source_layout.addWidget(source_browse_btn)
        source_group.setLayout(source_layout)
        main_layout.addWidget(source_group)
        
        # 目标文件夹选择
        target_group = QGroupBox("目标文件夹")
        target_layout = QHBoxLayout()
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("选择保存转换后图片的目标文件夹...")
        target_browse_btn = QPushButton("浏览...")
        target_browse_btn.clicked.connect(self.browse_target)
        target_browse_btn.setMinimumWidth(100)
        target_layout.addWidget(self.target_edit)
        target_layout.addWidget(target_browse_btn)
        target_group.setLayout(target_layout)
        main_layout.addWidget(target_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setMinimumSize(120, 40)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.convert_btn.clicked.connect(self.start_conversion)
        button_layout.addWidget(self.convert_btn)
        
        clear_btn = QPushButton("清空日志")
        clear_btn.setMinimumSize(120, 40)
        clear_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_btn)
        
        exit_btn = QPushButton("退出")
        exit_btn.setMinimumSize(120, 40)
        exit_btn.clicked.connect(self.close)
        button_layout.addWidget(exit_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # 日志区域
        log_group = QGroupBox("转换日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    @Slot()
    def browse_source(self):
        """浏览源文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择源文件夹", "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if folder:
            self.source_edit.setText(folder)
            self.log(f"已选择源文件夹: {folder}")
    
    @Slot()
    def browse_target(self):
        """浏览目标文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择目标文件夹", "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if folder:
            self.target_edit.setText(folder)
            self.log(f"已选择目标文件夹: {folder}")
    
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    @Slot()
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
    
    @Slot()
    def start_conversion(self):
        """开始转换"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "警告", "转换正在进行中，请稍候...")
            return
        
        source = self.source_edit.text().strip()
        target = self.target_edit.text().strip()
        
        if not source:
            QMessageBox.critical(self, "错误", "请选择源文件夹！")
            return
        
        if not target:
            QMessageBox.critical(self, "错误", "请选择目标文件夹！")
            return
        
        if not os.path.exists(source):
            QMessageBox.critical(self, "错误", "源文件夹不存在！")
            return
        
        # 禁用转换按钮
        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("转换中...")
        
        # 创建并启动工作线程
        self.worker = ConversionWorker(source, target)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.conversion_finished)
        self.worker.start()
    
    @Slot(int, int)
    def update_progress(self, current, total):
        """更新进度条"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.statusBar().showMessage(f"转换中... ({current}/{total})")
    
    @Slot(int, int, int)
    def conversion_finished(self, total, success, failed):
        """转换完成"""
        self.convert_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        
        if failed == -1:
            self.statusBar().showMessage("转换失败")
            QMessageBox.critical(self, "错误", "转换过程中发生错误，请查看日志。")
        elif failed == 0:
            self.statusBar().showMessage(f"转换完成！成功: {success}")
            QMessageBox.information(
                self, "成功",
                f"所有图片转换成功！\n共转换 {success} 个文件。"
            )
        else:
            self.statusBar().showMessage(f"转换完成！成功: {success}, 失败: {failed}")
            QMessageBox.warning(
                self, "完成",
                f"转换完成，但有 {failed} 个文件失败。\n成功: {success}, 失败: {failed}"
            )


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建主窗口
    window = ImageConverterGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
