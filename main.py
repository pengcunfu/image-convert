import sys

from PySide6.QtWidgets import QApplication
from app.window import ImageConverterGUI


def main():
    app = QApplication(sys.argv)
    app.setStyle("windowsvista")

    window = ImageConverterGUI()

    # 窗口居中
    screen = app.primaryScreen()
    if screen:
        geo = screen.availableGeometry()
        x = (geo.width() - window.width()) // 2 + geo.x()
        y = (geo.height() - window.height()) // 2 + geo.y()
        window.move(x, y)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
