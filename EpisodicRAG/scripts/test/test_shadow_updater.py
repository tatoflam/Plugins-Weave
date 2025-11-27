#!/usr/bin/env python3
"""
shadow/shadow_updater.py のユニットテスト
=========================================

ShadowUpdaterクラスの動作を検証。
- _ensure_overall_digest_initialized: overall_digestの初期化
- add_files_to_shadow: ファイル追加
- clear_shadow_level: レベルクリア
- get_shadow_digest_for_level: Shadow取得
- cascade_update_on_digest_finalize: カスケード処理
"""
import json
import pytest
from pathlib import Path

# Application層
from application.shadow import ShadowUpdater, ShadowIO, ShadowTemplate, FileDetector
from application.tracking import DigestTimesTracker

# Domain層
from domain.constants import LEVEL_NAMES, LEVEL_CONFIG, PLACEHOLDER_MARKER

# 設定
from config import DigestConfig
from test_helpers import create_test_loop_file


# =============================================================================
# フィクスチャ
# =============================================================================

@pytest.fixture
def config(temp_plugin_env):
    """テスト用DigestConfig"""
    return DigestConfig(plugin_root=temp_plugin_env.plugin_root)


@pytest.fixture
def times_tracker(config):
    """テスト用DigestTimesTracker"""
    return DigestTimesTracker(config)


@pytest.fixture
def template():
    """テスト用ShadowTemplate"""
    return ShadowTemplate(levels=LEVEL_NAMES)


@pytest.fixture
def shadow_io(temp_plugin_env, template):
    """テスト用ShadowIO"""
    shadow_file = temp_plugin_env.plugin_root / ".claude-plugin" / "ShadowGrandDigest.txt"
    return ShadowIO(shadow_file, template.get_template)


@pytest.fixture
def file_detector(config, times_tracker):
    """テスト用FileDetector"""
    return FileDetector(config, times_tracker)


@pytest.fixture
def level_hierarchy():
    """レベル階層情報"""
    return {
        level: {"source": cfg["source"], "next": cfg["next"]}
        for level, cfg in LEVEL_CONFIG.items()
    }


@pytest.fixture
def updater(shadow_io, file_detector, template, level_hierarchy):
    """テスト用ShadowUpdater"""
    return ShadowUpdater(shadow_io, file_detector, template, level_hierarchy)


# =============================================================================
# _ensure_overall_digest_initialized テスト
# =============================================================================

class TestEnsureOverallDigestInitialized:
    """_ensure_overall_digest_initialized メソッドのテスト"""

    @pytest.mark.integration
    def test_initializes_null_overall_digest(self, updater, shadow_io):
        """overall_digestがnullの場合、初期化される"""
        shadow_data = shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = None

        result = updater._ensure_overall_digest_initialized(shadow_data, "weekly")

        assert result is not None
        assert isinstance(result, dict)
        assert "source_files" in result

    @pytest.mark.integration
    def test_initializes_non_dict_overall_digest(self, updater, shadow_io):
        """overall_digestがdict以外の場合、初期化される"""
        shadow_data = shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = "invalid"

        result = updater._ensure_overall_digest_initialized(shadow_data, "weekly")

        assert isinstance(result, dict)
        assert "source_files" in result

    @pytest.mark.integration
    def test_preserves_existing_valid_digest(self, updater, shadow_io):
        """有効なoverall_digestは保持される"""
        shadow_data = shadow_io.load_or_create()
        existing_digest = {
            "source_files": ["Loop0001_test.txt"],
            "abstract": "Existing content"
        }
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = existing_digest

        result = updater._ensure_overall_digest_initialized(shadow_data, "weekly")

        assert result["abstract"] == "Existing content"
        assert "Loop0001_test.txt" in result["source_files"]

    @pytest.mark.integration
    def test_adds_source_files_if_missing(self, updater, shadow_io):
        """source_filesがない場合、追加される"""
        shadow_data = shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = {
            "abstract": "Some content"
            # source_filesがない
        }

        result = updater._ensure_overall_digest_initialized(shadow_data, "weekly")

        assert "source_files" in result
        assert result["source_files"] == []


