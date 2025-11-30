#!/usr/bin/env python3
"""
digest_config.py のテスト
=========================

ConfigEditor クラスと CLI エントリーポイントのテスト。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest


class TestConfigEditor(unittest.TestCase):
    """ConfigEditor クラスのテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        self._create_config()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_config(self):
        """設定ファイルを作成"""
        config_data = {
            "_comment_base_dir": "Data base directory",
            "base_dir": ".",
            "_comment_trusted_external_paths": "Trusted paths",
            "trusted_external_paths": [],
            "_comment_paths": "Paths config",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
            "_comment_levels": "Threshold config",
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_show_returns_current_config(self):
        """show が現在の設定を返す"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.show()

        assert result["status"] == "ok"
        assert "config" in result
        assert "resolved_paths" in result
        assert result["config"]["base_dir"] == "."

    @pytest.mark.unit
    def test_show_excludes_comment_fields(self):
        """show がコメントフィールドを除外する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.show()

        config = result["config"]
        for key in config.keys():
            assert not key.startswith("_comment")

    @pytest.mark.unit
    def test_show_includes_resolved_paths(self):
        """show が解決済みパスを含む"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.show()

        resolved = result["resolved_paths"]
        assert "plugin_root" in resolved
        assert "loops_path" in resolved
        assert "digests_path" in resolved
        assert "essences_path" in resolved

    @pytest.mark.unit
    def test_set_value_updates_nested_key(self):
        """set_value がネストされたキーを更新する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.set_value("levels.weekly_threshold", 7)

        assert result["status"] == "ok"
        assert result["old_value"] == 5
        assert result["new_value"] == 7

        # ファイルが更新されていることを確認
        with open(self.plugin_root / ".claude-plugin" / "config.json", "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        assert saved_config["levels"]["weekly_threshold"] == 7

    @pytest.mark.unit
    def test_set_value_converts_threshold_to_int(self):
        """set_value が閾値を整数に変換する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.set_value("levels.weekly_threshold", "10")

        assert result["status"] == "ok"
        assert result["new_value"] == 10
        assert isinstance(result["new_value"], int)

    @pytest.mark.unit
    def test_update_replaces_config(self):
        """update が設定を更新する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        new_config = {"base_dir": "../other"}
        result = editor.update(new_config)

        assert result["status"] == "ok"
        assert "base_dir" in result["updated_keys"]

    @pytest.mark.unit
    def test_update_preserves_comments(self):
        """update がコメントを保持する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        new_config = {"base_dir": "../other"}
        editor.update(new_config)

        with open(self.plugin_root / ".claude-plugin" / "config.json", "r", encoding="utf-8") as f:
            saved_config = json.load(f)

        assert "_comment_base_dir" in saved_config

    @pytest.mark.unit
    def test_add_trusted_path_adds_new_path(self):
        """add_trusted_path が新しいパスを追加する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.add_trusted_path("~/DEV/production")

        assert result["status"] == "ok"
        assert "~/DEV/production" in result["trusted_external_paths"]

    @pytest.mark.unit
    def test_add_trusted_path_rejects_relative_paths(self):
        """add_trusted_path が相対パスを拒否する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.add_trusted_path("relative/path")

        assert result["status"] == "error"
        assert "absolute" in result["error"].lower()

    @pytest.mark.unit
    def test_add_trusted_path_handles_duplicates(self):
        """add_trusted_path が重複を処理する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        editor.add_trusted_path("~/DEV/production")
        result = editor.add_trusted_path("~/DEV/production")

        assert result["status"] == "ok"
        assert "already exists" in result["message"].lower()

    @pytest.mark.unit
    def test_remove_trusted_path_removes_existing(self):
        """remove_trusted_path が既存のパスを削除する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        editor.add_trusted_path("~/DEV/production")
        result = editor.remove_trusted_path("~/DEV/production")

        assert result["status"] == "ok"
        assert "~/DEV/production" not in result["trusted_external_paths"]

    @pytest.mark.unit
    def test_remove_trusted_path_handles_nonexistent(self):
        """remove_trusted_path が存在しないパスを処理する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.remove_trusted_path("~/nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    @pytest.mark.unit
    def test_list_trusted_paths_returns_all_paths(self):
        """list_trusted_paths が全パスを返す"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        editor.add_trusted_path("~/path1")
        editor.add_trusted_path("~/path2")
        result = editor.list_trusted_paths()

        assert result["status"] == "ok"
        assert result["count"] == 2
        assert "~/path1" in result["trusted_external_paths"]


class TestConfigEditorErrors(unittest.TestCase):
    """ConfigEditor エラーハンドリングのテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_show_raises_when_config_missing(self):
        """設定ファイルがない場合に FileNotFoundError"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)

        with pytest.raises(FileNotFoundError):
            editor.show()


class TestConfigEditorResolvePath(unittest.TestCase):
    """ConfigEditor _resolve_path メソッドのテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        self._create_config()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_config(self):
        """設定ファイルを作成"""
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_resolve_absolute_path(self):
        """絶対パスはそのまま解決される"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        # Windowsでも動作するよう、tempディレクトリを使用
        abs_path = str(self.plugin_root / "some" / "path")
        result = editor._resolve_path(abs_path)

        assert result.is_absolute()

    @pytest.mark.unit
    def test_resolve_relative_path(self):
        """相対パスはbase_dirを基準に解決される"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor._resolve_path("subdir/file.txt")

        assert result.is_absolute()
        # plugin_root配下に解決されることを確認
        assert str(self.plugin_root) in str(result)


class TestConfigEditorSetValueErrors(unittest.TestCase):
    """ConfigEditor set_value エラーハンドリングのテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        config_data = {
            "base_dir": ".",
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_set_invalid_threshold_returns_error(self):
        """無効な閾値（整数に変換できない値）でエラーを返す"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.set_value("levels.weekly_threshold", "not_a_number")

        assert result["status"] == "error"
        assert "integer" in result["error"].lower()


class TestConfigEditorIdentityPath(unittest.TestCase):
    """ConfigEditor identity_file_path 処理のテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_show_with_identity_file_path(self):
        """identity_file_pathがある場合に解決済みパスに含まれる"""
        from interfaces.digest_config import ConfigEditor

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": "identity.json",
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.show()

        assert "identity_file_path" in result["resolved_paths"]


class TestOutputHelpers(unittest.TestCase):
    """出力ヘルパー関数のテスト"""

    @pytest.mark.unit
    def test_output_json_formats_correctly(self):
        """output_json が正しいJSON形式で出力する"""
        from unittest.mock import patch

        from interfaces.digest_config import output_json

        test_data = {"status": "ok", "message": "Test"}

        with patch("builtins.print") as mock_print:
            output_json(test_data)
            mock_print.assert_called_once()
            # 出力がJSON形式であることを確認
            call_args = mock_print.call_args[0][0]
            parsed = json.loads(call_args)
            assert parsed["status"] == "ok"

    @pytest.mark.unit
    def test_output_error_basic(self):
        """output_error が基本的なエラーを出力する"""
        from unittest.mock import patch

        from interfaces.digest_config import output_error

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                output_error("Test error")

            assert exc_info.value.code == 1
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            parsed = json.loads(call_args)
            assert parsed["status"] == "error"
            assert parsed["error"] == "Test error"

    @pytest.mark.unit
    def test_output_error_with_details(self):
        """output_error が詳細情報付きでエラーを出力する"""
        from unittest.mock import patch

        from interfaces.digest_config import output_error

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit):
                output_error("Test error", details={"action": "Run setup"})

            call_args = mock_print.call_args[0][0]
            parsed = json.loads(call_args)
            assert parsed["status"] == "error"
            assert parsed["details"]["action"] == "Run setup"


class TestConfigCLI(unittest.TestCase):
    """CLI エントリーポイントのテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        self._create_config()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_config(self):
        """設定ファイルを作成"""
        config_data = {
            "base_dir": ".",
            "trusted_external_paths": [],
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_main_show_command(self):
        """show コマンドが動作する"""
        from unittest.mock import patch

        with patch("sys.argv", ["digest_config.py", "--plugin-root", str(self.plugin_root), "show"]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                assert mock_print.called

    @pytest.mark.unit
    def test_main_set_command(self):
        """set コマンドが動作する"""
        from unittest.mock import patch

        with patch(
            "sys.argv",
            [
                "digest_config.py",
                "--plugin-root",
                str(self.plugin_root),
                "set",
                "--key",
                "levels.weekly_threshold",
                "--value",
                "7",
            ],
        ):
            from interfaces.digest_config import main

            with patch("builtins.print"):
                main()

        # 値が更新されていることを確認
        with open(self.plugin_root / ".claude-plugin" / "config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        assert config["levels"]["weekly_threshold"] == 7

    @pytest.mark.unit
    def test_main_help_exits_zero(self):
        """--help で exit code 0"""
        from unittest.mock import patch

        with patch("sys.argv", ["digest_config.py", "--help"]):
            with patch("sys.stdout"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_config import main

                    main()
                assert exc_info.value.code == 0


# ============================================================================
# 追加CLIテストクラス（Phase 1: In-Process拡充）
# ============================================================================


class TestConfigCLIUpdateCommand(unittest.TestCase):
    """update サブコマンドのCLIテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        self._create_config()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_config(self):
        """設定ファイルを作成"""
        config_data = {
            "base_dir": ".",
            "trusted_external_paths": [],
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_update_with_valid_json(self):
        """update --config で有効なJSONを渡す"""
        config_json = json.dumps({"base_dir": "../new_path"})

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", config_json
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert "base_dir" in result["updated_keys"]

    @pytest.mark.unit
    def test_update_with_invalid_json_exits_error(self):
        """update --config に不正なJSONを渡すとエラー"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", "{invalid json"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_update_with_empty_json_object(self):
        """update --config で空のJSONオブジェクト"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", "{}"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert result["updated_keys"] == []

    @pytest.mark.unit
    def test_update_preserves_existing_keys(self):
        """update が既存キーを保持する"""
        config_json = json.dumps({"base_dir": "../updated"})

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", config_json
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print"):
                main()

        # levels キーが保持されていることを確認
        with open(self.plugin_root / ".claude-plugin" / "config.json", "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        assert "levels" in saved_config
        assert saved_config["levels"]["weekly_threshold"] == 5

    @pytest.mark.unit
    def test_update_missing_config_flag_exits_error(self):
        """update で --config フラグがない場合にエラー"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update"
        ]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_config import main
                    main()
                assert exc_info.value.code == 2  # argparse error

    @pytest.mark.unit
    def test_update_output_is_valid_json(self):
        """update の出力が有効なJSON"""
        config_json = json.dumps({"base_dir": "."})

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", config_json
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                # JSONとしてパース可能であることを確認
                result = json.loads(output)
                assert isinstance(result, dict)

    @pytest.mark.unit
    def test_update_with_partial_config(self):
        """update で一部のキーのみ更新"""
        config_json = json.dumps({
            "levels": {"weekly_threshold": 10}
        })

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", config_json
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"

        # 更新されていることを確認
        with open(self.plugin_root / ".claude-plugin" / "config.json", "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        assert saved_config["levels"]["weekly_threshold"] == 10

    @pytest.mark.unit
    def test_update_reports_updated_keys(self):
        """update が更新されたキーを報告"""
        config_json = json.dumps({
            "base_dir": "../new",
            "levels": {"weekly_threshold": 7}
        })

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", config_json
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert "base_dir" in result["updated_keys"]
                assert "levels" in result["updated_keys"]


class TestConfigCLISetCommandExtended(unittest.TestCase):
    """set サブコマンドの追加CLIテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        self._create_config()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_config(self):
        """設定ファイルを作成"""
        config_data = {
            "base_dir": ".",
            "trusted_external_paths": [],
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {"weekly_threshold": 5, "monthly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_set_missing_key_exits_error(self):
        """set で --key がない場合にエラー"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "set",
            "--value", "7"
        ]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_config import main
                    main()
                assert exc_info.value.code == 2

    @pytest.mark.unit
    def test_set_missing_value_exits_error(self):
        """set で --value がない場合にエラー"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "set",
            "--key", "levels.weekly_threshold"
        ]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_config import main
                    main()
                assert exc_info.value.code == 2

    @pytest.mark.unit
    def test_set_deeply_nested_key(self):
        """set で深くネストされたキーを設定"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "set",
            "--key", "paths.loops_dir",
            "--value", "custom/Loops"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert result["new_value"] == "custom/Loops"

    @pytest.mark.unit
    def test_set_creates_intermediate_keys(self):
        """set が中間キーを作成する"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "set",
            "--key", "new_section.new_key",
            "--value", "new_value"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"

        # ファイルを確認
        with open(self.plugin_root / ".claude-plugin" / "config.json", "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        assert saved_config["new_section"]["new_key"] == "new_value"

    @pytest.mark.unit
    def test_set_boolean_true(self):
        """set で true を設定"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "set",
            "--key", "some_flag",
            "--value", "true"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["new_value"] is True

    @pytest.mark.unit
    def test_set_boolean_false(self):
        """set で false を設定"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "set",
            "--key", "some_flag",
            "--value", "false"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["new_value"] is False

    @pytest.mark.unit
    def test_set_null_value(self):
        """set で null を設定"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "set",
            "--key", "paths.identity_file_path",
            "--value", "null"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["new_value"] is None

    @pytest.mark.unit
    def test_set_negative_integer(self):
        """set で負の整数を設定"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "set",
            "--key", "some_value",
            "--value", "-10"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["new_value"] == -10

    @pytest.mark.unit
    def test_set_threshold_invalid_string_exits_error(self):
        """set で閾値に無効な文字列を設定するとエラー"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "set",
            "--key", "levels.weekly_threshold",
            "--value", "not_a_number"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"
                assert "integer" in result["error"].lower()

    @pytest.mark.unit
    def test_set_output_shows_old_value(self):
        """set が古い値を表示"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "set",
            "--key", "levels.weekly_threshold",
            "--value", "10"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["old_value"] == 5
                assert result["new_value"] == 10


class TestConfigCLITrustedPathsCommand(unittest.TestCase):
    """trusted-paths サブコマンドのCLIテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        self._create_config()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_config(self):
        """設定ファイルを作成"""
        config_data = {
            "base_dir": ".",
            "trusted_external_paths": [],
            "paths": {
                "loops_dir": "data/Loops",
            },
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_trusted_paths_list_empty(self):
        """trusted-paths list で空リスト"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "list"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert result["count"] == 0
                assert result["trusted_external_paths"] == []

    @pytest.mark.unit
    def test_trusted_paths_list_with_paths(self):
        """trusted-paths list でパスあり"""
        # 先にパスを追加
        config_data = {
            "base_dir": ".",
            "trusted_external_paths": ["~/path1", "~/path2"],
            "paths": {"loops_dir": "data/Loops"},
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "list"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["count"] == 2

    @pytest.mark.unit
    def test_trusted_paths_add_valid_absolute_path(self):
        """trusted-paths add で有効な絶対パス"""
        # Windowsでも動作するよう、tempディレクトリを使用
        abs_path = str(self.plugin_root / "external")

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "add", abs_path
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert abs_path in result["trusted_external_paths"]

    @pytest.mark.unit
    def test_trusted_paths_add_tilde_path(self):
        """trusted-paths add で ~ パス"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "add", "~/DEV/production"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert "~/DEV/production" in result["trusted_external_paths"]

    @pytest.mark.unit
    def test_trusted_paths_add_relative_path_rejected(self):
        """trusted-paths add で相対パスを拒否"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "add", "relative/path"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_trusted_paths_add_duplicate_handled(self):
        """trusted-paths add で重複を処理"""
        # 先にパスを追加
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "add", "~/DEV/test"
        ]):
            from interfaces.digest_config import main
            with patch("builtins.print"):
                main()

        # 同じパスを再度追加
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "add", "~/DEV/test"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert "already exists" in result["message"].lower()

    @pytest.mark.unit
    def test_trusted_paths_remove_existing(self):
        """trusted-paths remove で既存パス削除"""
        # 先にパスを追加
        config_data = {
            "base_dir": ".",
            "trusted_external_paths": ["~/DEV/production"],
            "paths": {"loops_dir": "data/Loops"},
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "remove", "~/DEV/production"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert "~/DEV/production" not in result["trusted_external_paths"]

    @pytest.mark.unit
    def test_trusted_paths_remove_nonexistent_error(self):
        """trusted-paths remove で存在しないパスはエラー"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "remove", "~/nonexistent"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_trusted_paths_no_subcommand_lists(self):
        """trusted-paths でサブコマンドなしはリスト表示"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert "trusted_external_paths" in result

    @pytest.mark.unit
    def test_trusted_paths_output_is_valid_json(self):
        """trusted-paths の出力が有効なJSON"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "list"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                # JSONとしてパース可能であることを確認
                result = json.loads(output)
                assert isinstance(result, dict)


class TestConfigCLINoCommand(unittest.TestCase):
    """コマンドなしの場合のテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        config_data = {"base_dir": ".", "levels": {"weekly_threshold": 5}}
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_no_command_exits_with_code_1(self):
        """コマンドなしで exit code 1"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root)
        ]):
            with patch("sys.stdout"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_config import main
                    main()
                assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_invalid_command_exits_with_error(self):
        """無効なコマンドでエラー"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "invalid_command"
        ]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_config import main
                    main()
                assert exc_info.value.code == 2  # argparse error


if __name__ == "__main__":
    unittest.main()
