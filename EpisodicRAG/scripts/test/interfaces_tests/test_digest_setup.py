#!/usr/bin/env python3
"""
digest_setup.py のテスト
========================

SetupManager クラスと CLI エントリーポイントのテスト。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSetupManager(unittest.TestCase):
    """SetupManager クラスのテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        # .claude-plugin ディレクトリを作成
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_templates(self):
        """テンプレートファイルを作成"""
        template_dir = self.plugin_root / ".claude-plugin"

        # GrandDigest.template.txt
        grand_template = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "major_digests": {},
        }
        with open(template_dir / "GrandDigest.template.txt", "w", encoding="utf-8") as f:
            json.dump(grand_template, f)

        # ShadowGrandDigest.template.txt
        shadow_template = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {},
        }
        with open(template_dir / "ShadowGrandDigest.template.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_template, f)

        # last_digest_times.template.json
        times_template = {"weekly": {"timestamp": "", "last_processed": None}}
        with open(template_dir / "last_digest_times.template.json", "w", encoding="utf-8") as f:
            json.dump(times_template, f)

    @pytest.mark.unit
    def test_check_returns_not_configured_when_no_config(self):
        """設定ファイルがない場合、not_configured を返す"""
        from interfaces.digest_setup import SetupManager

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.check()

        assert result["status"] == "not_configured"
        assert result["config_exists"] is False
        assert result["directories_exist"] is False

    @pytest.mark.unit
    def test_check_returns_configured_when_setup_complete(self):
        """セットアップ完了時に configured を返す"""
        from interfaces.digest_setup import SetupManager

        # 設定ファイルを作成
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
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

        # ディレクトリを作成
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.check()

        assert result["status"] == "configured"
        assert result["config_exists"] is True
        assert result["directories_exist"] is True

    @pytest.mark.unit
    def test_init_creates_config_file(self):
        """init が設定ファイルを作成する"""
        from interfaces.digest_setup import SetupManager

        self._create_templates()

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
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

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data)

        assert result.status == "ok"
        assert (self.plugin_root / ".claude-plugin" / "config.json").exists()

    @pytest.mark.unit
    def test_init_creates_directories(self):
        """init がディレクトリを作成する"""
        from interfaces.digest_setup import SetupManager

        self._create_templates()

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
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

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data)

        assert result.status == "ok"
        assert (self.plugin_root / "data" / "Loops").exists()
        assert (self.plugin_root / "data" / "Digests" / "1_Weekly").exists()
        assert (self.plugin_root / "data" / "Digests" / "1_Weekly" / "Provisional").exists()
        assert (self.plugin_root / "data" / "Essences").exists()

    @pytest.mark.unit
    def test_init_creates_initial_files(self):
        """init が初期ファイルを作成する"""
        from interfaces.digest_setup import SetupManager

        self._create_templates()

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
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

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data)

        assert result.status == "ok"
        assert "GrandDigest.txt" in result.created["files"]
        assert "ShadowGrandDigest.txt" in result.created["files"]
        assert (self.plugin_root / "data" / "Essences" / "GrandDigest.txt").exists()

    @pytest.mark.unit
    def test_init_fails_without_force_when_config_exists(self):
        """既存設定がある場合、force なしで失敗する"""
        from interfaces.digest_setup import SetupManager

        # 既存の設定ファイルを作成
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump({}, f)

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
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

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data)

        assert result.status == "already_configured"

    @pytest.mark.unit
    def test_init_succeeds_with_force_when_config_exists(self):
        """既存設定がある場合でも force で成功する"""
        from interfaces.digest_setup import SetupManager

        self._create_templates()

        # 既存の設定ファイルを作成
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump({}, f)

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
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

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data, force=True)

        assert result.status == "ok"

    @pytest.mark.unit
    def test_init_validates_config_data(self):
        """init が設定データをバリデーションする"""
        from interfaces.digest_setup import SetupManager

        # 必須フィールドがない設定
        config_data = {"base_dir": "."}

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data)

        assert result.status == "error"
        assert "paths" in result.error

    @pytest.mark.unit
    def test_init_detects_external_paths(self):
        """init が外部パスを検出する"""
        from interfaces.digest_setup import SetupManager

        self._create_templates()

        config_data = {
            "base_dir": "~/external/path",  # 外部パス
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
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

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data)

        assert result.status == "ok"
        assert len(result.external_paths_detected) > 0
        assert any("base_dir" in p for p in result.external_paths_detected)


