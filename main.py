#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片格式转换工具 - PySide6图形界面版本
支持多种格式之间的相互转换
"""

import os
import sys
import traceback
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox, QTabWidget, QComboBox, QLabel
)
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtGui import QFont

from converter import ImageConverter, OutputFormat


class DragDropLineEdit(QLineEdit):
    """支持拖拽的文本框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.drag_mode = "both"  # "file", "folder", or "both"

    def setDragMode(self, mode):
        """设置拖拽模式: file, folder, 或 both"""
        self.drag_mode = mode

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            for url in urls:
                path = url.toLocalFile()
                if path:
                    # 根据模式过滤文件或文件夹
                    if self.drag_mode == "folder":
                        if os.path.isdir(path):
                            self.setText(path)
                            break
                    elif self.drag_mode == "file":
                        if os.path.isfile(path):
                            self.setText(path)
                            break
                    else:  # both
                        self.setText(path)
                        break
        event.acceptProposedAction()


class ConversionWorker(QThread):
    """后台批量转换线程"""
    log_signal = Signal(str)
    progress_signal = Signal(int, int)  # current, total
    finished_signal = Signal(int, int, int)  # total, success, failed

    def __init__(self, source_folder, target_folder, output_format):
        super().__init__()
        self.source_folder = source_folder
        self.target_folder = target_folder
        self.output_format = output_format
        self.is_running = True

    def run(self):
        """执行批量转换任务"""
        try:
            self.log_signal.emit("=" * 60)
            self.log_signal.emit("开始图片格式转换...")
            self.log_signal.emit(f"源文件夹: {self.source_folder}")
            self.log_signal.emit(f"目标文件夹: {self.target_folder}")
            self.log_signal.emit(f"输出格式: {self.output_format.value.upper()}")
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

            # 创建转换器
            converter = ImageConverter(self.output_format)
            ext = converter.output_format.get_extension()

            # 遍历源文件夹中的所有文件
            for idx, file_path in enumerate(all_files, 1):
                if not self.is_running:
                    self.log_signal.emit("转换已取消")
                    break

                total_files += 1
                file_extension = file_path.suffix.lower()

                target_file_path = target_path / f"{file_path.stem}{ext}"

                if target_file_path.exists():
                    self.log_signal.emit(f"覆盖已存在的文件: {target_file_path.name}")

                if file_extension in supported_formats or file_extension == '':
                    success, method = converter.convert_single_image(file_path, target_file_path)
                    if success:
                        self.log_signal.emit(f"✓ {method} 成功转换: {file_path.name}")
                        converted_files += 1
                    else:
                        self.log_signal.emit(f"✗ 转换失败: {file_path.name}")
                        failed_files += 1
                else:
                    self.log_signal.emit(f"未知格式，尝试转换: {file_path.name}")
                    success, method = converter.convert_single_image(file_path, target_file_path)
                    if success:
                        self.log_signal.emit(f"✓ {method} 成功转换: {file_path.name}")
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

    def stop(self):
        """停止转换"""
        self.is_running = False