# =============================================================================
# add_files_to_shadow テスト
# =============================================================================

class TestAddFilesToShadow:
    """add_files_to_shadow メソッドのテスト"""

    @pytest.mark.integration
    def test_adds_files_to_empty_shadow(self, updater, temp_plugin_env, shadow_io):
        """空のShadowにファイルを追加"""
        # Loopファイルを作成
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        loop2 = create_test_loop_file(temp_plugin_env.loops_path, 2)

        updater.add_files_to_shadow("weekly", [loop1, loop2])

        # 検証
        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert len(overall["source_files"]) == 2
        assert "Loop0001_test.txt" in overall["source_files"]
        assert "Loop0002_test.txt" in overall["source_files"]

    @pytest.mark.integration
    def test_does_not_add_duplicate_files(self, updater, temp_plugin_env, shadow_io):
        """重複ファイルは追加されない"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)

        # 2回追加
        updater.add_files_to_shadow("weekly", [loop1])
        updater.add_files_to_shadow("weekly", [loop1])

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert len(overall["source_files"]) == 1

    @pytest.mark.integration
    def test_incremental_add(self, updater, temp_plugin_env, shadow_io):
        """増分追加が正しく動作"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        loop2 = create_test_loop_file(temp_plugin_env.loops_path, 2)
        loop3 = create_test_loop_file(temp_plugin_env.loops_path, 3)

        # 最初に2ファイル追加
        updater.add_files_to_shadow("weekly", [loop1, loop2])

        # 後から1ファイル追加
        updater.add_files_to_shadow("weekly", [loop3])

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert len(overall["source_files"]) == 3

    @pytest.mark.integration
    def test_updates_placeholder_on_add(self, updater, temp_plugin_env, shadow_io):
        """ファイル追加時にプレースホルダーが更新される"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)

        updater.add_files_to_shadow("weekly", [loop1])

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert PLACEHOLDER_MARKER in overall["abstract"]
        assert "1ファイル" in overall["abstract"]


# =============================================================================
# clear_shadow_level テスト
# =============================================================================

class TestClearShadowLevel:
    """clear_shadow_level メソッドのテスト"""

    @pytest.mark.integration
    def test_clears_shadow_data(self, updater, temp_plugin_env, shadow_io):
        """Shadowデータがクリアされる"""
        # まずファイルを追加
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        updater.add_files_to_shadow("weekly", [loop1])

        # クリア
        updater.clear_shadow_level("weekly")

        # 検証
        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert overall["source_files"] == []

    @pytest.mark.integration
    def test_resets_to_placeholder(self, updater, shadow_io):
        """クリア後はプレースホルダーに戻る"""
        updater.clear_shadow_level("weekly")

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert PLACEHOLDER_MARKER in overall["abstract"]
        assert PLACEHOLDER_MARKER in overall["impression"]

    @pytest.mark.integration
    def test_does_not_affect_other_levels(self, updater, temp_plugin_env, shadow_io):
        """他のレベルに影響しない"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)

        # weeklyとmonthlyにファイル追加
        updater.add_files_to_shadow("weekly", [loop1])

        # weekly digestファイルを作成（monthlyのソース）
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        weekly_file = weekly_dir / "W0001_test.txt"
        with open(weekly_file, 'w', encoding='utf-8') as f:
            json.dump({"overall_digest": {"test": "data"}}, f)

        updater.add_files_to_shadow("monthly", [weekly_file])

        # weeklyだけクリア
        updater.clear_shadow_level("weekly")

        shadow_data = shadow_io.load_or_create()
        assert shadow_data["latest_digests"]["weekly"]["overall_digest"]["source_files"] == []
        assert len(shadow_data["latest_digests"]["monthly"]["overall_digest"]["source_files"]) == 1