class TestSetupManagerCheckEdgeCases(unittest.TestCase):
    """SetupManager check() のエッジケーステスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_check_returns_partial_when_config_exists_but_dirs_missing(self):
        """設定ファイルがあるがディレクトリがない場合、partial を返す"""
        from interfaces.digest_setup import SetupManager

        # 設定ファイルを作成（ディレクトリは作成しない）
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.check()

        assert result["status"] == "partial"
        assert result["config_exists"] is True
        assert result["directories_exist"] is False

    @pytest.mark.unit
    def test_check_handles_corrupt_json(self):
        """破損したJSONファイルを処理する"""
        from interfaces.digest_setup import SetupManager

        # 破損したJSONファイルを作成
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            f.write("{ invalid json content")

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.check()

        # JSONDecodeErrorをキャッチしてpartialまたはnot_configuredを返す
        # 設定ファイルは存在するがパースできないので結果はpartial相当
        assert result["status"] in ["partial", "not_configured"]
        assert result["config_exists"] is True

    @pytest.mark.unit
    def test_check_handles_missing_keys_in_config(self):
        """設定にpathsキーがない場合を処理する"""
        from interfaces.digest_setup import SetupManager

        # pathsキーがない設定ファイルを作成
        config_data = {"base_dir": "."}  # pathsがない
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.check()

        # KeyErrorをキャッチして処理
        assert result["status"] in ["partial", "not_configured"]
        assert result["config_exists"] is True


class TestSetupCLI(unittest.TestCase):
    """CLI エントリーポイントのテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_main_check_command(self):
        """check コマンドが動作する"""
        from unittest.mock import patch

        with patch("sys.argv", ["digest_setup.py", "--plugin-root", str(self.plugin_root), "check"]):
            from interfaces.digest_setup import main

            # 出力をキャプチャ
            with patch("builtins.print") as mock_print:
                main()
                # JSON が出力されることを確認
                assert mock_print.called

    @pytest.mark.unit
    def test_main_help_exits_zero(self):
        """--help で exit code 0"""
        from unittest.mock import patch

        with patch("sys.argv", ["digest_setup.py", "--help"]):
            with patch("sys.stdout"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_setup import main

                    main()
                assert exc_info.value.code == 0


# ============================================================================
# 追加CLIテストクラス（Phase 1: In-Process拡充）
# ============================================================================


class TestSetupCLIInitCommand(unittest.TestCase):
    """init サブコマンドのCLIテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        self._create_templates()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_templates(self):
        """テンプレートファイルを作成"""
        template_dir = self.plugin_root / ".claude-plugin"
        grand_template = {"metadata": {"last_updated": "", "version": "1.0"}, "major_digests": {}}
        with open(template_dir / "GrandDigest.template.txt", "w", encoding="utf-8") as f:
            json.dump(grand_template, f)
        shadow_template = {"metadata": {"last_updated": "", "version": "1.0"}, "latest_digests": {}}
        with open(template_dir / "ShadowGrandDigest.template.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_template, f)
        times_template = {"weekly": {"timestamp": "", "last_processed": None}}
        with open(template_dir / "last_digest_times.template.json", "w", encoding="utf-8") as f:
            json.dump(times_template, f)

    def _get_valid_config_json(self):
        """有効な設定JSONを返す"""
        return json.dumps({
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
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
        })

    @pytest.mark.unit
    def test_init_with_valid_config_json(self):
        """init --config で有効なJSONを渡す"""
        from unittest.mock import patch

        config_json = self._get_valid_config_json()

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init",
            "--config", config_json
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert result["created"] is not None

    @pytest.mark.unit
    def test_init_with_invalid_json_exits_error(self):
        """init --config に不正なJSONを渡すとエラー"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init",
            "--config", "{invalid json"
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_init_with_missing_paths_exits_error(self):
        """init --config で paths がないとエラー"""
        from unittest.mock import patch

        config_json = json.dumps({
            "base_dir": ".",
            "levels": {"weekly_threshold": 5},
        })

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init",
            "--config", config_json
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"
                assert "paths" in result["error"].lower()

    @pytest.mark.unit
    def test_init_with_missing_levels_exits_error(self):
        """init --config で levels がないとエラー"""
        from unittest.mock import patch

        config_json = json.dumps({
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
        })

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init",
            "--config", config_json
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"
                assert "levels" in result["error"].lower()

    @pytest.mark.unit
    def test_init_with_invalid_threshold_exits_error(self):
        """init --config で無効な閾値を渡すとエラー"""
        from unittest.mock import patch

        config_json = json.dumps({
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {
                "weekly_threshold": -1,  # 無効な値
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        })

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init",
            "--config", config_json
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_init_creates_directories(self):
        """init がディレクトリを作成する"""
        from unittest.mock import patch

        config_json = self._get_valid_config_json()

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init",
            "--config", config_json
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print"):
                main()

        # ディレクトリが作成されていることを確認
        assert (self.plugin_root / "data" / "Loops").exists()
        assert (self.plugin_root / "data" / "Digests" / "1_Weekly").exists()
        assert (self.plugin_root / "data" / "Essences").exists()

    @pytest.mark.unit
    def test_init_creates_config_file(self):
        """init が設定ファイルを作成する"""
        from unittest.mock import patch

        config_json = self._get_valid_config_json()

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init",
            "--config", config_json
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print"):
                main()

        # 設定ファイルが作成されていることを確認
        assert (self.plugin_root / ".claude-plugin" / "config.json").exists()

    @pytest.mark.unit
    def test_init_without_force_fails_when_exists(self):
        """既存設定がある場合、force なしで失敗する"""
        from unittest.mock import patch

        # 既存の設定ファイルを作成
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump({}, f)

        config_json = self._get_valid_config_json()

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init",
            "--config", config_json
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "already_configured"

    @pytest.mark.unit
    def test_init_with_force_overwrites_existing(self):
        """既存設定がある場合でも force で上書きする"""
        from unittest.mock import patch

        # 既存の設定ファイルを作成
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump({"old": "config"}, f)

        config_json = self._get_valid_config_json()

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init",
            "--config", config_json,
            "--force"
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"

    @pytest.mark.unit
    def test_init_detects_external_paths(self):
        """init が外部パスを検出する"""
        from unittest.mock import patch

        config_json = json.dumps({
            "base_dir": "~/external/path",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
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
        })

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init",
            "--config", config_json
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert len(result["external_paths_detected"]) > 0

    @pytest.mark.unit
    def test_init_output_is_valid_json(self):
        """init の出力が有効なJSON"""
        from unittest.mock import patch

        config_json = self._get_valid_config_json()

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init",
            "--config", config_json
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                # JSONとしてパース可能であることを確認
                result = json.loads(output)
                assert isinstance(result, dict)

    @pytest.mark.unit
    def test_init_output_contains_created_info(self):
        """init の出力が作成情報を含む"""
        from unittest.mock import patch

        config_json = self._get_valid_config_json()

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init",
            "--config", config_json
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert "created" in result
                assert "config_file" in result["created"]
                assert "directories" in result["created"]
                assert "files" in result["created"]


class TestSetupCLICheckCommandExtended(unittest.TestCase):
    """check サブコマンドの追加CLIテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_check_not_configured_output_format(self):
        """check の not_configured 出力形式"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "check"
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "not_configured"
                assert "config_exists" in result
                assert "directories_exist" in result
                assert "message" in result

    @pytest.mark.unit
    def test_check_configured_output_format(self):
        """check の configured 出力形式"""
        from unittest.mock import patch

        # 設定ファイルとディレクトリを作成
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "check"
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "configured"
                assert result["config_exists"] is True
                assert result["directories_exist"] is True

    @pytest.mark.unit
    def test_check_partial_output_format(self):
        """check の partial 出力形式"""
        from unittest.mock import patch

        # 設定ファイルのみ作成（ディレクトリなし）
        config_data = {
            "base_dir": ".",
            "paths": {"loops_dir": "data/Loops"},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "check"
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "partial"
                assert result["config_exists"] is True
                assert result["directories_exist"] is False

    @pytest.mark.unit
    def test_check_with_corrupted_config(self):
        """check で破損した設定ファイルを処理"""
        from unittest.mock import patch

        # 破損したJSONファイルを作成
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "check"
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                # エラーにならずにpartialを返す
                assert result["status"] in ["partial", "not_configured"]
                assert result["config_exists"] is True

    @pytest.mark.unit
    def test_check_output_is_valid_json(self):
        """check の出力が有効なJSON"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "check"
        ]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                # JSONとしてパース可能であることを確認
                result = json.loads(output)
                assert isinstance(result, dict)


class TestSetupCLINoCommand(unittest.TestCase):
    """コマンドなしの場合のテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_no_command_exits_with_code_1(self):
        """コマンドなしで exit code 1"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root)
        ]):
            with patch("sys.stdout"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_setup import main
                    main()
                assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_invalid_command_exits_with_error(self):
        """無効なコマンドでエラー"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "invalid_command"
        ]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_setup import main
                    main()
                assert exc_info.value.code == 2  # argparse error

    @pytest.mark.unit
    def test_init_missing_config_flag_exits_error(self):
        """init で --config フラグがない場合にエラー"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_setup.py",
            "--plugin-root", str(self.plugin_root),
            "init"
        ]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_setup import main
                    main()
                assert exc_info.value.code == 2  # argparse error


if __name__ == "__main__":
    unittest.main()
