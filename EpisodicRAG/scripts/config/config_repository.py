#!/usr/bin/env python3
"""
Config Repository
=================

config.json の読み書き
"""
import json
from pathlib import Path
from typing import Dict, Any


def load_config(config_file: Path) -> Dict[str, Any]:
    """
    設定読み込み

    Args:
        config_file: 設定ファイルのパス

    Returns:
        設定辞書

    Raises:
        FileNotFoundError: 設定ファイルが見つからない場合
        json.JSONDecodeError: JSONのパースに失敗した場合
    """
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in config file {config_file}: {e.msg}",
                e.doc, e.pos
            )

    raise FileNotFoundError(
        f"Config file not found: {config_file}\n"
        f"Run setup first: bash scripts/setup.sh"
    )
