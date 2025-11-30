#!/usr/bin/env python3
"""
EpisodicRAG Interfaces Layer
============================

エントリーポイント・CLIスクリプト層。
application層に依存。

Scripts:
    - finalize_from_shadow: ShadowからRegularDigestを作成
    - save_provisional_digest: ProvisionalDigestを保存
    - digest_setup: 初期セットアップCLI
    - digest_config: 設定変更CLI
    - digest_auto: 健全性診断CLI

Submodules:
    - provisional: Modular components for provisional digest handling

Usage:
    python -m interfaces.finalize_from_shadow weekly "タイトル"
    python -m interfaces.save_provisional_digest weekly data.json
    python -m interfaces.digest_setup check
    python -m interfaces.digest_config show
    python -m interfaces.digest_auto --output json
"""

from interfaces.digest_auto import DigestAutoAnalyzer
from interfaces.digest_config import ConfigEditor
from interfaces.digest_setup import SetupManager
from interfaces.finalize_from_shadow import DigestFinalizerFromShadow
from interfaces.interface_helpers import get_next_digest_number, sanitize_filename
from interfaces.provisional import (
    DigestMerger,
    InputLoader,
    ProvisionalFileManager,
)
from interfaces.save_provisional_digest import ProvisionalDigestSaver

__all__ = [
    # Main classes
    "DigestFinalizerFromShadow",
    "ProvisionalDigestSaver",
    # New CLI classes
    "SetupManager",
    "ConfigEditor",
    "DigestAutoAnalyzer",
    # Helpers
    "sanitize_filename",
    "get_next_digest_number",
    # Provisional submodule
    "InputLoader",
    "ProvisionalFileManager",
    "DigestMerger",
]
