#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片格式转换工具 - PySide6图形界面版本
支持多种格式之间的相互转换，批量并发处理
"""

import os
import subprocess
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QTabWidget, QComboBox, QLabel
)
from PySide6.QtCore import QThread, Signal, Slot, QUrl, Qt
from PySide6.QtGui import QFont, QDesktopServices

from .converter import ImageConverter, OutputFormat


# 支持的输入图片格式
SUPPORTED_INPUT_FORMATS = {
    '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif',
    '.webp', '.jfif', '.avif', '.heic', '.heif', '.svg', '.ico',
    '.tga', '.dds', '.pcx', '.pgm', '.ppm', '.pbm', '.ras',
    '.sgi', '.exr', '.hdr',
}


class DragDropLineEdit(QLineEdit):
    """支持拖拽的文本框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.drag_mode = "both"

    def setDragMode(self, mode):
        self.drag_mode = mode

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            for url in urls:
                path = url.toLocalFile()
                if path:
                    if self.drag_mode == "folder":
                        if os.path.isdir(path):
                            self.setText(path)
                            break
                    elif self.drag_mode == "file":
                        if os.path.isfile(path):
                            self.setText(path)
                            break
                    else:
                        self.setText(path)
                        break
        event.acceptProposedAction()


class BatchWorker(QThread):
    """批量转换工作线程（并发执行）"""
    log_signal = Signal(str)
    progress_signal = Signal(int, int)
    finished_signal = Signal(int, int, int)

    def __init__(self, source_folder, target_folder, output_format, max_workers=4):
        super().__init__()
        self.source_folder = source_folder
        self.target_folder = target_folder
        self.output_format = output_format
        self.max_workers = max_workers
        self.is_running = True

    def _convert_one(self, args):
        """转换单个文件（在线程池中执行）"""
        file_path, target_file_path = args
        converter = ImageConverter(self.output_format)
        success, method = converter.convert_single_image(file_path, target_file_path)
        return file_path.name, success, method

    def run(self):
        try:
            self.log_signal.emit("=" * 50)
            self.log_signal.emit(f"开始转换 | 格式: {self.output_format.value.upper()} | 线程数: {self.max_workers}")
            self.log_signal.emit(f"源: {self.source_folder}")
            self.log_signal.emit(f"目标: {self.target_folder}")
            self.log_signal.emit("=" * 50)

            source_path = Path(self.source_folder)
            target_path = Path(self.target_folder)
            target_path.mkdir(exist_ok=True, parents=True)

            converter = ImageConverter(self.output_format)
            ext = converter.output_format.get_extension()

            all_files = [f for f in source_path.iterdir() if f.is_file()]
            total_count = len(all_files)

            if total_count == 0:
                self.log_signal.emit("源文件夹中没有文件")
                self.finished_signal.emit(0, 0, 0)
                return

            tasks = []
            for file_path in all_files:
                target_file_path = target_path / f"{file_path.stem}{ext}"
                tasks.append((file_path, target_file_path))

            converted = 0
            failed = 0

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._convert_one, t): t for t in tasks}
                for idx, future in enumerate(as_completed(futures), 1):
                    if not self.is_running:
                        self.log_signal.emit("转换已取消")
                        break

                    name, success, method = future.result()
                    if success:
                        self.log_signal.emit(f"✓ {method} | {name}")
                        converted += 1
                    else:
                        self.log_signal.emit(f"✗ 失败 | {name}")
                        failed += 1

                    self.progress_signal.emit(idx, total_count)

            self.log_signal.emit("=" * 50)
            self.log_signal.emit(f"完成 | 总计: {total_count} 成功: {converted} 失败: {failed}")
            if total_count > 0:
                self.log_signal.emit(f"成功率: {converted / total_count * 100:.1f}%")
            self.log_signal.emit("=" * 50)

            self.finished_signal.emit(total_count, converted, failed)

        except Exception as e:
            self.log_signal.emit(f"错误: {str(e)}")
            self.log_signal.emit(traceback.format_exc())
            self.finished_signal.emit(0, 0, -1)

    def stop(self):
        self.is_running = False