class SingleFileWorker(QThread):
    """单个文件转换线程"""
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)  # success, message

    def __init__(self, source_file, target_file, output_format):
        super().__init__()
        self.source_file = Path(source_file)
        self.target_file = Path(target_file)
        self.output_format = output_format

    def run(self):
        """执行单个文件转换"""
        try:
            self.log_signal.emit("=" * 60)
            self.log_signal.emit("开始单个图片格式转换...")
            self.log_signal.emit(f"源文件: {self.source_file}")
            self.log_signal.emit(f"目标文件: {self.target_file}")
            self.log_signal.emit(f"输出格式: {self.output_format.value.upper()}")
            self.log_signal.emit("=" * 60)

            # 创建目标文件夹
            self.target_file.parent.mkdir(exist_ok=True, parents=True)

            # 创建转换器并执行转换
            converter = ImageConverter(self.output_format)
            success, method = converter.convert_single_image(self.source_file, self.target_file)

            self.log_signal.emit("=" * 60)
            if success:
                self.log_signal.emit(f"✓ {method} 转换成功！文件已保存至: {self.target_file}")
                self.finished_signal.emit(True, f"文件转换成功！\n已保存至: {self.target_file}")
            else:
                self.log_signal.emit(f"✗ 转换失败")
                self.finished_signal.emit(False, "文件转换失败，请查看日志获取详细信息。")
            self.log_signal.emit("=" * 60)

        except Exception as e:
            self.log_signal.emit(f"发生错误: {str(e)}")
            self.log_signal.emit(traceback.format_exc())
            self.finished_signal.emit(False, f"转换过程中发生错误: {str(e)}")


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

        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # 批量转换标签页
        batch_tab = QWidget()
        self.init_batch_tab(batch_tab)
        self.tab_widget.addTab(batch_tab, "批量转换")

        # 单个文件转换标签页
        single_tab = QWidget()
        self.init_single_tab(single_tab)
        self.tab_widget.addTab(single_tab, "单个文件转换")

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

    def init_batch_tab(self, tab):
        """初始化批量转换标签页"""
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # 源文件夹选择
        source_group = QGroupBox("源文件夹")
        source_layout = QHBoxLayout()
        self.source_edit = DragDropLineEdit()
        self.source_edit.setPlaceholderText("选择包含图片的源文件夹...")
        self.source_edit.setDragMode("folder")  # 只接受文件夹拖拽
        source_browse_btn = QPushButton("浏览...")
        source_browse_btn.clicked.connect(self.browse_source)
        source_browse_btn.setMinimumWidth(100)
        source_layout.addWidget(self.source_edit)
        source_layout.addWidget(source_browse_btn)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        # 目标文件夹选择
        target_group = QGroupBox("目标文件夹")
        target_layout = QHBoxLayout()
        self.target_edit = DragDropLineEdit()
        self.target_edit.setPlaceholderText("选择保存转换后图片的目标文件夹...")
        self.target_edit.setDragMode("folder")  # 只接受文件夹拖拽
        target_browse_btn = QPushButton("浏览...")
        target_browse_btn.clicked.connect(self.browse_target)
        target_browse_btn.setMinimumWidth(100)
        target_layout.addWidget(self.target_edit)
        target_layout.addWidget(target_browse_btn)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

        # 输出格式选择
        format_group = QGroupBox("输出格式")
        format_layout = QHBoxLayout()
        format_label = QLabel("目标格式:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPG", "PNG", "ICO", "WEBP", "BMP", "TIFF"])
        self.format_combo.setCurrentText("JPG")
        self.format_combo.currentTextChanged.connect(self.on_batch_format_changed)
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # 连接文本变化信号以记录拖拽操作
        self.source_edit.textChanged.connect(self.on_source_folder_changed)
        self.target_edit.textChanged.connect(self.on_target_folder_changed)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setMinimumSize(120, 40)
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
        layout.addLayout(button_layout)

        layout.addStretch()

    def init_single_tab(self, tab):
        """初始化单个文件转换标签页"""
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # 源文件选择
        source_group = QGroupBox("源文件")
        source_layout = QHBoxLayout()
        self.single_source_edit = DragDropLineEdit()
        self.single_source_edit.setPlaceholderText("选择要转换的图片文件...")
        self.single_source_edit.setDragMode("file")  # 只接受文件拖拽
        self.single_source_edit.textChanged.connect(self.on_single_source_changed)
        source_browse_btn = QPushButton("浏览...")
        source_browse_btn.clicked.connect(self.browse_single_file)
        source_browse_btn.setMinimumWidth(100)
        source_layout.addWidget(self.single_source_edit)
        source_layout.addWidget(source_browse_btn)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        # 目标文件选择
        target_group = QGroupBox("目标文件")
        target_layout = QHBoxLayout()
        self.single_target_edit = DragDropLineEdit()
        self.single_target_edit.setPlaceholderText("选择保存转换后的文件路径...")
        self.single_target_edit.setDragMode("both")  # 文件和文件夹都可以
        target_browse_btn = QPushButton("浏览...")
        target_browse_btn.clicked.connect(self.browse_single_target)
        target_browse_btn.setMinimumWidth(100)
        target_layout.addWidget(self.single_target_edit)
        target_layout.addWidget(target_browse_btn)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

        # 输出格式选择
        format_group = QGroupBox("输出格式")
        format_layout = QHBoxLayout()
        format_label = QLabel("目标格式:")
        self.single_format_combo = QComboBox()
        self.single_format_combo.addItems(["JPG", "PNG", "ICO", "WEBP", "BMP", "TIFF"])
        self.single_format_combo.setCurrentText("JPG")
        self.single_format_combo.currentTextChanged.connect(self.on_single_format_changed)
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.single_format_combo)
        format_layout.addStretch()
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.single_convert_btn = QPushButton("转换")
        self.single_convert_btn.setMinimumSize(120, 40)
        self.single_convert_btn.clicked.connect(self.start_single_conversion)
        button_layout.addWidget(self.single_convert_btn)

        clear_btn = QPushButton("清空日志")
        clear_btn.setMinimumSize(120, 40)
        clear_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()

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

    @Slot(str)
    def on_source_folder_changed(self, text):
        """当源文件夹路径改变时记录日志"""
        if text.strip() and os.path.isdir(text):
            self.log(f"已选择源文件夹: {text}")

    @Slot(str)
    def on_target_folder_changed(self, text):
        """当目标文件夹路径改变时记录日志"""
        if text.strip() and os.path.isdir(text):
            self.log(f"已选择目标文件夹: {text}")

    @Slot(str)
    def on_batch_format_changed(self, format_text):
        """批量转换格式改变"""
        self.log(f"批量转换目标格式已更改为: {format_text}")

    @Slot()
    def browse_single_file(self):
        """浏览要转换的单个源文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要转换的图片文件", "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.tif *.webp *.jfif *.avif *.heic *.heif *.ico);;所有文件 (*.*)"
        )
        if file_path:
            self.single_source_edit.setText(file_path)
            self.log(f"已选择源文件: {file_path}")
            self.update_single_target_placeholder()

    @Slot(str)
    def on_single_source_changed(self, text):
        """当源文件路径改变时自动更新目标文件提示"""
        if text.strip():
            self.update_single_target_placeholder()

    @Slot(str)
    def on_single_format_changed(self, format_text):
        """单个文件转换格式改变"""
        self.log(f"单个文件转换目标格式已更改为: {format_text}")
        self.update_single_target_placeholder()

    def update_single_target_placeholder(self):
        """更新单个文件转换的目标文件提示"""
        text = self.single_source_edit.text().strip()
        if text:
            try:
                source_path = Path(text)
                if source_path.exists() and source_path.is_file():
                    format_text = self.single_format_combo.currentText()
                    ext = f".{format_text.lower()}"
                    if format_text == "JPEG":
                        ext = ".jpg"
                    target_name = f"{source_path.stem}{ext}"
                    self.single_target_edit.setPlaceholderText(f"将保存为: {target_name} (可拖拽文件夹或手动指定)")
            except Exception:
                pass

    @Slot()
    def browse_single_target(self):
        """浏览单个文件的目标保存路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择保存路径", "",
            "所有文件 (*.*)"
        )
        if file_path:
            self.single_target_edit.setText(file_path)
            self.log(f"已设置目标文件: {file_path}")

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
        """开始批量转换"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "警告", "转换正在进行中，请稍候...")
            return

        source = self.source_edit.text().strip()
        target = self.target_edit.text().strip()
        format_text = self.format_combo.currentText()

        if not source:
            QMessageBox.critical(self, "错误", "请选择源文件夹！")
            return

        if not target:
            QMessageBox.critical(self, "错误", "请选择目标文件夹！")
            return

        if not os.path.exists(source):
            QMessageBox.critical(self, "错误", "源文件夹不存在！")
            return

        # 获取输出格式
        output_format = OutputFormat.from_string(format_text)

        # 禁用转换按钮
        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("转换中...")

        # 创建并启动工作线程
        self.worker = ConversionWorker(source, target, output_format)
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
        """批量转换完成"""
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

    @Slot()
    def start_single_conversion(self):
        """开始单个文件转换"""
        source = self.single_source_edit.text().strip()
        target = self.single_target_edit.text().strip()
        format_text = self.single_format_combo.currentText()

        if not source:
            QMessageBox.critical(self, "错误", "请选择源文件！")
            return

        # 如果未设置目标文件，使用源文件同目录下的文件
        if not target:
            source_path = Path(source)
            ext = f".{format_text.lower()}"
            if format_text == "JPEG":
                ext = ".jpg"
            target = str(source_path.parent / f"{source_path.stem}{ext}")

        if not os.path.exists(source):
            QMessageBox.critical(self, "错误", "源文件不存在！")
            return

        # 获取输出格式
        output_format = OutputFormat.from_string(format_text)

        # 禁用转换按钮
        self.single_convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("转换中...")

        # 使用临时工作线程进行单个文件转换
        self.worker = SingleFileWorker(source, target, output_format)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.single_conversion_finished)
        self.worker.start()

    @Slot(bool, str)
    def single_conversion_finished(self, success, message):
        """单个文件转换完成"""
        self.single_convert_btn.setEnabled(True)
        self.progress_bar.setValue(100)

        if success:
            self.statusBar().showMessage("转换完成！")
            QMessageBox.information(self, "成功", message)
        else:
            self.statusBar().showMessage("转换失败")
            QMessageBox.critical(self, "错误", message)


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 使用windowsvista原生样式
    app.setStyle("windowsvista")

    # 创建主窗口
    window = ImageConverterGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
