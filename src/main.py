"""Application entry point for the Wish client UI.

This boots a Qt application, applies the Fluent theme, and shows the main
window. Backend wiring can be added later; for now we just render the shell
window so the UI stack is verified.
"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme

from ui.main_window import MainWindow


def main() -> int:
	"""Start the Qt event loop and display the main window."""

	# High-DPI awareness for crisp rendering on Windows displays
	QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
	QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

	app = QApplication(sys.argv)
	app.setApplicationName("Wish Client")
	app.setOrganizationName("WishLab")

	setTheme(Theme.AUTO)  # follow system theme; change to Theme.LIGHT/DARK as needed

	window = MainWindow()
	window.show()

	return app.exec_()


if __name__ == "__main__":
	sys.exit(main())
