from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import BodyLabel, PrimaryPushButton


class FriendsDetailView(QWidget):
	"""Displays selected friend's info: avatar, remark, nick, description."""

	def __init__(self, parent: Optional[QWidget] = None) -> None:
		super().__init__(parent)
		self._build_ui()

	def _build_ui(self) -> None:
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(12)

		header = QHBoxLayout()
		header.setSpacing(16)

		self.avatar = QLabel(self)
		self.avatar.setFixedSize(96, 96)
		self.avatar.setStyleSheet(
			"border-radius: 16px; background-color: #f5f5f5; font-size: 28px; font-weight: 600;"
		)
		header.addWidget(self.avatar)

		name_block = QVBoxLayout()
		name_block.setSpacing(6)
		self.remark_label = BodyLabel("", self)
		self.remark_label.setStyleSheet("font-size: 20px; font-weight: 600;")
		self.nick_label = BodyLabel("", self)
		self.nick_label.setStyleSheet("color: #666;")
		name_block.addWidget(self.remark_label)
		name_block.addWidget(self.nick_label)
		header.addLayout(name_block)
		header.addStretch(1)

		self.desc_label = QLabel(self)
		self.desc_label.setWordWrap(True)
		self.desc_label.setStyleSheet("color: #444;")

		self.generate_btn = PrimaryPushButton("生成祝福", self)
		self.generate_btn.setVisible(True)

		layout.addLayout(header)
		layout.addWidget(self.desc_label)
		layout.addWidget(self.generate_btn, alignment=Qt.AlignLeft)
		layout.addStretch(1)

		self.set_placeholder()

	def set_placeholder(self) -> None:
		self.setVisible(False)
		self.avatar.setPixmap(QPixmap())
		self.avatar.setText("?")
		self.avatar.setAlignment(Qt.AlignCenter)
		self.remark_label.setText("选择好友以查看详情")
		self.nick_label.setText("")
		self.desc_label.setText("")
		self.generate_btn.setEnabled(False)

	def set_user(self, *, avatar: Optional[QPixmap], initials: str, remark: str, nick: str, desc: str) -> None:
		self.setVisible(True)
		self.generate_btn.setEnabled(True)
		if avatar:
			self.avatar.setPixmap(
				avatar.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
			)
			self.avatar.setText("")
		else:
			self.avatar.setPixmap(QPixmap())
			self.avatar.setText(initials or "?")
			self.avatar.setAlignment(Qt.AlignCenter)

		self.remark_label.setText(remark)
		self.nick_label.setText(f"昵称：{nick}")
		self.desc_label.setText(desc)