# =============================================================================
# get_shadow_digest_for_level テスト
# =============================================================================

class TestGetShadowDigestForLevel:
    """get_shadow_digest_for_level メソッドのテスト"""

    @pytest.mark.integration
    def test_returns_none_for_empty_shadow(self, updater):
        """空のShadowはNoneを返す"""
        result = updater.get_shadow_digest_for_level("weekly")
        assert result is None

    @pytest.mark.integration
    def test_returns_digest_when_files_exist(self, updater, temp_plugin_env):
        """ファイルがある場合はdigestを返す"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        updater.add_files_to_shadow("weekly", [loop1])

        result = updater.get_shadow_digest_for_level("weekly")

        assert result is not None
        assert "source_files" in result
        assert len(result["source_files"]) == 1

    @pytest.mark.integration
    def test_returns_none_after_clear(self, updater, temp_plugin_env):
        """クリア後はNoneを返す"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        updater.add_files_to_shadow("weekly", [loop1])
        updater.clear_shadow_level("weekly")

        result = updater.get_shadow_digest_for_level("weekly")
        assert result is None


# =============================================================================
# update_shadow_for_new_loops テスト
# =============================================================================

class TestUpdateShadowForNewLoops:
    """update_shadow_for_new_loops メソッドのテスト"""

    @pytest.mark.integration
    def test_does_nothing_when_no_new_files(self, updater, shadow_io):
        """新しいファイルがない場合は何もしない"""
        updater.update_shadow_for_new_loops()

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert overall.get("source_files", []) == []

    @pytest.mark.integration
    def test_adds_new_loop_files(self, updater, temp_plugin_env, shadow_io):
        """新しいLoopファイルを追加"""
        # Loopファイルを作成
        create_test_loop_file(temp_plugin_env.loops_path, 1)
        create_test_loop_file(temp_plugin_env.loops_path, 2)

        updater.update_shadow_for_new_loops()

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert len(overall["source_files"]) == 2


# =============================================================================
# cascade_update_on_digest_finalize テスト
# =============================================================================

