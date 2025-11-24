#!/usr/bin/env python3
"""
ShadowGrandDigest Manager
=========================

GrandDigest更新後に作成された新しいコンテンツを保持し、
常に最新の知識にアクセス可能にするシステム

使用方法:
    from shadow_grand_digest import ShadowGrandDigestManager
    from config import DigestConfig

    config = DigestConfig()
    manager = ShadowGrandDigestManager(config)

    # 新しいLoopファイルを検出してShadowを更新
    manager.update_shadow_for_new_loops()

    # Weeklyダイジェスト確定時のカスケード処理
    manager.cascade_update_on_digest_finalize("weekly")
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Plugin版: config.pyをインポート
from config import DigestConfig


class ShadowGrandDigestManager:
    """ShadowGrandDigest管理クラス（config.py統合版）"""

    def __init__(self, config: Optional[DigestConfig] = None):
        # 設定を読み込み
        if config is None:
            config = DigestConfig()
        self.config = config

        # パスを設定から取得
        self.digests_path = config.digests_path
        self.loops_path = config.loops_path
        self.essences_path = config.essences_path

        # ファイルパスを設定
        self.grand_digest_file = self.essences_path / "GrandDigest.txt"
        self.shadow_digest_file = self.essences_path / "ShadowGrandDigest.txt"
        self.last_digest_file = self.config.plugin_root / ".claude-plugin" / "last_digest_times.json"

        # レベル設定
        self.levels = ["weekly", "monthly", "quarterly", "annual", "triennial", "decadal", "multi_decadal", "centurial"]
        self.level_hierarchy = {
            "weekly": {"source": "loops", "next": "monthly"},
            "monthly": {"source": "weekly", "next": "quarterly"},
            "quarterly": {"source": "monthly", "next": "annual"},
            "annual": {"source": "quarterly", "next": "triennial"},
            "triennial": {"source": "annual", "next": "decadal"},
            "decadal": {"source": "triennial", "next": "multi_decadal"},
            "multi_decadal": {"source": "decadal", "next": "centurial"},
            "centurial": {"source": "multi_decadal", "next": None}
        }

        # ダイジェスト設定
        self.digest_config = {
            "weekly": {"dir": "1_Weekly", "prefix": "W"},
            "monthly": {"dir": "2_Monthly", "prefix": "M"},
            "quarterly": {"dir": "3_Quarterly", "prefix": "Q"},
            "annual": {"dir": "4_Annual", "prefix": "A"},
            "triennial": {"dir": "5_Triennial", "prefix": "T"},
            "decadal": {"dir": "6_Decadal", "prefix": "D"},
            "multi_decadal": {"dir": "7_Multi-decadal", "prefix": "MD"},
            "centurial": {"dir": "8_Centurial", "prefix": "C"}
        }

    def get_template(self) -> dict:
        """ShadowGrandDigest.txtのテンプレートを返す"""
        overall_digest_placeholder = {
            "timestamp": "<!-- PLACEHOLDER -->",
            "source_files": [],
            "digest_type": "<!-- PLACEHOLDER -->",
            "keywords": ["<!-- PLACEHOLDER: keyword1 -->", "<!-- PLACEHOLDER: keyword2 -->",
                        "<!-- PLACEHOLDER: keyword3 -->", "<!-- PLACEHOLDER: keyword4 -->",
                        "<!-- PLACEHOLDER: keyword5 -->"],
            "abstract": "<!-- PLACEHOLDER: 全体統合分析 (2400文字程度) -->",
            "impression": "<!-- PLACEHOLDER: 所感・展望 (800文字程度) -->"
        }

        return {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
                "description": "GrandDigest更新後に作成された新しいコンテンツの増分ダイジェスト（下書き帳）"
            },
            "latest_digests": {
                "weekly": {
                    "overall_digest": overall_digest_placeholder.copy()
                },
                "monthly": {
                    "overall_digest": overall_digest_placeholder.copy()
                },
                "quarterly": {
                    "overall_digest": overall_digest_placeholder.copy()
                },
                "annual": {
                    "overall_digest": overall_digest_placeholder.copy()
                },
                "triennial": {
                    "overall_digest": overall_digest_placeholder.copy()
                },
                "decadal": {
                    "overall_digest": overall_digest_placeholder.copy()
                },
                "multi_decadal": {
                    "overall_digest": overall_digest_placeholder.copy()
                },
                "centurial": {
                    "overall_digest": overall_digest_placeholder.copy()
                }
            }
        }

    def load_or_create_shadow(self) -> dict:
        """ShadowGrandDigestを読み込む。存在しなければ作成"""
        if self.shadow_digest_file.exists():
            with open(self.shadow_digest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print("[INFO] ShadowGrandDigest.txt not found. Creating new file.")
            template = self.get_template()
            self.save_shadow(template)
            return template

    def save_shadow(self, data: dict):
        """ShadowGrandDigestを保存"""
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(self.shadow_digest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_last_digest_times(self) -> dict:
        """last_digest_times.jsonを読み込む（存在しなければテンプレートから初期化）"""
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
                return {level: {"timestamp": "", "last_processed": None} for level in self.levels}

    def get_max_file_number(self, level: str) -> Optional[str]:
        """指定レベルの最大ファイル番号を取得"""
        times_data = self.load_last_digest_times()
        level_data = times_data.get(level, {})
        return level_data.get("last_processed")

    def extract_number_from_filename(self, filename: str) -> Optional[int]:
        """ファイル名から数値部分を抽出"""
        # Loop0186 → 186, W0037 → 37, M001 → 1
        match = re.search(r'(Loop|[WMQATD])(\d+)', filename)
        if match:
            return int(match.group(2))
        return None

    def find_new_files(self, level: str) -> List[Path]:
        """GrandDigest更新後に作成された新しいファイルを検出"""
        max_file_number = self.get_max_file_number(level)

        # ソースディレクトリとパターンを決定
        source_info = self.level_hierarchy[level]["source"]
        if source_info == "loops":
            source_dir = self.loops_path
            pattern = "Loop*.txt"
        else:
            config = self.digest_config[source_info]
            source_dir = self.digests_path / config["dir"]
            pattern = f"{config['prefix']}*.txt"

        if not source_dir.exists():
            return []

        # ファイルを検出
        all_files = sorted(source_dir.glob(pattern))

        if max_file_number is None:
            # 初回は全ファイルを検出
            return all_files

        # 最大番号より大きいファイルを抽出
        max_num = self.extract_number_from_filename(max_file_number)
        new_files = []

        for file in all_files:
            file_num = self.extract_number_from_filename(file.name)
            if file_num and file_num > max_num:
                new_files.append(file)

        return new_files

    def _get_source_path(self, level: str) -> Path:
        """
        指定レベルのソースファイルが格納されているディレクトリを返す

        Args:
            level: "weekly", "monthly", "quarterly"など

        Returns:
            Path: ソースファイルのディレクトリ
        """
        source_type = self.level_hierarchy[level]["source"]

        if source_type == "loops":
            # Weekly: Loopファイルを参照
            return self.loops_path
        else:
            # Monthly以上: 下位レベルのDigestファイルを参照
            source_config = self.digest_config.get(source_type)
            if source_config:
                return self.digests_path / source_config["dir"]
            else:
                raise ValueError(f"Unknown source type: {source_type}")

    def add_files_to_shadow(self, level: str, new_files: List[Path]):
        """
        指定レベルのShadowに新しいファイルを追加（増分更新）

        Weekly: source_filesのみ追加（PLACEHOLDERのまま）→ Claude分析待ち
        Monthly以上: Digestファイル内容を読み込んでログ出力（まだらボケ回避）
        """
        shadow_data = self.load_or_create_shadow()
        overall_digest = shadow_data["latest_digests"][level]["overall_digest"]

        # overall_digestがnullの場合、初期化
        if overall_digest is None:
            overall_digest = {
                "timestamp": "<!-- PLACEHOLDER -->",
                "source_files": [],
                "digest_type": "<!-- PLACEHOLDER -->",
                "keywords": [
                    "<!-- PLACEHOLDER: keyword1 -->",
                    "<!-- PLACEHOLDER: keyword2 -->",
                    "<!-- PLACEHOLDER: keyword3 -->",
                    "<!-- PLACEHOLDER: keyword4 -->",
                    "<!-- PLACEHOLDER: keyword5 -->"
                ],
                "abstract": "<!-- PLACEHOLDER: 全体統合分析 (2400文字程度) -->",
                "impression": "<!-- PLACEHOLDER: 所感・展望 (800文字程度) -->"
            }
            shadow_data["latest_digests"][level]["overall_digest"] = overall_digest

        # source_filesがoverall_digest内に存在しない場合、初期化
        if "source_files" not in overall_digest:
            overall_digest["source_files"] = []

        # 既存のファイルリストを取得
        existing_files = set(overall_digest["source_files"])

        # レベルに応じたソースタイプを取得
        source_type = self.level_hierarchy[level]["source"]

        # 新しいファイルだけをsource_filesに追加
        added_count = 0
        for file_path in new_files:
            if file_path.name not in existing_files:
                overall_digest["source_files"].append(file_path.name)
                added_count += 1
                print(f"  + {file_path.name}")

                # Monthly以上: Digestファイルの内容を読み込んでログ出力（まだらボケ回避）
                if source_type != "loops":
                    source_dir = self._get_source_path(level)
                    full_path = source_dir / file_path.name

                    if full_path.exists() and full_path.suffix == '.txt':
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                digest_data = json.load(f)
                                overall = digest_data.get("overall_digest", {})

                                # ログ出力: Digestファイルから読み込んだ情報
                                print(f"    [INFO] Read digest content from {file_path.name}")
                                print(f"      - digest_type: {overall.get('digest_type', 'N/A')}")
                                print(f"      - keywords: {len(overall.get('keywords', []))} items")
                                print(f"      - abstract: {len(overall.get('abstract', ''))} chars")
                                print(f"      - impression: {len(overall.get('impression', ''))} chars")
                        except json.JSONDecodeError:
                            print(f"    [WARN] Failed to parse {file_path.name} as JSON")
                        except Exception as e:
                            print(f"    [WARN] Error reading {file_path.name}: {e}")

        # 既存分析がPLACEHOLDERかどうか確認
        total_files = len(overall_digest["source_files"])
        is_placeholder = (
            isinstance(overall_digest.get("abstract", ""), str) and
            "<!-- PLACEHOLDER" in overall_digest.get("abstract", "")
        )

        if is_placeholder:
            # PLACEHOLDERの場合のみ更新
            overall_digest["abstract"] = f"<!-- PLACEHOLDER: {total_files}ファイル分の全体統合分析 (2400文字程度) -->"
            overall_digest["impression"] = "<!-- PLACEHOLDER: 所感・展望 (800文字程度) -->"
            overall_digest["keywords"] = [
                "<!-- PLACEHOLDER: keyword1 -->",
                "<!-- PLACEHOLDER: keyword2 -->",
                "<!-- PLACEHOLDER: keyword3 -->",
                "<!-- PLACEHOLDER: keyword4 -->",
                "<!-- PLACEHOLDER: keyword5 -->"
            ]
            print(f"[INFO] Initialized placeholder for {total_files} file(s)")
        else:
            # 既存の分析を保持
            print(f"[INFO] Preserved existing analysis (now {total_files} file(s) total)")
            print(f"[INFO] Claude should re-analyze all {total_files} files to integrate new content")

        self.save_shadow(shadow_data)
        print(f"[INFO] Added {added_count} file(s) to ShadowGrandDigest.{level}")
        print(f"[INFO] Total files in shadow: {total_files}")

    def clear_shadow_level(self, level: str):
        """指定レベルのShadowを初期化"""
        shadow_data = self.load_or_create_shadow()

        # overall_digestを空のプレースホルダーにリセット
        shadow_data["latest_digests"][level]["overall_digest"] = {
            "timestamp": "<!-- PLACEHOLDER -->",
            "source_files": [],
            "digest_type": "<!-- PLACEHOLDER -->",
            "keywords": ["<!-- PLACEHOLDER: keyword1 -->", "<!-- PLACEHOLDER: keyword2 -->",
                        "<!-- PLACEHOLDER: keyword3 -->", "<!-- PLACEHOLDER: keyword4 -->",
                        "<!-- PLACEHOLDER: keyword5 -->"],
            "abstract": "<!-- PLACEHOLDER: 全体統合分析 (2400文字程度) -->",
            "impression": "<!-- PLACEHOLDER: 所感・展望 (800文字程度) -->"
        }

        self.save_shadow(shadow_data)
        print(f"[INFO] Cleared ShadowGrandDigest for level: {level}")

    def get_shadow_digest_for_level(self, level: str) -> Optional[Dict[str, Any]]:
        """
        指定レベルのShadowダイジェストを取得

        finalize_from_shadow.pyで使用: これがRegularDigestの内容になります
        """
        shadow_data = self.load_or_create_shadow()
        overall_digest = shadow_data["latest_digests"][level]["overall_digest"]

        if not overall_digest or not overall_digest.get("source_files"):
            print(f"[INFO] No shadow digest for level: {level}")
            return None

        return overall_digest

    def promote_shadow_to_grand(self, level: str):
        """
        ShadowのレベルをGrandDigestに昇格

        注意: この機能は実際にはfinalize_from_shadow.pyの処理2で
        GrandDigestManagerが実行します。ここでは確認のみ。
        """
        digest = self.get_shadow_digest_for_level(level)

        if not digest:
            print(f"[INFO] No shadow digest to promote for level: {level}")
            return

        file_count = len(digest.get("source_files", []))
        print(f"[INFO] Shadow digest ready for promotion: {file_count} file(s)")
        # 実際の昇格処理はfinalize_from_shadow.pyで実行される

    def update_shadow_for_new_loops(self):
        """新しいLoopファイルを検出してShadowを増分更新"""
        # Shadowファイルを読み込み（存在しなければ作成）
        shadow_data = self.load_or_create_shadow()

        new_files = self.find_new_files("weekly")

        if not new_files:
            print("[INFO] No new Loop files found")
            return

        print(f"[INFO] Found {len(new_files)} new Loop file(s):")

        # Shadowに増分追加
        self.add_files_to_shadow("weekly", new_files)

    def cascade_update_on_digest_finalize(self, level: str):
        """
        ダイジェスト確定時のカスケード処理（処理3）

        処理内容:
        1. 現在のレベルのShadow → Grand に昇格（確認のみ、実際は処理2で完了）
        2. 次のレベルの新しいファイルを検出
        3. 次のレベルのShadowに増分追加
        4. 現在のレベルのShadowをクリア
        """
        print(f"\n[処理3] ShadowGrandDigest cascade for level: {level}")

        # 1. Shadow → Grand 昇格の確認
        self.promote_shadow_to_grand(level)

        # 2. 次のレベルの新しいファイルを検出
        next_level = self.level_hierarchy[level]["next"]
        if next_level:
            new_files = self.find_new_files(next_level)

            if new_files:
                print(f"[INFO] Found {len(new_files)} new file(s) for {next_level}:")

                # 3. 次のレベルのShadowに増分追加
                self.add_files_to_shadow(next_level, new_files)
        else:
            print(f"[INFO] No next level for {level} (top level)")

        # 4. 現在のレベルのShadowをクリア
        self.clear_shadow_level(level)

        print(f"[処理3] Cascade completed for level: {level}")


def main():
    """新しいLoopファイルを検出してShadowGrandDigest.weeklyに増分追加"""
    from pathlib import Path

    config = DigestConfig()
    manager = ShadowGrandDigestManager(config)

    print("="*60)
    print("ShadowGrandDigest Update - New Loop Detection")
    print("="*60)

    # 新しいLoopファイルの検出と追加
    manager.update_shadow_for_new_loops()

    print("\n" + "="*60)
    print("Placeholder added to ShadowGrandDigest.weekly")
    print("="*60)
    print("")
    print("[!] WARNING: Claude analysis required immediately!")
    print("Without analysis, memory fragmentation (madaraboke) occurs.")
    print("="*60)


if __name__ == "__main__":
    main()
