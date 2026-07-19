"""应用编排层。

这一层不实现具体的解码算法、通知方式，只负责把各个模块串接起来：
剪贴板出现新图 -> 交给解码器 -> 有结果就依次执行配置里启用的动作。

这样划分的好处：以后要加新功能（比如加一种解码库、加一种动作），
只需要改 decoders.py / actions.py，app.py 不用动。
"""
from __future__ import annotations

import logging
import os
from typing import List

from PIL import Image

from .actions import ACTION_FACTORIES, QRAction
from .clipboard_watcher import ClipboardWatcher
from .config import AppConfig
from .decoders import QRDecoder, get_decoder

logger = logging.getLogger(__name__)


class QRSnipperApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.decoder: QRDecoder = get_decoder(config.decoder_backend)
        self.actions: List[QRAction] = self._build_actions(config)
        self.watcher = ClipboardWatcher(on_image=self._on_new_image)

    @staticmethod
    def _build_actions(config: AppConfig) -> List[QRAction]:
        actions: List[QRAction] = []
        for name in config.actions:
            factory = ACTION_FACTORIES.get(name)
            if factory is None:
                logger.warning("配置中 %r，已忽略", name)
                continue
            action = factory(config)
            if action is not None:
                actions.append(action)
        logger.info("已启用动作：%s", [a.__class__.__name__ for a in actions])
        return actions

    def _on_new_image(self, image: Image.Image) -> None:
        try:
            results = self.decoder.decode(image)
        except Exception:
            logger.exception("二维码解码过程出错")
            return

        if not results:
            logger.debug("本次截图未识别到二维码")
            return

        logger.info("识别到 %d 个二维码：%s", len(results), results)
        for action in self.actions:
            try:
                action.execute(results, image)
            except Exception:
                logger.exception("执行动作 %s 时出错", action.__class__.__name__)

    def open_history(self) -> None:
        """供托盘菜单调用：打开历史记录文件（用系统默认程序）。"""
        path = self.config.history_file
        if not os.path.exists(path):
            open(path, "a", encoding="utf-8").close()
        os.startfile(path)  # noqa: Windows 专用 API，本项目只面向 Windows

    def run(self) -> None:
        """启动主循环，会阻塞直到 stop() 被调用。"""
        logger.info("QR Snipper 启动，等待剪切板……")
        self.watcher.start()

    def stop(self) -> None:
        self.watcher.stop()
