"""Decrypt page with a single action to trigger WeChat data decryption."""

from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, PrimaryPushButton

from core.direct_decrypt import decrypt_all_db
from core.config_manager import app_config


class DecryptPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._worker = None
        self._dots_state = 0
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 32, 24, 32)
        layout.setSpacing(16)

        title = BodyLabel("解密微信数据库")
        layout.addWidget(title)

        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        self.status_label = QLabel("准备就绪", self)
        self.indicator = QLabel("...", self)
        self.indicator.setStyleSheet("font-size: 18px;")
        self.indicator.setFixedWidth(36)
        self.indicator.setVisible(False)
        self.check_label = QLabel("✔", self)
        self.check_label.setStyleSheet("font-size: 18px;")
        self.check_label.setVisible(False)
        self.fail_label = QLabel("✖", self)
        self.fail_label.setStyleSheet("font-size: 18px; color: red;")
        self.fail_label.setVisible(False)
        status_row.addWidget(self.status_label)
        status_row.addWidget(self.indicator)
        status_row.addWidget(self.check_label)
        status_row.addWidget(self.fail_label)
        layout.addLayout(status_row)

        self.decrypt_btn = PrimaryPushButton("解密微信数据", self)
        self.decrypt_btn.clicked.connect(self._on_decrypt_clicked)
        layout.addWidget(self.decrypt_btn)
        layout.addStretch(1)

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(350)
        self._anim_timer.timeout.connect(self._tick_anim)

    def _on_decrypt_clicked(self) -> None:
        cfg = self._load_config()
        db_dir = cfg.get("weixin_file_path", "").strip()
        out_dir = cfg.get("cache_file_path", "").strip()
        hex_key = cfg.get("decryption_key", "").strip()

        if not (db_dir and out_dir and hex_key):
            self._set_status("配置缺失，请先在设置中填写路径与密钥。", success=False)
            return

        self._reset_status_running()
        self._worker = _DecryptWorker(db_dir, out_dir, hex_key)
        self._worker.result_ready.connect(self._on_decrypt_result)
        self._worker.start()
        self._anim_timer.start()

    def _on_decrypt_result(self, success: bool) -> None:
        self._anim_timer.stop()
        self.indicator.setVisible(False)
        self.decrypt_btn.setEnabled(True)
        self.check_label.setVisible(success)
        self.fail_label.setVisible(not success)
        self.status_label.setText("解密完成" if success else "解密失败")
        self._worker = None

    def _tick_anim(self) -> None:
        self._dots_state = (self._dots_state + 1) % 3
        dots = "." * (self._dots_state + 1)
        if self.indicator.isVisible():
            self.indicator.setText(dots)

    def _reset_status_running(self) -> None:
        self.status_label.setText("解密进行中")
        self.check_label.setVisible(False)
        self.fail_label.setVisible(False)
        self.indicator.setVisible(True)
        self.decrypt_btn.setEnabled(False)
        self._dots_state = 0
        self.indicator.setText("...")

    def _set_status(self, text: str, success: bool | None) -> None:
        self.status_label.setText(text)
        self.check_label.setVisible(success is True)
        self.fail_label.setVisible(success is False)
        self.indicator.setVisible(False)
        self.decrypt_btn.setEnabled(True)

    def _load_config(self) -> dict:
        try:
            return app_config.reload()
        except Exception as exc:
            print(f"读取配置失败: {exc}")
            return {}


class _DecryptWorker(QThread):
    result_ready = pyqtSignal(bool)

    def __init__(self, db_dir: str, out_dir: str, hex_key: str) -> None:
        super().__init__()
        self.db_dir = db_dir
        self.out_dir = out_dir
        self.hex_key = hex_key

    def run(self) -> None:
        try:
            result = decrypt_all_db(self.db_dir, self.out_dir, self.hex_key)
            self.result_ready.emit(bool(result))
        except Exception as exc:
            print(f"解密异常: {exc}")
            self.result_ready.emit(False)
