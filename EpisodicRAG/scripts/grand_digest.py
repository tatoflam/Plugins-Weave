#!/usr/bin/env python3
"""
GrandDigest Manager
===================

GrandDigest.txt の管理を担当するモジュール。
finalize_from_shadow.py から分離。
"""
import json
from datetime import datetime
from typing import Dict, Any

from config import DigestConfig, LEVEL_NAMES
from utils import log_error


class GrandDigestManager:
    """GrandDigest.txt管理クラス"""

    def __init__(self, config: DigestConfig):
        self.config = config
        self.grand_digest_file = config.essences_path / "GrandDigest.txt"

    def get_template(self) -> dict:
        """GrandDigest.txtのテンプレートを返す（全8レベル対応）"""
        return {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            },
            "major_digests": {
                level: {"overall_digest": None}
                for level in LEVEL_NAMES
            }
        }

    def load_or_create(self) -> dict:
        """GrandDigest.txtを読み込む。存在しなければテンプレートで作成"""
        if self.grand_digest_file.exists():
            with open(self.grand_digest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print("[INFO] GrandDigest.txt not found. Creating new file.")
            template = self.get_template()
            self.save(template)
            return template

    def save(self, data: dict):
        """GrandDigest.txtを保存"""
        with open(self.grand_digest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def update_digest(self, level: str, digest_name: str, overall_digest: dict) -> bool:
        """指定レベルのダイジェストを更新"""
        grand_data = self.load_or_create()

        if level not in grand_data["major_digests"]:
            log_error(f"Unknown level: {level}")
            return False

        # overall_digestを更新（完全なオブジェクトとして保存）
        grand_data["major_digests"][level]["overall_digest"] = overall_digest

        # メタデータを更新
        grand_data["metadata"]["last_updated"] = datetime.now().isoformat()

        # 保存
        self.save(grand_data)
        print(f"[INFO] Updated GrandDigest.txt for level: {level}")
        return True
