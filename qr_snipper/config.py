"""配置的数据结构与加载逻辑。

配置以 JSON 文件描述，缺失字段会使用默认值兜底，未知字段会被忽略（而不是报错），
这样以后给配置文件加新字段、或者用户的配置文件里有旧字段时都不会互相破坏。
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, fields, replace
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    # 二维码解码后端：auto（自动挑选可用的库）/ pyzbar / opencv
    decoder_backend: str = "auto"

    # 识别成功后依次执行的动作名称，对应 actions.py 里 ACTION_REGISTRY 的 key
    actions: List[str] = field(
        default_factory=lambda: ["notify", "copy", "open_url", "history"]
    )

    # 系统通知显示时长（秒）
    notify_duration: int = 5

    # 识别结果里若包含 http/https 链接，是否自动用默认浏览器打开
    auto_open_url: bool = True

    # 识别历史记录写入的文件（JSON Lines 格式，每行一条记录）
    history_file: str = "qr_history.jsonl"

    # 日志级别：DEBUG / INFO / WARNING / ERROR
    log_level: str = "INFO"


def load_config(path: str = "config.json") -> AppConfig:
    """从 JSON 文件加载配置；文件不存在则直接返回默认配置。"""
    defaults = AppConfig()

    if not os.path.exists(path):
        logger.info("未找到配置文件 %s，使用默认配置", path)
        return defaults

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        logger.exception("配置文件 %s 解析失败，使用默认配置", path)
        return defaults

    valid_keys = {f.name for f in fields(AppConfig)}
    unknown = set(raw) - valid_keys
    if unknown:
        logger.warning("配置文件中存在未知字段，已忽略：%s", unknown)

    filtered = {k: v for k, v in raw.items() if k in valid_keys}
    return replace(defaults, **filtered)
