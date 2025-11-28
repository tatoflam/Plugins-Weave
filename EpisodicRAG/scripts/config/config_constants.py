#!/usr/bin/env python3
"""
Config Constants
================

設定関連の共通定数を定義。
REQUIRED_CONFIG_KEYSなど、複数のモジュールで使用される定数を一元管理。

Usage:
    from config.config_constants import REQUIRED_CONFIG_KEYS
"""

from typing import List

# =============================================================================
# 必須設定キー
# =============================================================================

# 設定ファイルに必須のキー
REQUIRED_CONFIG_KEYS: List[str] = ["loops_path", "digests_path", "essences_path"]

# =============================================================================
# 閾値キー
# =============================================================================

# 各レベルの閾値キー（設定ファイルで使用）
THRESHOLD_KEYS: List[str] = [
    "weekly_threshold",
    "monthly_threshold",
    "quarterly_threshold",
    "annual_threshold",
    "triennial_threshold",
    "decadal_threshold",
    "multi_decadal_threshold",
    "centurial_threshold",
]
