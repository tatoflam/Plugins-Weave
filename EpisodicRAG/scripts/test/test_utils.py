#!/usr/bin/env python3
"""
utils.py のユニットテスト
=========================

sanitize_filename() のテスト
"""
import sys
import unittest
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import sanitize_filename


class TestSanitizeFilename(unittest.TestCase):
    """sanitize_filename() のテスト"""

    def test_basic(self):
        """基本的な変換"""
        self.assertEqual(sanitize_filename("テスト"), "テスト")
        self.assertEqual(sanitize_filename("Hello World"), "Hello_World")

    def test_dangerous_chars(self):
        """危険な文字の削除"""
        self.assertEqual(sanitize_filename("test<>:\"/\\|?*"), "test")
        self.assertEqual(sanitize_filename("file:name"), "filename")

    def test_spaces_to_underscore(self):
        """空白をアンダースコアに変換"""
        self.assertEqual(sanitize_filename("a b c"), "a_b_c")
        self.assertEqual(sanitize_filename("a  b"), "a_b")  # 連続空白

    def test_strip_underscores(self):
        """先頭・末尾のアンダースコア削除"""
        self.assertEqual(sanitize_filename(" test "), "test")
        self.assertEqual(sanitize_filename("_test_"), "test")

    def test_max_length(self):
        """長さ制限"""
        long_title = "a" * 100
        result = sanitize_filename(long_title, max_length=50)
        self.assertEqual(len(result), 50)

    def test_max_length_no_trailing_underscore(self):
        """長さ制限後に末尾アンダースコアなし"""
        # 50文字目がアンダースコアになるケース
        result = sanitize_filename("a" * 49 + " b", max_length=50)
        self.assertFalse(result.endswith("_"))

    def test_japanese(self):
        """日本語タイトル"""
        self.assertEqual(sanitize_filename("AIとの対話"), "AIとの対話")
        self.assertEqual(sanitize_filename("テスト 2025"), "テスト_2025")


if __name__ == "__main__":
    unittest.main()
