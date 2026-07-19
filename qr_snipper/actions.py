"""识别到二维码后要执行的动作。

采用插件式注册：QRAction 是抽象接口，具体动作各自成一个类。
新增一种动作（比如"发到微信""写入数据库"）时，只需要新写一个子类，
并在 app.py 的 ACTION_REGISTRY 里加一行映射，不需要改动主流程代码。
"""
from __future__ import annotations

import json
import logging
import time
import webbrowser
from abc import ABC, abstractmethod
from typing import List
from urllib.parse import urlparse

from PIL import Image

logger = logging.getLogger(__name__)


class QRAction(ABC):
    """识别到二维码后触发的动作接口。"""

    @abstractmethod
    def execute(self, results: List[str], image: Image.Image) -> None:
        """results 是本次识别到的所有二维码内容，image 是原始截图。"""
        raise NotImplementedError


class CopyToClipboardAction(QRAction):
    """把识别结果写回剪贴板，方便用户直接 Ctrl+V 粘贴使用。"""

    def execute(self, results: List[str], image: Image.Image) -> None:
        import win32clipboard

        text = "\n".join(results)
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        finally:
            win32clipboard.CloseClipboard()
        logger.info("识别结果已复制到剪贴板")


class ToastNotifyAction(QRAction):
    """弹出 Windows 系统通知，显示识别到的内容。"""

    def __init__(self, duration: int = 5) -> None:
        self._duration = duration

    def execute(self, results: List[str], image: Image.Image) -> None:
        from win10toast import ToastNotifier

        toaster = ToastNotifier()
        preview = results[0] if len(results) == 1 else f"共 {len(results)} 个二维码：{results[0]}"
        if len(preview) > 200:
            preview = preview[:200] + "…"
        toaster.show_toast(
            "识别到二维码",
            preview,
            duration=self._duration,
            threaded=True,
        )

class WinNotifyAction(QRAction):
    """弹出 Windows 系统通知，显示识别到的内容。"""

    def __init__(self, duration: int = 5) -> None:
        self._duration = duration

    @staticmethod
    def _is_url(text: str) -> bool:
        """判断文本是否为合法的 HTTP/HTTPS 链接"""
        try:
            result = urlparse(text.strip())
            return all([result.scheme in ("http", "https"), result.netloc])
        except ValueError:
            return False

    def execute(self, results: List[str], image: Image.Image) -> None:
        from winotify import Notification,audio

        if not results:
            return

        preview = results[0] if len(results) == 1 else f"共 {len(results)} 个二维码：{results[0]}"
        if len(preview) > 200:
            preview = preview[:200] + "…"

        # winotify 调用的是 Win10/11 原生接口，不需要 threaded 参数，不会阻塞程序
        toast = Notification(
            app_id="QR Snipper",
            title="识别到二维码",
            msg=preview,
            duration="short" if self._duration <= 5 else "long"
        )

        # 系统提示音
        # toast.set_audio(audio.Default, loop=False)
        url_count = 0
        for i, text in enumerate(results):
            clean_text = text.strip()
            if self._is_url(clean_text):
                url_count += 1
                btn_label = "打开链接" if len(results) == 1 else f"打开链接 ({url_count})"

                toast.add_actions(
                    label=btn_label,
                    launch=clean_text  # 点击后 Windows 会调用默认浏览器打开此 URL
                )

                if url_count >= 3:
                    break
        toast.show()


class OpenURLAction(QRAction):
    """如果识别结果里包含 http/https 链接，自动用默认浏览器打开第一个。"""

    def execute(self, results: List[str], image: Image.Image) -> None:
        for text in results:
            if text.startswith("http://") or text.startswith("https://"):
                webbrowser.open(text)
                logger.info("已自动打开链接：%s", text)
                return


class HistoryLogAction(QRAction):
    """把每次识别结果追加写入本地历史文件（JSON Lines），便于日后查阅。"""

    def __init__(self, path: str) -> None:
        self._path = path

    def execute(self, results: List[str], image: Image.Image) -> None:
        entry = {
            "timestamp": time.time(),
            "readable_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": results,
        }
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# 名称 -> 构造函数（接收 AppConfig，返回 QRAction 实例，或返回 None 表示不启用）
# 之所以用工厂函数而不是直接映射到类，是因为有些动作的构造需要读取配置项（比如通知时长）。
ACTION_FACTORIES = {
    "copy": lambda cfg: CopyToClipboardAction(),
    # "notify": lambda cfg: ToastNotifyAction(cfg.notify_duration),
    "notify": lambda cfg: WinNotifyAction(cfg.notify_duration),
    # "open_url": lambda cfg: OpenURLAction() if cfg.auto_open_url else None,
    "history": lambda cfg: HistoryLogAction(cfg.history_file),
}
