#!/usr/bin/env python3
"""
Digest Times Tracker
====================

last_digest_times.json の管理を担当するモジュール。
finalize_from_shadow.py から分離。
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import DigestConfig, LEVEL_CONFIG, LEVEL_NAMES, extract_file_number


class DigestTimesTracker:
    """last_digest_times.json 管理クラス"""

    def __init__(self, config: DigestConfig):
        self.config = config
        self.last_digest_file = config.plugin_root / ".claude-plugin" / "last_digest_times.json"

    def load(self) -> dict:
        """最終ダイジェスト生成時刻を読み込む（存在しなければテンプレートから初期化）"""
        if self.last_digest_file.exists():
            with open(self.last_digest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # テンプレートから初期化
            template_file = self.config.plugin_root / ".claude-plugin" / "last_digest_times.template.json"
            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                # テンプレートをコピーして保存
                with open(self.last_digest_file, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=2, ensure_ascii=False)
                print(f"[INFO] Initialized last_digest_times.json from template")
                return template
            else:
                # テンプレートがない場合は空の階層的フォーマット
                return {level: {"timestamp": "", "last_processed": None} for level in LEVEL_NAMES}

    def extract_file_numbers(self, level: str, input_files: List[str]) -> List[str]:
        """ファイル名から連番を抽出（プレフィックス付き、ゼロ埋め維持）"""
        if not input_files:
            return []

        # プレフィックス→レベル の逆引きマップ
        prefix_to_level = {cfg["prefix"]: lvl for lvl, cfg in LEVEL_CONFIG.items()}

        numbers = []
        for file in input_files:
            result = extract_file_number(file)
            if result:
                prefix, num = result
                # ゼロ埋めを維持した文字列を生成
                if prefix == "Loop":
                    numbers.append(f"Loop{num:04d}")
                else:
                    # プレフィックスからソースファイルのレベルを特定
                    source_level = prefix_to_level.get(prefix)
                    if source_level:
                        digits = LEVEL_CONFIG[source_level]["digits"]
                    else:
                        digits = 4  # fallback
                    numbers.append(f"{prefix}{num:0{digits}d}")

        return sorted(numbers)

    def save(self, level: str, input_files: List[str] = None):
        """最終ダイジェスト生成時刻と最新処理済みファイル番号を保存"""
        times = self.load()

        # 連番を抽出
        file_numbers = self.extract_file_numbers(level, input_files)

        # 最後の要素のみを保存
        last_file = file_numbers[-1] if file_numbers else None

        # 保存
        times[level] = {
            "timestamp": datetime.now().isoformat(),
            "last_processed": last_file
        }

        with open(self.last_digest_file, 'w', encoding='utf-8') as f:
            json.dump(times, f, indent=2, ensure_ascii=False)

        print(f"[INFO] Updated last_digest_times.json for level: {level}")
        if last_file:
            print(f"[INFO] Last processed: {last_file}")
