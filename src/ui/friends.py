import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
	QFrame,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QScrollArea,
	QTextEdit,
	QVBoxLayout,
	QWidget,
)
from qfluentwidgets import BodyLabel

from core.search_users import search_users
from core.get_friend_info import single_user_info
from core.get_chat_data import single_user_all_msg
from core.config_manager import app_config
from core.call_llm import generate_greeting
from .friends_detailed import FriendsDetailView


class FriendsPage(QWidget):
	"""Two-pane friends page with a search bar on the left."""

	def __init__(self, parent: Optional[QWidget] = None) -> None:
		super().__init__(parent)
		self._db_path = self._resolve_db_path()
		self._avatar_cache: Dict[str, Optional[QPixmap]] = {}
		self._selected_item: Optional[QFrame] = None
		self._selected_user: Optional[Dict] = None
		self._init_ui()

	def _init_ui(self) -> None:
		root_layout = QHBoxLayout(self)
		root_layout.setContentsMargins(24, 24, 24, 24)
		root_layout.setSpacing(16)

		self.left_panel = QWidget(self)
		self.left_panel.setFixedWidth(280)
		left_layout = QVBoxLayout(self.left_panel)
		left_layout.setContentsMargins(0, 0, 0, 0)
		left_layout.setSpacing(12)

		self.search_box = QLineEdit(self.left_panel)
		self.search_box.setPlaceholderText("搜索好友")
		self.search_box.setClearButtonEnabled(True)
		self.search_box.returnPressed.connect(self._on_search_submitted)

		self.results_area = QScrollArea(self.left_panel)
		self.results_area.setWidgetResizable(True)
		self.results_area.setFrameShape(QScrollArea.NoFrame)
		self.results_container = QWidget(self.results_area)
		self.results_layout = QVBoxLayout(self.results_container)
		self.results_layout.setContentsMargins(0, 0, 0, 0)
		self.results_layout.setSpacing(8)
		self.results_layout.addStretch(1)
		self.results_area.setWidget(self.results_container)

		left_layout.addWidget(self.search_box)
		left_layout.addWidget(self.results_area, 1)

		self.right_panel = QWidget(self)
		right_layout = QVBoxLayout(self.right_panel)
		right_layout.setContentsMargins(12, 0, 0, 0)
		right_layout.setSpacing(12)

		self.detail_view = FriendsDetailView(self.right_panel)
		right_layout.addWidget(self.detail_view)
		self.detail_view.generate_btn.clicked.connect(self._on_generate_blessing)

		self.blessing_output = QTextEdit(self.right_panel)
		self.blessing_output.setReadOnly(True)
		self.blessing_output.setPlaceholderText("生成的祝福将显示在这里")
		self.blessing_output.setMinimumHeight(160)
		self.blessing_output.setFrameStyle(QFrame.NoFrame)
		self.blessing_output.setStyleSheet("background: transparent; border: none; color: #333;")
		self.blessing_output.setVisible(False)
		right_layout.addWidget(self.blessing_output)

		root_layout.addWidget(self.left_panel)
		root_layout.addWidget(self.right_panel, 1)

		self._show_status_message("输入关键词后按回车搜索好友")

	def _on_search_submitted(self) -> None:
		query = self.search_box.text().strip()
		self._do_search(query)

	def _do_search(self, query: str) -> None:
		if not query:
			self._clear_results()
			self._show_status_message("输入关键词后按回车搜索好友")
			self._hide_blessing_text()
			return

		db_path = self._resolve_db_path()
		self._db_path = db_path
		if not db_path or not db_path.exists():
			self._clear_results()
			self._show_status_message("未找到联系人数据库，请在设置中检查缓存路径")
			self._hide_blessing_text()
			return

		results = search_users(str(db_path), query) or []
		if not results:
			self._clear_results()
			self._show_status_message("没有匹配的好友")
			self._hide_blessing_text()
			return

		self._render_results(results)

	def _render_results(self, users: List[Dict]) -> None:
		self._clear_results()
		items: List[QFrame] = []
		for user in users:
			item = self._build_user_item(user)
			items.append(item)
			self.results_layout.insertWidget(self.results_layout.count() - 1, item)
		# auto-select first result
		if users and items:
			self._handle_user_clicked(None, users[0], items[0])

	def _build_user_item(self, user: Dict) -> QFrame:
		container = QFrame(self.results_container)
		container.setObjectName("friendItem")
		container.setStyleSheet(self._item_style(selected=False))
		container.user_data = user  # store for future detail rendering
		container.setProperty("userData", user)
		container.mousePressEvent = lambda event, u=user, item=container: self._handle_user_clicked(event, u, item)
		container.setCursor(Qt.PointingHandCursor)
		layout = QHBoxLayout(container)
		layout.setContentsMargins(8, 4, 8, 4)
		layout.setSpacing(12)

		avatar_label = QLabel(container)
		avatar_label.setFixedSize(40, 40)
		avatar_label.setStyleSheet(
			"border-radius: 20px; background-color: #f0f0f0; font-weight: 600;"
		)
		pixmap = self._extract_avatar(user)
		if pixmap:
			avatar_label.setPixmap(
				pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
			)
		else:
			avatar_label.setText(self._initials(self._display_name(user)))
			avatar_label.setAlignment(Qt.AlignCenter)

		name_label = BodyLabel(self._display_name(user), container)

		layout.addWidget(avatar_label)
		layout.addWidget(name_label, 1)

		return container

	def _clear_results(self) -> None:
		while self.results_layout.count() > 1:
			item = self.results_layout.takeAt(0)
			widget = item.widget()
			if widget:
				widget.deleteLater()

	def _show_status_message(self, text: str) -> None:
		self._clear_results()
		label = BodyLabel(text, self.results_container)
		label.setStyleSheet("color: #666;")
		self.results_layout.insertWidget(self.results_layout.count() - 1, label)
		self._show_placeholder_detail()
		self._hide_blessing_text()

	def _show_placeholder_detail(self) -> None:
		self.detail_view.set_placeholder()
		self._set_selected_item(None)
		self._hide_blessing_text()

	def _handle_user_clicked(self, event, user: Dict, item: Optional[QFrame] = None) -> None:
		if item is not None:
			self._set_selected_item(item)
		self._selected_user = user
		self._hide_blessing_text()
		name = self._display_name(user)
		pix = self._load_pixmap(user.get("big_head_url") or user.get("bigHeadImgUrl"))
		if not pix:
			pix = self._extract_avatar(user)

		remark = user.get("remark") or name
		nick = user.get("nick_name") or ""
		desc = (user.get("description") or "").strip()
		self.detail_view.set_user(
			avatar=pix,
			initials=self._initials(name),
			remark=remark,
			nick=nick,
			desc=desc,
		)

	def _on_generate_blessing(self) -> None:
		if not self._selected_user:
			print("[生成祝福] 当前未选择好友，忽略。")
			return
		wxid = self._selected_user.get("username") or ""
		if not wxid:
			print("[生成祝福] 选中好友缺少 username，无法查询。")
			return

		self._set_blessing_text("正在生成祝福，请稍候…")

		import time
		# start_time = time.time()
		config = self._load_config()
		cache_dir = (config.get("cache_file_path") or "").strip()
		if not cache_dir:
			print("[生成祝福] cache_file_path 未配置。")
			self._set_blessing_text("缺少缓存路径配置，无法生成祝福。")
			return
		base = Path(cache_dir)
		contact_db = base / "contact.sqlite"
		if not contact_db.exists():
			print(f"[生成祝福] 未找到联系人库: {contact_db}")
			self._set_blessing_text("未找到联系人库，无法生成祝福。")
			return

		message_dbs = sorted(p for p in base.glob("message_*.sqlite") if p.is_file())
		if not message_dbs:
			print("[生成祝福] 未找到任何 message_*.sqlite 日志库。")
			self._set_blessing_text("未找到聊天记录数据库，无法生成祝福。")
			return
		# initialize_time = time.time()
		try:
			user_info = single_user_info(str(contact_db), wxid)
		except Exception as exc:
			print(f"[生成祝福] 读取用户信息失败: {exc}")
			user_info = None
		# user_info_time = time.time()
		try:
			chat_info = single_user_all_msg([str(p) for p in message_dbs], wxid, {1})
		except Exception as exc:
			print(f"[生成祝福] 读取聊天记录失败: {exc}")
			chat_info = []
		#chat_info_time = time.time()
		
  		# 只使用最近的100条消息来生成祝福
		if len(chat_info) > 100:
			chat_info = chat_info[:100]

		chat_history_info = ""
		cfg = app_config.reload()
		current_user_wxid = cfg.get("wx_id", "").strip()
		for msg in chat_info:
			sender = "我" if msg.sender_name == current_user_wxid else "好友"
   
			dt_object = datetime.fromtimestamp(msg.create_time)
			chinese_date = f"{dt_object.year}年{dt_object.month}月{dt_object.day}日 {dt_object.hour}时{dt_object.minute}分"
   
			chat_history_info += f"{sender} ({chinese_date}): {str(msg.message_content)}\n"

		api_key = (config.get("api_key") or "").strip()
		if not api_key:
			self._set_blessing_text("缺少 API Key，无法生成祝福。")
			return

		model_name = (config.get("model_name") or "").strip()
		if not model_name:
			self._set_blessing_text("缺少模型名称，无法生成祝福。")
			return

		# pos_processed_time = time.time()
		try:
			blessing = generate_greeting(user_info, chat_history_info, api_key, model_name)
		except Exception as exc:
			blessing = f"生成祝福失败: {exc}"
		# generate_time = time.time()
		# print(f"生成祝福耗时: 初始化 {initialize_time - start_time:.2f}s")
		# print(f"读取用户信息 {user_info_time - initialize_time:.2f}s")
		# print(f"读取聊天记录 {chat_info_time - user_info_time:.2f}s")
		# print(f"数据处理 {pos_processed_time - chat_info_time:.2f}s")
		# print(f"调用接口 {generate_time - pos_processed_time:.2f}s")
        # 生成祝福耗时: 初始化 0.00s
		# 读取用户信息 0.01s
		# 读取聊天记录 0.03s
		# 数据处理 0.00s
		# 调用接口 53.97s
		self._set_blessing_text(blessing)
		return 

	def _set_selected_item(self, item: Optional[QFrame]) -> None:
		if self._selected_item is item:
			return
		if self._selected_item is not None:
			self._selected_item.setStyleSheet(self._item_style(selected=False))
		self._selected_item = item
		if item is not None:
			item.setStyleSheet(self._item_style(selected=True))

	def _set_blessing_text(self, text: str) -> None:
		text = text or ""
		self.blessing_output.setPlainText(text)
		self.blessing_output.setVisible(bool(text))

	def _hide_blessing_text(self) -> None:
		self.blessing_output.clear()
		self.blessing_output.setVisible(False)

	@staticmethod
	def _item_style(selected: bool) -> str:
		if selected:
			return (
				"#friendItem {border: 1px solid #5b8def; background-color: #e8f0ff;"
				" border-radius: 8px; padding: 8px;}"
			)
		return "#friendItem {border: 1px solid #e5e5e5; border-radius: 8px; padding: 8px;}"

	def _display_name(self, user: Dict) -> str:
		remark = (user.get("remark") or "").strip()
		nick = (user.get("nick_name") or "").strip()
		username = (user.get("username") or "").strip()
		return remark or nick or username or "未命名"

	@staticmethod
	def _initials(name: str) -> str:
		return name[:1].upper() if name else "?"

	def _extract_avatar(self, user: Dict) -> Optional[QPixmap]:
		# Prefer explicit small head URL/path field
		preferred = user.get("small_head_url") or user.get("small_head_img_url")
		if preferred:
			pix = self._load_pixmap(preferred)
			if pix:
				return pix

		candidates = [
			"headimg",
			"avatar",
			"small_head_img",
			"big_head_img",
			"head_img",
			"head_image",
			"smallHeadImgUrl",
			"bigHeadImgUrl",
			"head_img_url",
			"headimgurl",
		]
		for key in candidates:
			val = user.get(key)
			pix = self._load_pixmap(val)
			if pix:
				return pix
		return None

	def _load_pixmap(self, source) -> Optional[QPixmap]:
		if not source:
			return None
		if isinstance(source, (bytes, bytearray)):
			pix = QPixmap()
			if pix.loadFromData(source):
				return pix
		elif isinstance(source, str):
			# http(s) url download with simple in-memory cache
			if source.startswith("http://") or source.startswith("https://"):
				if source in self._avatar_cache:
					return self._avatar_cache[source]
				try:
					with urllib.request.urlopen(source, timeout=5) as resp:
						data = resp.read()
						pix = QPixmap()
						if pix.loadFromData(data):
							self._avatar_cache[source] = pix
							return pix
				except Exception:
					self._avatar_cache[source] = None
				return None

			path_candidate = Path(source)
			if path_candidate.exists():
				pix = QPixmap(str(path_candidate))
				if not pix.isNull():
					return pix
		return None

	def _resolve_db_path(self) -> Optional[Path]:
		config = self._load_config()
		cache_dir = (config.get("cache_file_path") or "").strip()
		if not cache_dir:
			return None
		path = Path(cache_dir).expanduser()
		if path.is_dir():
			return path / "contact.sqlite"
		return path

	def _load_config(self) -> Dict:
		# Reload to keep in sync with updates from settings page
		return app_config.reload()
