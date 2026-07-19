"""Windows 剪贴板事件监听器。

用 AddClipboardFormatListener 这个 Win32 API 做事件驱动监听，而不是写一个
while True + sleep 的轮询循环——前者是系统在剪贴板变化时主动推送消息给我们，
几乎不占 CPU；后者要么响应慢，要么空转浪费资源。

检测到剪贴板里出现"新的一张图片"时，通过回调函数把 PIL.Image 交给上层处理。
"""
from __future__ import annotations

import ctypes
import hashlib
import logging
from typing import Callable, Optional

import win32api
import win32con
import win32gui
from PIL import Image, ImageGrab

logger = logging.getLogger(__name__)

WM_CLIPBOARDUPDATE = 0x031D


class ClipboardWatcher:
    """监听系统剪贴板，检测到新图片时调用传入的回调函数。"""

    def __init__(self, on_image: Callable[[Image.Image], None]) -> None:
        self._on_image = on_image
        self._hwnd: Optional[int] = None
        self._last_hash: Optional[str] = None

    # ------------------------------------------------------------------
    # 内部实现：一个不可见窗口用来接收 WM_CLIPBOARDUPDATE 消息
    # ------------------------------------------------------------------
    def _wnd_proc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == WM_CLIPBOARDUPDATE:
            self._check_clipboard()
            return 0
        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _create_hidden_window(self) -> int:
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._wnd_proc
        wc.lpszClassName = "QRSnipperClipboardWatcherClass"
        wc.hInstance = win32api.GetModuleHandle(None)
        try:
            class_atom = win32gui.RegisterClass(wc)
        except win32gui.error:
            # 上一次异常退出可能没有注销窗口类，这种情况下直接复用类名即可
            class_atom = wc.lpszClassName
        return win32gui.CreateWindow(
            class_atom,
            "QRSnipperClipboardWatcher",
            0, 0, 0, 0, 0, 0, 0,
            wc.hInstance,
            None,
        )

    def _check_clipboard(self) -> None:
        try:
            content = ImageGrab.grabclipboard()
        except Exception:
            logger.exception("读取剪贴板内容失败")
            return

        # 剪贴板里不是图片（比如是文字、文件列表），跳过。
        # 注意：我们自己往剪贴板写识别结果时写的是文字，所以不会在这里被重复处理，天然避免死循环。
        if not isinstance(content, Image.Image):
            return

        digest = hashlib.md5(content.tobytes()).hexdigest()
        if digest == self._last_hash:
            logger.debug("与上一次处理的图片内容相同，跳过")
            return
        self._last_hash = digest

        logger.debug("检测到剪贴板新图片，尺寸=%s", content.size)
        try:
            self._on_image(content)
        except Exception:
            logger.exception("处理剪贴板图片的回调函数出错")

    # ------------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------------
    def start(self) -> None:
        """启动监听。这个调用会阻塞当前线程，直到 stop() 被调用。"""
        self._hwnd = self._create_hidden_window()
        ok = ctypes.windll.user32.AddClipboardFormatListener(self._hwnd)
        if not ok:
            raise RuntimeError("AddClipboardFormatListener 调用失败")
        logger.info("剪贴板监听已启动，等待新的截图……")
        win32gui.PumpMessages()  # 消息循环，收到 WM_QUIT 才会返回

    def stop(self) -> None:
        """请求停止监听，会让 start() 里阻塞的消息循环退出。"""
        if self._hwnd is None:
            return
        ctypes.windll.user32.RemoveClipboardFormatListener(self._hwnd)
        win32gui.PostMessage(self._hwnd, win32con.WM_CLOSE, 0, 0)
        logger.info("已请求停止剪贴板监听")
