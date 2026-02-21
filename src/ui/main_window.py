"""UI shell for the Wish client.

This keeps things minimal for now: a single Fluent-styled window with a
placeholder body. Backend integrations can hook into this window later.
"""

from PyQt5.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget, QVBoxLayout
from qfluentwidgets import (
	FluentIcon,
	NavigationInterface,
	NavigationItemPosition,
)

from .setting import SettingsPage
from .decrypt import DecryptPage
from .friends import FriendsPage


class MainWindow(QMainWindow):
	"""Top-level application window."""

	def __init__(self) -> None:
		super().__init__()
		self._init_window()
		self._init_body()

	def _init_window(self) -> None:
		self.setWindowTitle("Wish Client")
		# FluentIcon.* is an enum; .icon() converts to QIcon expected by Qt APIs
		self.setWindowIcon(FluentIcon.HOME.icon())
		self.resize(960, 600)

	def _init_body(self) -> None:
		central = QWidget(self)
		root_layout = QHBoxLayout(central)
		root_layout.setContentsMargins(0, 0, 0, 0)
		root_layout.setSpacing(0)

		self.stack = QStackedWidget(central)
		self.blank_page = QWidget(self.stack)
		self.stack.addWidget(self.blank_page)

		self.settings_page = self._build_settings_page()
		self.friends_page = self._build_friends_page()
		self.decrypt_page = self._build_decrypt_page()
		self.stack.addWidget(self.settings_page)
		self.stack.addWidget(self.friends_page)
		self.stack.addWidget(self.decrypt_page)

		self.nav = NavigationInterface(self, showMenuButton=False, showReturnButton=False)
		self.nav.setFixedWidth(72)
		self.nav.addItem(
			routeKey="settings",
			icon=FluentIcon.SETTING,
			text="设置",
			onClick=lambda: self._switch_to(self.settings_page),
			selectable=True,
			position=NavigationItemPosition.TOP,
		)
		self.nav.addItem(
			routeKey="decrypt",
			icon=FluentIcon.FOLDER,
			text="文件夹",
			onClick=lambda: self._switch_to(self.decrypt_page),
			selectable=True,
			position=NavigationItemPosition.TOP,
		)
		self.nav.addItem(
			routeKey="friends",
			icon=FluentIcon.PEOPLE,
			text="好友",
			onClick=lambda: self._switch_to(self.friends_page),
			selectable=True,
			position=NavigationItemPosition.TOP,
		)
		

		root_layout.addWidget(self.nav)
		root_layout.addWidget(self.stack, 1)

		self.setCentralWidget(central)
		self._switch_to(self.blank_page)

	def _switch_to(self, widget: QWidget) -> None:
		self.stack.setCurrentWidget(widget)
		# sync selection state for blank page
		if widget is self.blank_page:
			self.nav.setCurrentItem(None)

	def _build_settings_page(self) -> QWidget:
		return SettingsPage(self.stack)

	def _build_friends_page(self) -> QWidget:
		return FriendsPage(self.stack)

	def _build_decrypt_page(self) -> QWidget:
		return DecryptPage(self.stack)