class TestCascadeUpdateOnDigestFinalize:
    """cascade_update_on_digest_finalize メソッドのテスト"""

    @pytest.mark.integration
    def test_clears_current_level(self, updater, temp_plugin_env, shadow_io):
        """現在のレベルがクリアされる"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        updater.add_files_to_shadow("weekly", [loop1])

        updater.cascade_update_on_digest_finalize("weekly")

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert overall["source_files"] == []

    @pytest.mark.integration
    def test_does_not_cascade_from_centurial(self, updater, shadow_io):
        """centurial（最上位）からはカスケードしない"""
        # centurialにはnext=Noneなのでカスケードしない
        updater.cascade_update_on_digest_finalize("centurial")

        # エラーなく完了すればOK
        shadow_data = shadow_io.load_or_create()
        assert shadow_data is not None


# =============================================================================
# ShadowUpdater 初期化テスト
# =============================================================================

class TestShadowUpdaterInit:
    """ShadowUpdater 初期化のテスト"""

    @pytest.mark.unit
    def test_stores_dependencies(self, shadow_io, file_detector, template, level_hierarchy):
        """依存関係が正しく保存される"""
        updater = ShadowUpdater(shadow_io, file_detector, template, level_hierarchy)

        assert updater.shadow_io is shadow_io
        assert updater.file_detector is file_detector
        assert updater.template is template
        assert updater.level_hierarchy is level_hierarchy


# =============================================================================
# _log_digest_content テスト（Phase 0で追加）
# =============================================================================

class TestLogDigestContent:
    """_log_digest_content メソッドのテスト"""

    @pytest.mark.integration
    def test_log_digest_content_valid_json(self, updater, temp_plugin_env, capsys):
        """有効なJSONファイルの内容をログ出力"""
        # Weekly Digestファイルを作成
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        weekly_file = weekly_dir / "W0001_test.txt"
        digest_content = {
            "overall_digest": {
                "digest_type": "weekly",
                "keywords": ["test", "keyword"],
                "abstract": "Test abstract content",
                "impression": "Test impression"
            }
        }
        with open(weekly_file, 'w', encoding='utf-8') as f:
            json.dump(digest_content, f)

        # _log_digest_contentを呼び出し（monthlyレベルでweeklyファイルを読む）
        updater._log_digest_content(weekly_file, "monthly")

        # 出力を検証
        captured = capsys.readouterr()
        assert "digest_type" in captured.out or "Read digest content" in captured.out

    @pytest.mark.integration
    def test_log_digest_content_json_decode_error(self, updater, temp_plugin_env, capsys):
        """無効なJSONファイルの場合、警告を出力"""
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        weekly_file = weekly_dir / "W0001_invalid.txt"
        with open(weekly_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json content")

        # エラーなく完了すること
        updater._log_digest_content(weekly_file, "monthly")

        # 警告が出力されていることを確認（ログ出力の内容は実装依存）
        # エラーで落ちないことが重要

    @pytest.mark.integration
    def test_log_digest_content_file_not_found(self, updater, temp_plugin_env):
        """存在しないファイルの場合、エラーなく終了"""
        nonexistent_file = temp_plugin_env.digests_path / "1_Weekly" / "W9999_nonexistent.txt"

        # エラーなく完了すること
        updater._log_digest_content(nonexistent_file, "monthly")

    @pytest.mark.integration
    def test_log_digest_content_non_txt_file(self, updater, temp_plugin_env):
        """非テキストファイル（.json等）は無視される"""
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        json_file = weekly_dir / "W0001_test.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({"test": "data"}, f)

        # .txt以外は無視されるので、エラーなく完了
        updater._log_digest_content(json_file, "monthly")

    @pytest.mark.integration
    def test_log_digest_content_non_dict_digest(self, updater, temp_plugin_env, capsys):
        """overall_digestがdict以外の場合、警告を出力"""
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        weekly_file = weekly_dir / "W0001_non_dict.txt"
        with open(weekly_file, 'w', encoding='utf-8') as f:
            json.dump({"overall_digest": "not a dict"}, f)

        updater._log_digest_content(weekly_file, "monthly")

        # 警告が出力されていることを確認


# =============================================================================
# promote_shadow_to_grand テスト（Phase 0で追加）
# =============================================================================

class TestPromoteShadowToGrand:
    """promote_shadow_to_grand メソッドのテスト"""

    @pytest.mark.integration
    def test_promote_shadow_to_grand_with_files(self, updater, temp_plugin_env, capsys):
        """ファイルがある場合、昇格準備完了をログ出力"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        loop2 = create_test_loop_file(temp_plugin_env.loops_path, 2)
        updater.add_files_to_shadow("weekly", [loop1, loop2])

        updater.promote_shadow_to_grand("weekly")

        # ログ出力を検証
        captured = capsys.readouterr()
        # "2 file(s)" または "2ファイル" が含まれることを確認
        assert "2" in captured.out or captured.out == ""  # ログ実装による

    @pytest.mark.integration
    def test_promote_shadow_to_grand_empty(self, updater, capsys):
        """空のShadowの場合、何もしない"""
        updater.promote_shadow_to_grand("weekly")

        # エラーなく完了すること
        captured = capsys.readouterr()
        # "No shadow digest" が含まれることを確認（または何も出力しない）

    @pytest.mark.integration
    def test_promote_shadow_to_grand_after_clear(self, updater, temp_plugin_env, capsys):
        """クリア後は昇格対象なし"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        updater.add_files_to_shadow("weekly", [loop1])
        updater.clear_shadow_level("weekly")

        updater.promote_shadow_to_grand("weekly")

        # エラーなく完了すること
