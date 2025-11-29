#!/usr/bin/env python3
"""
Config層専用の例外
==================

Config層をDomain層から独立させるための例外クラス。
シンプルな例外として実装し、DiagnosticContextは持たない。

## ⚠️ なぜ domain.exceptions.ConfigError を使わないのか

Config層は `digest-config` スキルの本体であり、Claudeプラグインとして
**単独でロード可能**である必要があります。

Domain層への依存があると:
1. プラグイン初期化時にDomain層全体がロードされる
2. Circular Import の問題が発生する可能性がある
3. Config層の変更がDomain層に影響する

このため、Config層は独自の例外クラスを持ちます。

Usage:
    from config.exceptions import ConfigError

    raise ConfigError("Invalid config.json format")
"""


class ConfigError(Exception):
    """
    設定関連エラー

    Config層専用の例外クラス。Domain層の例外とは**完全に独立**。

    Examples:
        - config.json が見つからない
        - config.json のフォーマットが不正
        - 必須の設定キーが存在しない
        - 無効なレベルが指定された

    Warning:
        Domain層のEpisodicRAGErrorを継承しないため、
        `except EpisodicRAGError` ではキャッチされません。
        これはConfig層の独立性を保つための**意図的な設計**です。

        Config層のエラーをキャッチする場合は:
            from config.exceptions import ConfigError
            except ConfigError:
                ...
    """

    def __init__(self, message: str) -> None:
        """
        初期化

        Args:
            message: エラーメッセージ
        """
        super().__init__(message)
