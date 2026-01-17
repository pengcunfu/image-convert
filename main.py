import sys

from PySide6.QtWidgets import  QApplication
from app.window import ImageConverterGUI

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
