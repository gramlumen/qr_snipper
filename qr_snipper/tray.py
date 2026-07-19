"""系统托盘图标。

让程序以"托盘常驻"的形式运行，而不是霸占一个控制台窗口；
右键图标可以退出程序、打开历史记录文件。
图标本身用 PIL 现画一个简单的二维码风格方块，不依赖外部 .ico 文件，方便分发。
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


def _build_icon_image() -> Image.Image:
    size = 64
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    # 画几个方块，示意"二维码"图案，纯装饰用
    blocks = [
        (6, 6, 26, 26), (38, 6, 58, 26),
        (6, 38, 26, 58), (38, 38, 46, 46),
    ]
    for box in blocks:
        draw.rectangle(box, fill="black")
    return img


class TrayIcon:
    """封装 pystray，暴露"启动/退出/打开历史"三个动作。"""

    def __init__(
        self,
        on_quit: Callable[[], None],
        on_open_history: Optional[Callable[[], None]] = None,
    ) -> None:
        self._on_quit = on_quit
        menu_items = []
        if on_open_history is not None:
            menu_items.append(
                pystray.MenuItem("打开识别历史", lambda icon, item: on_open_history())
            )
        menu_items.append(pystray.MenuItem("退出", self._handle_quit))

        self._icon = pystray.Icon(
            name="qr_snipper",
            icon=_build_icon_image(),
            title="QR Snipper 运行中 —— 截图自动识别二维码",
            menu=pystray.Menu(*menu_items),
        )

    def _handle_quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        logger.info("用户从托盘菜单选择退出")
        icon.stop()
        self._on_quit()

    def run_detached(self) -> None:
        """在后台线程运行托盘图标，立即返回，不阻塞调用方。"""
        self._icon.run_detached()