class SingleFileWorker(QThread):
    """单个文件转换线程"""
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, source_file, target_file, output_format):
        super().__init__()
        self.source_file = Path(source_file)
        self.target_file = Path(target_file)
        self.output_format = output_format

    def run(self):
        try:
            self.log_signal.emit(f"转换: {self.source_file.name} → {self.output_format.value.upper()}")

            self.target_file.parent.mkdir(exist_ok=True, parents=True)

            converter = ImageConverter(self.output_format)
            success, method = converter.convert_single_image(self.source_file, self.target_file)

            if success:
                self.log_signal.emit(f"✓ {method} 转换成功")
                self.finished_signal.emit(True, f"转换成功！\n已保存至: {self.target_file}")
            else:
                self.log_signal.emit("✗ 转换失败")
                self.finished_signal.emit(False, "转换失败，请查看日志。")

        except Exception as e:
            self.log_signal.emit(f"错误: {str(e)}")
            self.finished_signal.emit(False, f"错误: {str(e)}")


class ImageConverterGUI(QMainWindow):
    """主窗口"""

    FORMATS = ["JPG", "PNG", "ICO", "WEBP", "BMP", "TIFF", "GIF", "TGA"]

    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("图片格式转换工具")
        self.setFixedSize(520, 320)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setSpacing(4)
        main.setContentsMargins(6, 6, 6, 6)

        # 标签页
        self.tab_widget = QTabWidget()
        main.addWidget(self.tab_widget)

        batch_tab = QWidget()
        self.init_batch_tab(batch_tab)
        self.tab_widget.addTab(batch_tab, "批量转换")

        single_tab = QWidget()
        self.init_single_tab(single_tab)
        self.tab_widget.addTab(single_tab, "单文件转换")

        # 日志
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 8))
        self.log_text.setMaximumHeight(80)
        main.addWidget(self.log_text)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(14)
        self.progress_bar.setTextVisible(False)
        main.addWidget(self.progress_bar)

        self.statusBar().setStyleSheet("font-size:11px;")
        self.statusBar().showMessage("就绪")

    def init_batch_tab(self, tab):
        layout = QVBoxLayout(tab)
        layout.setSpacing(3)
        layout.setContentsMargins(4, 4, 4, 4)

        # 源
        r1 = QHBoxLayout()
        r1.setSpacing(3)
        r1.addWidget(self._label("源"))
        self.source_edit = DragDropLineEdit()
        self.source_edit.setPlaceholderText("源文件夹...")
        self.source_edit.setDragMode("folder")
        r1.addWidget(self.source_edit)
        r1.addWidget(self._btn("浏览", 48, self.browse_source))
        layout.addLayout(r1)

        # 目标
        r2 = QHBoxLayout()
        r2.setSpacing(3)
        r2.addWidget(self._label("目标"))
        self.target_edit = DragDropLineEdit()
        self.target_edit.setPlaceholderText("目标文件夹...")
        self.target_edit.setDragMode("folder")
        r2.addWidget(self.target_edit)
        r2.addWidget(self._btn("浏览", 48, self.browse_target))
        layout.addLayout(r2)

        # 格式 + 并发数 + 按钮
        r3 = QHBoxLayout()
        r3.setSpacing(3)
        r3.addWidget(self._label("格式"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(self.FORMATS)
        self.format_combo.setCurrentText("JPG")
        self.format_combo.setFixedWidth(65)
        r3.addWidget(self.format_combo)

        r3.addWidget(self._label("线程"))
        self.workers_spin = QComboBox()
        self.workers_spin.addItems(["2", "4", "8", "16"])
        self.workers_spin.setCurrentText("4")
        self.workers_spin.setFixedWidth(50)
        r3.addWidget(self.workers_spin)

        r3.addStretch()
        r3.addWidget(self._btn("开始转换", 70, self.start_conversion))
        r3.addWidget(self._btn("清空日志", 70, self.clear_log))
        r3.addWidget(self._btn("退出", 48, self.close))
        layout.addLayout(r3)

        self.source_edit.textChanged.connect(self.on_source_folder_changed)
        self.target_edit.textChanged.connect(self.on_target_folder_changed)

    def init_single_tab(self, tab):
        layout = QVBoxLayout(tab)
        layout.setSpacing(3)
        layout.setContentsMargins(4, 4, 4, 4)

        # 源
        r1 = QHBoxLayout()
        r1.setSpacing(3)
        r1.addWidget(self._label("源"))
        self.single_source_edit = DragDropLineEdit()
        self.single_source_edit.setPlaceholderText("选择图片文件...")
        self.single_source_edit.setDragMode("file")
        self.single_source_edit.textChanged.connect(self.on_single_source_changed)
        r1.addWidget(self.single_source_edit)
        r1.addWidget(self._btn("浏览", 48, self.browse_single_file))
        layout.addLayout(r1)

        # 目标
        r2 = QHBoxLayout()
        r2.setSpacing(3)
        r2.addWidget(self._label("目标"))
        self.single_target_edit = DragDropLineEdit()
        self.single_target_edit.setPlaceholderText("保存路径（留空则保存到源文件同目录）...")
        self.single_target_edit.setDragMode("both")
        r2.addWidget(self.single_target_edit)
        r2.addWidget(self._btn("浏览", 48, self.browse_single_target))
        layout.addLayout(r2)

        # 格式 + 按钮
        r3 = QHBoxLayout()
        r3.setSpacing(3)
        r3.addWidget(self._label("格式"))
        self.single_format_combo = QComboBox()
        self.single_format_combo.addItems(self.FORMATS)
        self.single_format_combo.setCurrentText("JPG")
        self.single_format_combo.setFixedWidth(65)
        self.single_format_combo.currentTextChanged.connect(self.on_single_format_changed)
        r3.addWidget(self.single_format_combo)
        r3.addStretch()
        r3.addWidget(self._btn("转换", 70, self.start_single_conversion))
        r3.addWidget(self._btn("清空日志", 70, self.clear_log))
        layout.addLayout(r3)

    # ── 辅助 ──

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setFixedWidth(30)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return lbl

    def _btn(self, text, width, slot):
        btn = QPushButton(text)
        btn.setFixedWidth(width)
        btn.setFixedHeight(26)
        btn.clicked.connect(slot)
        return btn

    # ── 浏览 ──

    @Slot()
    def browse_source(self):
        folder = QFileDialog.getExistingDirectory(self, "选择源文件夹")
        if folder:
            self.source_edit.setText(folder)

    @Slot()
    def browse_target(self):
        folder = QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        if folder:
            self.target_edit.setText(folder)

    @Slot()
    def browse_single_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片文件", "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.tif *.webp "
            "*.jfif *.avif *.heic *.heif *.ico *.tga *.dds *.pcx *.exr *.hdr);;"
            "所有文件 (*.*)"
        )
        if file_path:
            self.single_source_edit.setText(file_path)
            self.update_single_target_placeholder()

    @Slot()
    def browse_single_target(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "选择保存路径", "", "所有文件 (*.*)")
        if file_path:
            self.single_target_edit.setText(file_path)

    # ── 信号 ──

    @Slot(str)
    def on_source_folder_changed(self, text):
        if text.strip() and os.path.isdir(text):
            self.log(f"源: {text}")

    @Slot(str)
    def on_target_folder_changed(self, text):
        if text.strip() and os.path.isdir(text):
            self.log(f"目标: {text}")

    @Slot(str)
    def on_single_source_changed(self, text):
        if text.strip():
            self.update_single_target_placeholder()

    @Slot(str)
    def on_single_format_changed(self, text):
        self.update_single_target_placeholder()

    def update_single_target_placeholder(self):
        text = self.single_source_edit.text().strip()
        if text:
            try:
                p = Path(text)
                if p.exists() and p.is_file():
                    fmt = self.single_format_combo.currentText()
                    ext = ".jpg" if fmt == "JPEG" else f".{fmt.lower()}"
                    self.single_target_edit.setPlaceholderText(f"→ {p.stem}{ext}")
            except Exception:
                pass

    # ── 日志 ──

    def log(self, message):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {message}")

    @Slot()
    def clear_log(self):
        self.log_text.clear()

    # ── 批量转换 ──

    @Slot()
    def start_conversion(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "提示", "转换进行中...")
            return

        source = self.source_edit.text().strip()
        target = self.target_edit.text().strip()
        fmt = self.format_combo.currentText()

        if not source:
            QMessageBox.critical(self, "错误", "请选择源文件夹")
            return
        if not target:
            QMessageBox.critical(self, "错误", "请选择目标文件夹")
            return
        if not os.path.exists(source):
            QMessageBox.critical(self, "错误", "源文件夹不存在")
            return

        output_format = OutputFormat.from_string(fmt)
        max_workers = int(self.workers_spin.currentText())

        self.progress_bar.setValue(0)
        self.statusBar().showMessage("转换中...")

        self.worker = BatchWorker(source, target, output_format, max_workers)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.conversion_finished)
        self.worker.start()

    @Slot(int, int)
    def update_progress(self, current, total):
        if total > 0:
            self.progress_bar.setValue(int(current / total * 100))
            self.statusBar().showMessage(f"转换中... {current}/{total}")

    @Slot(int, int, int)
    def conversion_finished(self, total, success, failed):
        self.progress_bar.setValue(100)
        target = self.target_edit.text().strip()

        if failed == -1:
            self.statusBar().showMessage("转换失败")
            QMessageBox.critical(self, "错误", "转换出错，请查看日志")
        else:
            self.statusBar().showMessage(f"完成 {success}/{total}")
            msg = QMessageBox(self)
            msg.setWindowTitle("完成")
            msg.setText(f"成功 {success}  失败 {failed}  共 {total}")
            msg.setIcon(QMessageBox.Information if failed == 0 else QMessageBox.Warning)
            msg.addButton("确定", QMessageBox.AcceptRole)
            if target and os.path.isdir(target):
                msg.addButton("打开目录", QMessageBox.ActionRole)
            msg.exec()
            if target and os.path.isdir(target) and msg.clickedButton().text() == "打开目录":
                QDesktopServices.openUrl(QUrl.fromLocalFile(target))

    # ── 单文件转换 ──

    @Slot()
    def start_single_conversion(self):
        source = self.single_source_edit.text().strip()
        target = self.single_target_edit.text().strip()
        fmt = self.single_format_combo.currentText()

        if not source:
            QMessageBox.critical(self, "错误", "请选择源文件")
            return
        if not os.path.exists(source):
            QMessageBox.critical(self, "错误", "源文件不存在")
            return

        if not target:
            sp = Path(source)
            ext = ".jpg" if fmt == "JPEG" else f".{fmt.lower()}"
            target = str(sp.parent / f"{sp.stem}{ext}")

        output_format = OutputFormat.from_string(fmt)

        self.progress_bar.setValue(0)
        self.statusBar().showMessage("转换中...")

        self.worker = SingleFileWorker(source, target, output_format)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.single_conversion_finished)
        self.worker.start()

    @Slot(bool, str)
    def single_conversion_finished(self, success, message):
        self.progress_bar.setValue(100)

        if success:
            self.statusBar().showMessage("转换完成")
            target_file = self.single_target_edit.text().strip()
            if not target_file:
                sp = Path(self.single_source_edit.text().strip())
                fmt = self.single_format_combo.currentText()
                ext = ".jpg" if fmt == "JPEG" else f".{fmt.lower()}"
                target_file = str(sp.parent / f"{sp.stem}{ext}")

            msg = QMessageBox(self)
            msg.setWindowTitle("完成")
            msg.setText(message)
            msg.setIcon(QMessageBox.Information)
            msg.addButton("确定", QMessageBox.AcceptRole)
            if target_file and os.path.exists(target_file):
                msg.addButton("打开文件位置", QMessageBox.ActionRole)
            msg.exec()
            if target_file and os.path.exists(target_file) and msg.clickedButton().text() == "打开文件位置":
                subprocess.Popen(['explorer', '/select,', os.path.normpath(target_file)])
        else:
            self.statusBar().showMessage("转换失败")
            QMessageBox.critical(self, "错误", message)
