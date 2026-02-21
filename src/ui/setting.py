"""Settings page layout.

Provides inputs for WeChat storage path, WeChat ID, and Key, plus action buttons.
"""

import subprocess

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import BodyLabel, LineEdit, PrimaryPushButton, PushButton
from core.get_key import get_key
from core.config_manager import app_config


class SettingsPage(QWidget):
    """Simple settings form with three inputs and two actions."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()
        self._wire_events()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 32, 24, 32)
        layout.setSpacing(16)

        self.ori_path_input = self._add_field(layout, "微信数据路径", "请输入微信数据存储路径，类似 C:\\Users\\User\\Documents\\WeChat Files\\wxid_xxx")
        self.cache_path_input = self._add_field(layout, "缓存数据路径", "一个可以用来放置数据的空文件夹，请勿包含中文路径")

        paths_btn_row = QHBoxLayout()
        paths_btn_row.setSpacing(12)
        paths_btn_row.setAlignment(Qt.AlignHCenter)
        self.auto_path_btn = PushButton("自动生成路径（暂不可用）", self)
        self.save_path_btn = PrimaryPushButton("保存路径信息", self)
        paths_btn_row.addWidget(self.auto_path_btn)
        paths_btn_row.addWidget(self.save_path_btn)
        layout.addLayout(paths_btn_row)

        self.key_input = self._add_field(layout, "Decryption Key", "点击下方自动获取")

        key_btn_row = QHBoxLayout()
        key_btn_row.setAlignment(Qt.AlignHCenter)
        self.auto_key_btn = PushButton("自动捕获密钥", self)
        self.save_key_btn = PrimaryPushButton("保存密钥", self)
        key_btn_row.addWidget(self.auto_key_btn)
        key_btn_row.addWidget(self.save_key_btn)
        layout.addLayout(key_btn_row)

        self.model_name_input = self._add_field(layout, "模型名称", "例如：GLM-5、gemini-3-flash-preview、qwen3.5-397b-a17b")
        self.model_api_input = self._add_field(layout, "模型 API Key", "用于生成祝福的 API Key")

        model_btn_row = QHBoxLayout()
        model_btn_row.setSpacing(12)
        model_btn_row.setAlignment(Qt.AlignHCenter)
        self.save_model_btn = PrimaryPushButton("保存模型设置", self)
        model_btn_row.addWidget(self.save_model_btn)
        layout.addLayout(model_btn_row)

        layout.addStretch(1)
    # 添加回调函数入口
    def _wire_events(self) -> None:
        self.save_path_btn.clicked.connect(self._save_paths)
        # auto_path_btn is exposed for later wiring to search logic
        # self.auto_path_btn.clicked.connect(self._auto_generate_paths)
        self.auto_key_btn.clicked.connect(self._show_key_capture_hint)
        self.save_key_btn.clicked.connect(self._save_key)
        self.save_model_btn.clicked.connect(self._save_model_settings)
    
    ##########################
    # save_path_btn
    def _save_paths(self) -> None:
        wx_path = self._normalize_path_input(self.ori_path_input.text())
        cache_path = self._normalize_path_input(self.cache_path_input.text())
        assert wx_path and cache_path, "路径不能为空"
        assert "wxid_" in wx_path, "微信数据路径应包含 'wxid_' 字样"
        wxid = wx_path.split("wxid_")[-1].split("\\")[0]
        assert wxid, "无法从路径中提取微信 ID (wxid)"
        wxid = "wxid_" + wxid
        try:
            app_config.update({
                "weixin_file_path": wx_path,
                "cache_file_path": cache_path,
                "wx_id": wxid
            })
        except Exception as exc:  # keep simple for UI; can be replaced with toast/dialog later
            print(f"保存路径失败: {exc}")
        else:
            print("路径已保存到 config.json")
    ##########################
    # auto_path_btn
    # TODO 之后实现，设置几个默认的搜索路径，自动检测并填入输入框
    
    @staticmethod
    def _normalize_path_input(raw: str) -> str:
        # Remove surrounding quotes if provided and collapse duplicated backslashes
        text = raw.strip()
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
        # Replace double backslash with single backslash for windows-style paths
        text = text.replace("\\\\", "\\")
        return text
    #########################
    # auto_key_btn
    def _show_key_capture_hint(self) -> None:
        dialog = KeyCaptureDialog(self, self.key_input)
        dialog.exec_()

    def _save_key(self) -> None:
        key_value = self.key_input.text().strip()
        try:
            app_config.set("decryption_key", key_value)
        except Exception as exc:
            print(f"保存密钥失败: {exc}")
        else:
            print("密钥已保存到 config.json")

    def _save_model_settings(self) -> None:
        model_name = self.model_name_input.text().strip()
        model_api = self.model_api_input.text().strip()
        try:
            app_config.update({"model_name": model_name, "api_key": model_api})
        except Exception as exc:
            print(f"保存模型设置失败: {exc}")
        else:
            print("模型名称与 API 已保存到 config.json")

    def _add_field(self, parent_layout: QVBoxLayout, label: str, placeholder: str) -> LineEdit:
        parent_layout.addWidget(BodyLabel(label))
        edit = LineEdit(self)
        edit.setPlaceholderText(placeholder)
        parent_layout.addWidget(edit)
        return edit


class KeyCaptureDialog(QDialog):
    """Dialog that guides user to close WeChat and waits until process exits."""

    def __init__(self, parent=None, key_input: LineEdit | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("自动捕获密钥")
        self._key_input = key_input
        self._timer_check = QTimer(self)
        self._timer_check.setInterval(1500)
        self._timer_check.timeout.connect(self._check_process)

        self._timer_anim = QTimer(self)
        self._timer_anim.setInterval(350)
        self._timer_anim.timeout.connect(self._tick_anim)
        self._dots_state = 0
        self._phase = 1  # 1: waiting close, 2: waiting reopen, 3: waiting key result, 4: done
        self._key_worker = None
        self._build_ui()
        self._timer_check.start()
        self._timer_anim.start()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        line1 = QHBoxLayout()
        line1.setSpacing(12)
        self.label1 = QLabel("第一步：关闭目前微信进程。", self)
        self.indicator1 = QLabel(".", self)
        self.indicator1.setStyleSheet("font-size: 18px;")
        self.indicator1.setFixedWidth(36)
        self.check_label1 = QLabel("✔", self)
        self.check_label1.setStyleSheet("font-size: 18px;")
        self.check_label1.setVisible(False)
        line1.addWidget(self.label1)
        line1.addWidget(self.indicator1)
        line1.addWidget(self.check_label1)
        layout.addLayout(line1)

        line2 = QHBoxLayout()
        line2.setSpacing(12)
        self.label2 = QLabel("第二步：打开微信并保留在登录前的界面。", self)
        self.indicator2 = QLabel("...", self)
        self.indicator2.setStyleSheet("font-size: 18px;")
        self.indicator2.setFixedWidth(36)
        self.label2.setVisible(False)
        self.indicator2.setVisible(False)
        self.check_label2 = QLabel("✔", self)
        self.check_label2.setStyleSheet("font-size: 18px;")
        self.check_label2.setVisible(False)
        line2.addWidget(self.label2)
        line2.addWidget(self.indicator2)
        line2.addWidget(self.check_label2)
        layout.addLayout(line2)

        line3 = QHBoxLayout()
        line3.setSpacing(12)
        self.label3 = QLabel("第三步：请登录微信。", self)
        self.indicator3 = QLabel("...", self)
        self.indicator3.setStyleSheet("font-size: 18px;")
        self.indicator3.setFixedWidth(36)
        self.label3.setVisible(False)
        self.indicator3.setVisible(False)
        self.check_label3 = QLabel("✔", self)
        self.check_label3.setStyleSheet("font-size: 18px;")
        self.check_label3.setVisible(False)
        self.fail_label3 = QLabel("✖", self)
        self.fail_label3.setStyleSheet("font-size: 18px; color: red;")
        self.fail_label3.setVisible(False)
        line3.addWidget(self.label3)
        line3.addWidget(self.indicator3)
        line3.addWidget(self.check_label3)
        line3.addWidget(self.fail_label3)
        layout.addLayout(line3)

        layout.addSpacing(12)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok, self)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _check_process(self) -> None:
        running = self._is_process_running("weixin.exe")
        if self._phase == 1:
            if not running:
                self.check_label1.setVisible(True)
                self.indicator1.setVisible(False)
                # move to phase 2
                self._phase = 2
                self.label2.setVisible(True)
                self.indicator2.setVisible(True)
                self._dots_state = 0
        elif self._phase == 2:
            if running:
                self._timer_check.stop()
                self.indicator2.setVisible(False)
                self.check_label2.setVisible(True)
                self._phase = 3
                self._start_key_capture()
        elif self._phase == 4:
            self._timer_check.stop()

    def _tick_anim(self) -> None:
        self._dots_state = (self._dots_state + 1) % 3
        dots = "." * (self._dots_state + 1)
        if self._phase == 1 and self.indicator1.isVisible():
            self.indicator1.setText(dots)
        elif self._phase == 2 and self.indicator2.isVisible():
            self.indicator2.setText(dots)
        elif self._phase == 3 and self.indicator3.isVisible():
            self.indicator3.setText(dots)

    def _start_key_capture(self) -> None:
        # start async call before showing the third step
        self._dots_state = 0
        self.check_label3.setVisible(False)
        self.fail_label3.setVisible(False)
        self.indicator3.setVisible(True)
        self.label3.setVisible(True)

        self._key_worker = _KeyWorker()
        self._key_worker.result_ready.connect(self._on_key_result)
        self._key_worker.start()

    def _on_key_result(self, key_value: str) -> None:
        self._phase = 4
        self._timer_anim.stop()
        self.indicator3.setVisible(False)
        if isinstance(key_value, str) and key_value:
            self.check_label3.setVisible(True)
            if self._key_input is not None:
                self._key_input.setText(key_value)
        else:
            self.fail_label3.setVisible(True)
        self._key_worker = None
        QTimer.singleShot(3000, self.accept)

    @staticmethod
    def _is_process_running(proc_name: str) -> bool:
        try:
            output = subprocess.check_output(["tasklist"], text=True, errors="ignore", creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            return False
        proc_name = proc_name.lower()
        return any(proc_name in line.lower() for line in output.splitlines())


class _KeyWorker(QThread):
    result_ready = pyqtSignal(object)

    def run(self) -> None:
        result = get_key()
        self.result_ready.emit(result)
