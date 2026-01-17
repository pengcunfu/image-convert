#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片格式转换核心模块
支持多种输入格式和输出格式(JPG, PNG, ICO, WEBP等)
"""

import os
import traceback
from pathlib import Path
from enum import Enum
import cv2
import numpy as np
import imageio
from PIL import Image


class OutputFormat(Enum):
    """支持的输出格式"""
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    ICO = "ico"
    WEBP = "webp"
    BMP = "bmp"
    TIFF = "tiff"

    @classmethod
    def from_string(cls, value):
        """从字符串获取格式"""
        value_map = {
            "jpg": cls.JPG,
            "jpeg": cls.JPEG,
            "png": cls.PNG,
            "ico": cls.ICO,
            "webp": cls.WEBP,
            "bmp": cls.BMP,
            "tiff": cls.TIFF,
        }
        return value_map.get(value.lower(), cls.JPG)

    def get_extension(self):
        """获取文件扩展名"""
        if self == OutputFormat.JPG or self == OutputFormat.JPEG:
            return ".jpg"
        elif self == OutputFormat.PNG:
            return ".png"
        elif self == OutputFormat.ICO:
            return ".ico"
        elif self == OutputFormat.WEBP:
            return ".webp"
        elif self == OutputFormat.BMP:
            return ".bmp"
        elif self == OutputFormat.TIFF:
            return ".tiff"
        return ".jpg"


class ImageConverter:
    """图片转换器"""

    def __init__(self, output_format=OutputFormat.JPG):
        """
        初始化转换器
        :param output_format: 输出格式
        """
        self.output_format = output_format

    def convert_with_opencv(self, file_path, target_path):
        """使用OpenCV转换图片"""
        try:
            img = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
            if img is None:
                return False

            # 根据输出格式处理
            ext = self.output_format.get_extension()

            if ext in [".jpg", ".jpeg"]:
                # JPEG不支持透明通道,需要处理
                if len(img.shape) == 3 and img.shape[2] == 4:  # BGRA
                    bg = np.ones((img.shape[0], img.shape[1], 3), dtype=np.uint8) * 255
                    alpha = img[:, :, 3] / 255.0
                    for c in range(3):
                        bg[:, :, c] = bg[:, :, c] * (1 - alpha) + img[:, :, c] * alpha
                    img = bg
                elif len(img.shape) == 2:  # 灰度图
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                cv2.imwrite(str(target_path), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            elif ext == ".png":
                if len(img.shape) == 2:  # 灰度图
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                cv2.imwrite(str(target_path), img)
            elif ext == ".webp":
                cv2.imwrite(str(target_path), img, [cv2.IMWRITE_WEBP_QUALITY, 95])
            elif ext == ".bmp":
                cv2.imwrite(str(target_path), img)
            elif ext == ".tiff":
                cv2.imwrite(str(target_path), img)
            else:
                return False

            return True
        except Exception as e:
            return False

    def convert_with_imageio(self, file_path, target_path):
        """使用imageio转换图片"""
        try:
            img = imageio.v2.imread(str(file_path))
            ext = self.output_format.get_extension()

            if ext in [".jpg", ".jpeg"]:
                # JPEG不支持透明通道
                if len(img.shape) == 3 and img.shape[2] == 4:  # RGBA
                    bg = np.ones((img.shape[0], img.shape[1], 3), dtype=img.dtype) * 255
                    alpha = img[:, :, 3] / 255.0
                    for c in range(3):
                        bg[:, :, c] = bg[:, :, c] * (1 - alpha) + img[:, :, c] * alpha
                    img = bg.astype(img.dtype)
                elif len(img.shape) == 2:  # 灰度图
                    img = np.stack([img] * 3, axis=-1)
                imageio.v2.imwrite(str(target_path), img, format='JPEG', quality=100)
            elif ext == ".png":
                imageio.v2.imwrite(str(target_path), img, format='PNG')
            elif ext == ".webp":
                imageio.v2.imwrite(str(target_path), img, format='WEBP', quality=95)
            else:
                return False

            return True
        except Exception:
            return False

    def convert_with_pil(self, file_path, target_path):
        """使用Pillow转换图片(支持ICO等特殊格式)"""
        try:
            img = Image.open(str(file_path))
            ext = self.output_format.get_extension()

            # 处理透明通道
            if ext in [".jpg", ".jpeg"]:
                # JPEG不支持透明,需要转为RGB
                if img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        background.paste(img, mask=img.split()[-1])  # 使用alpha通道作为mask
                        img = background
                    else:
                        img = img.convert('RGB')
                else:
                    img = img.convert('RGB')
                img.save(str(target_path), 'JPEG', quality=95, optimize=True)
            elif ext == ".png":
                img.save(str(target_path), 'PNG', optimize=True)
            elif ext == ".ico":
                # ICO格式需要特殊处理
                img.save(str(target_path), 'ICO', sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
            elif ext == ".webp":
                img.save(str(target_path), 'WEBP', quality=95, method=6)
            elif ext == ".bmp":
                img.save(str(target_path), 'BMP')
            elif ext == ".tiff":
                img.save(str(target_path), 'TIFF')
            else:
                return False

            return True
        except Exception:
            return False

    def convert_single_image(self, file_path, target_path):
        """
        尝试多种方法转换单个图片
        :param file_path: 源文件路径
        :param target_path: 目标文件路径
        :return: 是否成功
        """
        methods = []

        # 根据输出格式选择最佳转换方法
        ext = self.output_format.get_extension()
        if ext == ".ico":
            # ICO格式优先使用Pillow
            methods = [("Pillow", self.convert_with_pil)]
        else:
            # 其他格式使用多种方法
            methods = [
                ("Pillow", self.convert_with_pil),
                ("OpenCV", self.convert_with_opencv),
                ("imageio", self.convert_with_imageio)
            ]

        for method_name, convert_func in methods:
            try:
                if convert_func(file_path, target_path):
                    return True, method_name
            except Exception:
                continue

        return False, None
