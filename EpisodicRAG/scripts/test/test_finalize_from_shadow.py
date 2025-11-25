#!/usr/bin/env python3
"""
DigestFinalizerFromShadow 統合テスト
=====================================

一時ディレクトリを使用したファイルI/Oテスト
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from finalize_from_shadow import DigestFinalizerFromShadow
from utils import get_next_digest_number


class TestGetNextDigestNumber(unittest.TestCase):
    """get_next_digest_number関数のテスト"""

    def setUp(self):
        """一時ディレクトリでテスト環境を構築"""
        self.temp_dir = tempfile.mkdtemp()
        self.digests_path = Path(self.temp_dir) / "Digests"
        self.digests_path.mkdir()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir)

    def test_empty_directory_returns_1(self):
        """空のディレクトリでは1を返す"""
        result = get_next_digest_number(self.digests_path, "weekly")
        self.assertEqual(result, 1)

    def test_nonexistent_directory_returns_1(self):
        """存在しないディレクトリでは1を返す"""
        nonexistent = Path(self.temp_dir) / "NonExistent"
        result = get_next_digest_number(nonexistent, "weekly")
        self.assertEqual(result, 1)

    def test_with_existing_files(self):
        """既存ファイルがある場合、最大番号+1を返す"""
        weekly_dir = self.digests_path / "1_Weekly"
        weekly_dir.mkdir()

        (weekly_dir / "W0001_test.txt").write_text("{}")
        (weekly_dir / "W0003_test.txt").write_text("{}")
        (weekly_dir / "W0005_test.txt").write_text("{}")

        result = get_next_digest_number(self.digests_path, "weekly")
        self.assertEqual(result, 6)

    def test_invalid_level_raises(self):
        """無効なレベルでValueError"""
        with self.assertRaises(ValueError):
            get_next_digest_number(self.digests_path, "invalid_level")


class TestDigestFinalizerFromShadow(unittest.TestCase):
    """DigestFinalizerFromShadow の統合テスト"""

    def setUp(self):
        """一時ディレクトリでテスト環境を構築"""
        self.temp_dir = tempfile.mkdtemp()
        self.digests_path = Path(self.temp_dir) / "Digests"
        self.loops_path = Path(self.temp_dir) / "Loops"
        self.essences_path = Path(self.temp_dir) / "Essences"

        self.digests_path.mkdir()
        self.loops_path.mkdir()
        self.essences_path.mkdir()

        # モック設定
        self.mock_config = MagicMock()
        self.mock_config.digests_path = self.digests_path
        self.mock_config.loops_path = self.loops_path
        self.mock_config.essences_path = self.essences_path

        self.finalizer = DigestFinalizerFromShadow(self.mock_config)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir)

    def test_validate_shadow_content_valid(self):
        """正常なsource_filesの検証"""
        source_files = ["Loop0001_test.txt", "Loop0002_test.txt"]
        result = self.finalizer.validate_shadow_content("weekly", source_files)
        self.assertTrue(result)

    def test_validate_shadow_content_empty(self):
        """空のsource_filesでFalse"""
        result = self.finalizer.validate_shadow_content("weekly", [])
        self.assertFalse(result)

    def test_validate_shadow_content_not_list(self):
        """リストでない場合False"""
        result = self.finalizer.validate_shadow_content("weekly", "not a list")
        self.assertFalse(result)

    def test_validate_shadow_content_invalid_filename(self):
        """無効なファイル名形式でFalse"""
        source_files = ["invalid_file.txt"]
        result = self.finalizer.validate_shadow_content("weekly", source_files)
        self.assertFalse(result)

    def test_finalize_empty_title(self):
        """空タイトルでFalse"""
        result = self.finalizer.finalize_from_shadow("weekly", "")
        self.assertFalse(result)

    def test_finalize_no_shadow(self):
        """Shadowがない場合False"""
        result = self.finalizer.finalize_from_shadow("weekly", "Test Title")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
