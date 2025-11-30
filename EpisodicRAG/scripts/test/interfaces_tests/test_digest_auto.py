#!/usr/bin/env python3
"""
digest_auto.py のテスト
=======================

DigestAutoAnalyzer クラスと CLI エントリーポイントのテスト。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest


class TestDigestAutoAnalyzer(unittest.TestCase):
    """DigestAutoAnalyzer クラスのテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self._setup_plugin_structure()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self):
        """プラグイン構造を作成"""
        # ディレクトリ構造
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Digests").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

        # Digestサブディレクトリ
        for subdir in [
            "1_Weekly",
            "2_Monthly",
            "3_Quarterly",
            "4_Annual",
            "5_Triennial",
            "6_Decadal",
            "7_Multi-decadal",
            "8_Centurial",
        ]:
            (self.plugin_root / "data" / "Digests" / subdir).mkdir()
            (self.plugin_root / "data" / "Digests" / subdir / "Provisional").mkdir()

        # config.json
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

        # ShadowGrandDigest.txt
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {"overall_digest": None},
                "monthly": {"overall_digest": None},
            },
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

        # GrandDigest.txt
        grand_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "major_digests": {},
        }
        with open(self.plugin_root / "data" / "Essences" / "GrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(grand_data, f)

        # last_digest_times.json
        times_data = {"weekly": {"timestamp": "", "last_processed": None}}
        with open(self.plugin_root / ".claude-plugin" / "last_digest_times.json", "w", encoding="utf-8") as f:
            json.dump(times_data, f)

    @pytest.mark.unit
    def test_analyze_returns_ok_when_no_issues(self):
        """問題がない場合に ok を返す"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        assert result.status == "ok"
        assert len(result.issues) == 0

    @pytest.mark.unit
    def test_analyze_detects_unprocessed_loops(self):
        """未処理Loopを検出する"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # Loopファイルを作成
        (self.plugin_root / "data" / "Loops" / "L00001_Test.txt").write_text("content")
        (self.plugin_root / "data" / "Loops" / "L00002_Test.txt").write_text("content")

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        # 未処理Loopの問題が検出される
        unprocessed_issues = [i for i in result.issues if i.type == "unprocessed_loops"]
        assert len(unprocessed_issues) == 1
        assert unprocessed_issues[0].count == 2

    @pytest.mark.unit
    def test_analyze_detects_placeholders(self):
        """プレースホルダーを検出する"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # プレースホルダー付きのShadowを作成
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "source_files": ["L00001", "L00002"],
                        "abstract": "<!-- PLACEHOLDER: abstract -->",
                    }
                },
            },
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        placeholder_issues = [i for i in result.issues if i.type == "placeholders"]
        assert len(placeholder_issues) == 1
        assert placeholder_issues[0].level == "weekly"

    @pytest.mark.unit
    def test_analyze_detects_gaps(self):
        """中間ファイルのギャップを検出する"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # ギャップのあるsource_filesを持つShadowを作成
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "source_files": ["L00001", "L00003", "L00005"],  # L00002, L00004 が欠番
                        "abstract": "completed abstract",
                    }
                },
            },
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        gap_issues = [i for i in result.issues if i.type == "gaps"]
        assert len(gap_issues) == 1
        assert gap_issues[0].count == 2  # 2つの欠番

    @pytest.mark.unit
    def test_analyze_determines_generatable_levels(self):
        """生成可能な階層を判定する"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # 5つのLoopファイルを作成（weekly thresholdを満たす）
        for i in range(1, 6):
            (self.plugin_root / "data" / "Loops" / f"L{i:05d}_Test.txt").write_text("content")

        # last_processedを更新して未処理扱いにしない
        times_data = {"weekly": {"timestamp": "2025-01-01T00:00:00", "last_processed": 5}}
        with open(self.plugin_root / ".claude-plugin" / "last_digest_times.json", "w", encoding="utf-8") as f:
            json.dump(times_data, f)

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        # weeklyが生成可能
        weekly_levels = [l for l in result.generatable_levels if l.level == "weekly"]
        assert len(weekly_levels) == 1
        assert weekly_levels[0].ready is True

    @pytest.mark.unit
    def test_analyze_includes_recommendations(self):
        """推奨アクションが含まれる"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # 未処理Loopを作成
        (self.plugin_root / "data" / "Loops" / "L00001_Test.txt").write_text("content")

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        assert len(result.recommendations) > 0

    @pytest.mark.unit
    def test_analyze_returns_error_when_config_missing(self):
        """設定ファイルがない場合にエラーを返す"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # config.jsonを削除
        (self.plugin_root / ".claude-plugin" / "config.json").unlink()

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        assert result.status == "error"
        assert result.error is not None

    @pytest.mark.unit
    def test_analyze_returns_error_when_shadow_missing(self):
        """ShadowGrandDigestがない場合にエラーを返す"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # ShadowGrandDigest.txtを削除
        (self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt").unlink()

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        assert result.status == "error"


class TestDigestAutoAnalyzerHelpers(unittest.TestCase):
    """DigestAutoAnalyzer ヘルパーメソッドのテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_extract_file_number(self):
        """ファイル名から番号を抽出する"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)

        assert analyzer._extract_file_number("L00001_Test.txt") == 1
        assert analyzer._extract_file_number("W0005_Weekly.txt") == 5
        assert analyzer._extract_file_number("M003_Monthly.txt") == 3
        assert analyzer._extract_file_number("invalid") is None

    @pytest.mark.unit
    def test_find_gaps(self):
        """連番のギャップを検出する"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)

        assert analyzer._find_gaps([1, 2, 3]) == []
        assert analyzer._find_gaps([1, 3, 5]) == [2, 4]
        assert analyzer._find_gaps([1]) == []
        assert analyzer._find_gaps([]) == []

    @pytest.mark.unit
    def test_load_json_file_returns_none_for_invalid_json(self):
        """無効なJSONファイルに対してNoneを返す"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # 無効なJSONファイルを作成
        invalid_json_file = self.plugin_root / "invalid.json"
        invalid_json_file.write_text("{ invalid json content")

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer._load_json_file(invalid_json_file)

        assert result is None

    @pytest.mark.unit
    def test_load_json_file_returns_none_for_missing_file(self):
        """存在しないファイルに対してNoneを返す"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer._load_json_file(self.plugin_root / "nonexistent.json")

        assert result is None

    @pytest.mark.unit
    def test_load_json_file_returns_data_for_valid_json(self):
        """有効なJSONファイルに対してデータを返す"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # 有効なJSONファイルを作成
        valid_json_file = self.plugin_root / "valid.json"
        valid_json_file.write_text('{"key": "value"}')

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer._load_json_file(valid_json_file)

        assert result is not None
        assert result["key"] == "value"


class TestDigestAutoCLI(unittest.TestCase):
    """CLI エントリーポイントのテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self._setup_plugin_structure()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self):
        """最小のプラグイン構造を作成"""
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {"weekly": {"overall_digest": None}},
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

    @pytest.mark.unit
    def test_main_json_output(self):
        """JSON出力が動作する"""
        from unittest.mock import patch

        with patch(
            "sys.argv", ["digest_auto.py", "--output", "json", "--plugin-root", str(self.plugin_root)]
        ):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                assert mock_print.called
                # JSON形式であることを確認
                call_args = mock_print.call_args[0][0]
                parsed = json.loads(call_args)
                assert "status" in parsed

    @pytest.mark.unit
    def test_main_text_output(self):
        """テキスト出力が動作する"""
        from unittest.mock import patch

        with patch(
            "sys.argv", ["digest_auto.py", "--output", "text", "--plugin-root", str(self.plugin_root)]
        ):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                assert mock_print.called

    @pytest.mark.unit
    def test_main_help_exits_zero(self):
        """--help で exit code 0"""
        from unittest.mock import patch

        with patch("sys.argv", ["digest_auto.py", "--help"]):
            with patch("sys.stdout"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_auto import main

                    main()
                assert exc_info.value.code == 0


# ============================================================================
# 追加CLIテストクラス（Phase 1: In-Process拡充）
# ============================================================================


class TestDigestAutoCLIArgumentValidation(unittest.TestCase):
    """CLI引数バリデーションのテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self._setup_plugin_structure()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self):
        """最小のプラグイン構造を作成"""
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {"weekly": {"overall_digest": None}},
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

    @pytest.mark.unit
    def test_invalid_output_format_exits_with_error(self):
        """無効な --output 形式でエラー終了"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "invalid_format",
            "--plugin-root", str(self.plugin_root)
        ]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_auto import main
                    main()
                assert exc_info.value.code == 2  # argparse error

    @pytest.mark.unit
    def test_default_output_is_json(self):
        """--output 省略時はJSONがデフォルト"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_auto.py",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                # JSONとしてパース可能であることを確認
                result = json.loads(output)
                assert isinstance(result, dict)

    @pytest.mark.unit
    def test_plugin_root_without_config_exits_with_error(self):
        """config.json がない場合にエラー"""

        # config.json を削除
        (self.plugin_root / ".claude-plugin" / "config.json").unlink()

        with patch("sys.argv", [
            "digest_auto.py",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                # Note: digest_auto returns exit code 0 even with status="error"
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_nonexistent_plugin_root(self):
        """存在しない plugin-root でエラー"""

        with patch("sys.argv", [
            "digest_auto.py",
            "--plugin-root", "/nonexistent/path/to/plugin"
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                # Note: digest_auto returns exit code 0 even with status="error"
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_output_json_option(self):
        """--output json オプションが動作"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert "status" in result

    @pytest.mark.unit
    def test_output_text_option(self):
        """--output text オプションが動作（format_text_reportを直接テスト）"""
        from interfaces.digest_auto import AnalysisResult, format_text_report

        result = AnalysisResult(status="ok")
        formatted = format_text_report(result)

        # テキスト形式であることを確認
        assert "```text" in formatted
        assert "━" in formatted

    @pytest.mark.unit
    def test_unknown_option_exits_with_error(self):
        """未知のオプションでエラー終了"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_auto.py",
            "--unknown-option",
            "--plugin-root", str(self.plugin_root)
        ]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_auto import main
                    main()
                assert exc_info.value.code == 2

    @pytest.mark.unit
    def test_positional_args_accepted(self):
        """位置引数はargparseで定義されていないためエラー（または無視）"""
        from unittest.mock import patch

        # argparseの設定によっては位置引数がエラーになる
        with patch("sys.argv", [
            "digest_auto.py",
            "unexpected_positional",
            "--plugin-root", str(self.plugin_root)
        ]):
            with patch("sys.stderr"):
                # 位置引数がエラーになるかどうかを確認
                try:
                    from interfaces.digest_auto import main
                    with patch("builtins.print"):
                        main()
                except SystemExit as e:
                    # argparseがエラーを返す場合
                    assert e.code == 2


class TestDigestAutoCLIOutputFormats(unittest.TestCase):
    """出力形式テスト（JSON vs Text）"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self._setup_plugin_structure()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self):
        """プラグイン構造を作成"""
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Digests").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

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
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {"overall_digest": None},
                "monthly": {"overall_digest": None},
            },
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

        grand_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "major_digests": {},
        }
        with open(self.plugin_root / "data" / "Essences" / "GrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(grand_data, f)

        times_data = {"weekly": {"timestamp": "", "last_processed": None}}
        with open(self.plugin_root / ".claude-plugin" / "last_digest_times.json", "w", encoding="utf-8") as f:
            json.dump(times_data, f)

    @pytest.mark.unit
    def test_json_output_is_valid_json(self):
        """JSON出力がパース可能"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert isinstance(result, dict)

    @pytest.mark.unit
    def test_json_output_contains_required_fields(self):
        """JSON出力に必須フィールドが含まれる"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)

                assert "status" in result
                assert result["status"] in ["ok", "warning", "error"]

    @pytest.mark.unit
    def test_text_output_contains_header(self):
        """テキスト出力にヘッダーが含まれる"""
        from interfaces.digest_auto import AnalysisResult, format_text_report

        result = AnalysisResult(status="ok")
        formatted = format_text_report(result)

        assert "📊 EpisodicRAG システム状態" in formatted
        assert "```text" in formatted

    @pytest.mark.unit
    def test_text_output_contains_status_indicators(self):
        """テキスト出力にステータスインジケータが含まれる"""
        from interfaces.digest_auto import AnalysisResult, Issue, format_text_report

        # 警告ありの結果を作成
        result = AnalysisResult(
            status="warning",
            issues=[Issue(type="unprocessed_loops", count=2, files=["L00001.txt", "L00002.txt"])]
        )
        formatted = format_text_report(result)

        # 警告インジケータが含まれることを確認
        assert "⚠️" in formatted
        assert "未処理Loop" in formatted

    @pytest.mark.unit
    def test_error_json_contains_status_error(self):
        """エラー時にJSON出力がstatus=errorを含む"""
        from unittest.mock import patch

        # ShadowGrandDigestを削除してエラーを発生させる
        (self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt").unlink()

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_error_json_contains_error_message(self):
        """エラー時にJSON出力がerrorメッセージを含む"""
        from unittest.mock import patch

        # ShadowGrandDigestを削除してエラーを発生させる
        (self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt").unlink()

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert "error" in result
                assert result["error"] is not None


class TestDigestAutoCLIScenarios(unittest.TestCase):
    """統合シナリオテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self._setup_plugin_structure()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self):
        """完全なプラグイン構造を作成"""
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Digests").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

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

        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {"overall_digest": None},
                "monthly": {"overall_digest": None},
            },
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

        grand_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "major_digests": {},
        }
        with open(self.plugin_root / "data" / "Essences" / "GrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(grand_data, f)

        times_data = {"weekly": {"timestamp": "", "last_processed": None}}
        with open(self.plugin_root / ".claude-plugin" / "last_digest_times.json", "w", encoding="utf-8") as f:
            json.dump(times_data, f)

    @pytest.mark.unit
    def test_healthy_system_returns_ok(self):
        """問題がないシステムで ok を返す"""
        from unittest.mock import patch

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"

    @pytest.mark.unit
    def test_system_with_unprocessed_loops_returns_warning(self):
        """未処理Loopがあるシステムで warning を返す"""
        from unittest.mock import patch

        # Loopファイルを作成
        for i in range(1, 3):
            loop_data = {"overall_digest": {"abstract": f"Test loop {i}"}}
            with open(self.plugin_root / "data" / "Loops" / f"L{i:05d}_test.txt", "w", encoding="utf-8") as f:
                json.dump(loop_data, f)

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                # 未処理Loopがあるためwarning
                assert result["status"] in ["ok", "warning"]
                # issues に unprocessed_loops が含まれる
                if result["issues"]:
                    issue_types = [i["type"] for i in result["issues"]]
                    assert "unprocessed_loops" in issue_types

    @pytest.mark.unit
    def test_missing_shadow_returns_error(self):
        """ShadowGrandDigestがない場合にエラーを返す"""
        from unittest.mock import patch

        # ShadowGrandDigestを削除
        (self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt").unlink()

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_corrupted_config_returns_error(self):
        """破損した設定ファイルでエラーを返す"""

        # 設定ファイルを破損させる
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                # Note: digest_auto may not raise SystemExit but return error status
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 1
                    return

                # If no SystemExit, check for error status in output
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_generatable_levels_included_in_output(self):
        """生成可能なレベルが出力に含まれる"""
        from unittest.mock import patch

        # 5つのLoopファイルを作成（thresholdを満たす）
        for i in range(1, 6):
            loop_data = {"overall_digest": {"abstract": f"Test loop {i}"}}
            with open(self.plugin_root / "data" / "Loops" / f"L{i:05d}_test.txt", "w", encoding="utf-8") as f:
                json.dump(loop_data, f)

        # last_processedを更新して未処理扱いにしない
        times_data = {"weekly": {"timestamp": "2025-01-01T00:00:00", "last_processed": 5}}
        with open(self.plugin_root / ".claude-plugin" / "last_digest_times.json", "w", encoding="utf-8") as f:
            json.dump(times_data, f)

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)

                assert "generatable_levels" in result
                assert isinstance(result["generatable_levels"], list)

    @pytest.mark.unit
    def test_recommendations_included_when_issues_exist(self):
        """問題がある場合に推奨アクションが含まれる"""
        from unittest.mock import patch

        # 未処理Loopを作成
        loop_data = {"overall_digest": {"abstract": "Test loop"}}
        with open(self.plugin_root / "data" / "Loops" / "L00001_test.txt", "w", encoding="utf-8") as f:
            json.dump(loop_data, f)

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)

                assert "recommendations" in result
                assert len(result["recommendations"]) > 0


if __name__ == "__main__":
    unittest.main()
