"""二维码解码后端。

采用策略模式：QRDecoder 是抽象接口，PyzbarDecoder / OpenCVDecoder 是具体实现。
新增一种解码库时，只需要新写一个子类并在 DECODER_REGISTRY 里注册一行，
不需要改动 app.py 里的调用逻辑。
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List

from PIL import Image

logger = logging.getLogger(__name__)


class QRDecoder(ABC):
    """二维码解码器接口。"""

    @abstractmethod
    def decode(self, image: Image.Image) -> List[str]:
        """从图片中解析出所有二维码内容，找不到则返回空列表。"""
        raise NotImplementedError


class PyzbarDecoder(QRDecoder):
    """基于 pyzbar（zbar）的解码实现，准确率较高，推荐作为首选。"""

    def __init__(self) -> None:
        from pyzbar.pyzbar import decode as pyzbar_decode  # 延迟导入，未安装时不影响其他后端

        self._decode_fn = pyzbar_decode

    def decode(self, image: Image.Image) -> List[str]:
        symbols = self._decode_fn(image)
        results = [
            s.data.decode("utf-8", errors="replace")
            for s in symbols
            if s.type == "QRCODE"
        ]
        return results


class OpenCVDecoder(QRDecoder):
    """基于 OpenCV 自带 QRCodeDetector 的解码实现，作为无 pyzbar 时的备用方案。"""

    def __init__(self) -> None:
        import cv2
        import numpy as np

        self._cv2 = cv2
        self._np = np
        self._detector = cv2.QRCodeDetector()

    def decode(self, image: Image.Image) -> List[str]:
        rgb_array = self._np.array(image.convert("RGB"))
        bgr_array = rgb_array[:, :, ::-1]  # PIL 是 RGB，OpenCV 要 BGR
        try:
            ok, decoded_info, _points, _straight = self._detector.detectAndDecodeMulti(bgr_array)
        except self._cv2.error:
            logger.exception("OpenCV 解码过程出错")
            return []
        if not ok:
            return []
        return [text for text in decoded_info if text]


class AutoDecoder(QRDecoder):
    """按优先级依次尝试可用的解码后端，前一个识别不到结果时自动尝试下一个。"""

    _BACKEND_CLASSES = (PyzbarDecoder, OpenCVDecoder)

    def __init__(self) -> None:
        self._backends: List[QRDecoder] = []
        for backend_cls in self._BACKEND_CLASSES:
            try:
                self._backends.append(backend_cls())
            except ImportError:
                logger.warning("未安装 %s 所需的依赖，已跳过该解码后端", backend_cls.__name__)
        if not self._backends:
            raise RuntimeError(
                "没有可用的二维码解码后端，请安装 pyzbar 或 opencv-python 其中之一"
            )

    def decode(self, image: Image.Image) -> List[str]:
        for backend in self._backends:
            try:
                results = backend.decode(image)
            except Exception:
                logger.exception("%s 解码时抛出异常，尝试下一个后端", backend.__class__.__name__)
                continue
            if results:
                return results
        return []


DECODER_REGISTRY = {
    "auto": AutoDecoder,
    "pyzbar": PyzbarDecoder,
    "opencv": OpenCVDecoder,
}


def get_decoder(backend_name: str) -> QRDecoder:
    """按名称构造解码器，名称来自配置文件的 decoder_backend 字段。"""
    key = backend_name.lower()
    decoder_cls = DECODER_REGISTRY.get(key)
    if decoder_cls is None:
        raise ValueError(
            f"未知的 decoder_backend: {backend_name!r}，"
            f"可选值：{', '.join(DECODER_REGISTRY)}"
        )
    return decoder_cls()
