#!/usr/bin/env python3
"""
Utility Functions
=================

共通ユーティリティ関数を提供するモジュール。
finalize_from_shadow.py から分離。
"""
import re
import sys
from typing import Optional


# =============================================================================
# ロギング関数（統一エラーハンドリング）
# =============================================================================

def log_error(message: str, exit_code: Optional[int] = None) -> None:
    """
    エラーメッセージをstderrに出力

    Args:
        message: エラーメッセージ
        exit_code: 指定時はこのコードでプログラムを終了
    """
    print(f"[ERROR] {message}", file=sys.stderr)
    if exit_code is not None:
        sys.exit(exit_code)


def log_warning(message: str) -> None:
    """
    警告メッセージをstderrに出力

    Args:
        message: 警告メッセージ
    """
    print(f"[WARNING] {message}", file=sys.stderr)


def log_info(message: str) -> None:
    """
    情報メッセージをstdoutに出力

    Args:
        message: 情報メッセージ
    """
    print(f"[INFO] {message}")


# =============================================================================
# ファイル名処理
# =============================================================================


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """
    ファイル名として安全な文字列に変換

    Args:
        title: 元のタイトル文字列
        max_length: 最大文字数（デフォルト: 50）

    Returns:
        ファイル名として安全な文字列
    """
    # 危険な文字を削除
    sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
    # 空白をアンダースコアに変換
    sanitized = re.sub(r'\s+', '_', sanitized)
    # 先頭・末尾のアンダースコアを削除
    sanitized = sanitized.strip('_')
    # 長さ制限
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')
    return sanitized
