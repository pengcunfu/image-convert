#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片格式转换脚本
将 images2 文件夹中的所有图片转换为 JPG 格式，并保存到 images 文件夹中
使用多种强大的第三方库确保所有格式都能成功转换，不依赖Pillow
"""

import os
import sys
import traceback
from pathlib import Path
import cv2
import numpy as np
import imageio

# 设置Wand为不可用，专注于OpenCV和imageio
WAND_AVAILABLE = False
print("使用OpenCV和imageio进行图片转换")

def convert_with_wand(file_path, target_path):
    """使用Wand库转换图片"""
    if not WAND_AVAILABLE:
        return False
    try:
        with WandImage(filename=str(file_path)) as img:
            # 设置白色背景（处理透明图片）
            img.background_color = Color('white')
            img.alpha_channel = 'remove'
            # 设置格式为JPEG
            img.format = 'jpeg'
            img.compression_quality = 95
            # 保存
            img.save(filename=str(target_path))
        return True
    except Exception as e:
        print(f"Wand转换失败：{e}")
        return False

def convert_with_opencv(file_path, target_path):
    """使用OpenCV转换图片"""
    try:
        # 读取图片
        img = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
        if img is None:
            return False
        
        # 处理透明通道
        if len(img.shape) == 3 and img.shape[2] == 4:  # BGRA
            # 创建白色背景
            bg = np.ones((img.shape[0], img.shape[1], 3), dtype=np.uint8) * 255
            alpha = img[:, :, 3] / 255.0
            for c in range(3):
                bg[:, :, c] = bg[:, :, c] * (1 - alpha) + img[:, :, c] * alpha
            img = bg
        elif len(img.shape) == 2:  # 灰度图
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        
        # 保存为JPG
        cv2.imwrite(str(target_path), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return True
    except Exception as e:
        print(f"OpenCV转换失败：{e}")
        return False

def convert_with_imageio(file_path, target_path):
    """使用imageio转换图片"""
    try:
        # 读取图片
        img = imageio.v2.imread(str(file_path))
        
        # 处理透明通道
        if len(img.shape) == 3 and img.shape[2] == 4:  # RGBA
            # 创建白色背景
            bg = np.ones((img.shape[0], img.shape[1], 3), dtype=img.dtype) * 255
            alpha = img[:, :, 3] / 255.0
            for c in range(3):
                bg[:, :, c] = bg[:, :, c] * (1 - alpha) + img[:, :, c] * alpha
            img = bg.astype(img.dtype)
        elif len(img.shape) == 2:  # 灰度图
            img = np.stack([img] * 3, axis=-1)
        
        # 保存为JPG
        imageio.v2.imwrite(str(target_path), img, format='JPEG', quality=100)
        return True
    except Exception as e:
        print(f"imageio转换失败：{e}")
        return False

def convert_single_image(file_path, target_path):
    """尝试多种方法转换单个图片"""
    # 根据Wand是否可用调整方法顺序
    if WAND_AVAILABLE:
        methods = [
            ("Wand", convert_with_wand),
            ("OpenCV", convert_with_opencv),
            ("imageio", convert_with_imageio)
        ]
    else:
        methods = [
            ("OpenCV", convert_with_opencv),
            ("imageio", convert_with_imageio)
        ]
    
    for method_name, convert_func in methods:
        try:
            print(f"尝试使用 {method_name} 转换：{file_path.name}")
            if convert_func(file_path, target_path):
                print(f"[成功] {method_name} 转换成功：{file_path.name} -> {target_path.name}")
                return True
        except Exception as e:
            print(f"[失败] {method_name} 转换失败：{e}")
            continue
    
    return False

def convert_images_to_jpg():
    """
    将 images2 文件夹中的所有图片转换为 JPG 格式
    """
    # 定义源文件夹和目标文件夹
    source_folder = Path("images2")
    target_folder = Path("images")
    
    # 检查源文件夹是否存在
    if not source_folder.exists():
        print(f"错误：源文件夹 '{source_folder}' 不存在！")
        return False
    
    # 创建目标文件夹
    target_folder.mkdir(exist_ok=True)
    print(f"已创建目标文件夹：{target_folder}")
    
    # 支持的图片格式（扩展支持更多格式）
    supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', 
                        '.webp', '.jfif', '.avif', '.heic', '.heif', '.svg', '.ico'}
    
    # 统计信息
    total_files = 0
    converted_files = 0
    failed_files = 0
    
    # 遍历源文件夹中的所有文件
    for file_path in source_folder.iterdir():
        if file_path.is_file():
            total_files += 1
            file_extension = file_path.suffix.lower()
            
            # 构建目标文件路径（将扩展名改为.jpg）
            target_file_path = target_folder / f"{file_path.stem}.jpg"
            
            # 强制转换，覆盖已存在的文件
            if target_file_path.exists():
                print(f"覆盖已存在的文件：{target_file_path.name}")
            
            # 检查是否为图片文件（通过扩展名或尝试转换）
            if file_extension in supported_formats or file_extension == '':
                success = convert_single_image(file_path, target_file_path)
                if success:
                    converted_files += 1
                else:
                    print(f"[错误] 所有方法都失败了：{file_path.name}")
                    failed_files += 1
            else:
                # 即使扩展名不在列表中，也尝试转换
                print(f"未知格式，尝试转换：{file_path.name}")
                success = convert_single_image(file_path, target_file_path)
                if success:
                    converted_files += 1
                else:
                    print(f"[错误] 无法转换：{file_path.name}")
                    failed_files += 1
    
    # 输出统计信息
    print("\n" + "="*60)
    print("转换完成！统计信息：")
    print(f"总文件数：{total_files}")
    print(f"成功转换：{converted_files}")
    print(f"转换失败：{failed_files}")
    print(f"成功率：{(converted_files/total_files*100):.1f}%" if total_files > 0 else "0%")
    print("="*60)
    
    return failed_files == 0

def main():
    """主函数"""
    print("开始图片格式转换...")
    print("源文件夹：images2")
    print("目标文件夹：images")
    print("目标格式：JPG")
    print("-" * 30)
    
    try:
        success = convert_images_to_jpg()
        if success:
            print("\n图片转换任务完成！")
        else:
            print("\n图片转换任务失败！")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n用户中断了转换过程。")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生未预期的错误：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
