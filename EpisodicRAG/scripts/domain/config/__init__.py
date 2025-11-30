#!/usr/bin/env python3
"""
Domain Config パッケージ
========================

設定関連のドメイン知識を提供。
バリデーションルールと設定キー定数を含む。

Usage:
    from domain.config import REQUIRED_CONFIG_KEYS, THRESHOLD_KEYS
    from domain.config import collect_type_error
"""

from domain.config.config_constants import REQUIRED_CONFIG_KEYS, THRESHOLD_KEYS
from domain.config.validation import collect_type_error

__all__ = [
    "REQUIRED_CONFIG_KEYS",
    "THRESHOLD_KEYS",
    "collect_type_error",
]
