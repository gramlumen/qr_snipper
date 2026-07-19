"""QR Snipper —— Win+Shift+S 截图后自动识别二维码。

用法：
    python main.py

运行后会在系统托盘出现一个图标（程序在后台常驻）。之后正常使用 Win+Shift+S
截图，只要截图区域里包含二维码，程序会自动识别，并按 config.json 里的配置
弹通知 / 复制结果到剪贴板 / 自动打开链接 / 写入历史记录。

退出方式：右键托盘图标 -> 退出，或者在运行的控制台窗口按 Ctrl+C。
"""
from __future__ import annotations

import logging
import sys

from qr_snipper.app import QRSnipperApp
from qr_snipper.config import load_config
from qr_snipper.tray import TrayIcon


def main() -> None:
    config = load_config("config.json")

    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("qr_snipper.main")

    try:
        app = QRSnipperApp(config)
    except Exception:
        logger.exception("初始化失败，请检查 requirements.txt 里的依赖是否已安装完整")
        sys.exit(1)

    tray = TrayIcon(on_quit=app.stop, on_open_history=app.open_history)
    tray.run_detached()

    try:
        app.run()  # 阻塞在这里，直到托盘"退出"或 Ctrl+C
    except KeyboardInterrupt:
        app.stop()
    finally:
        logger.info("QR Snipper 已退出")


if __name__ == "__main__":
    main()
