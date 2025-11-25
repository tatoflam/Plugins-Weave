#!/usr/bin/env python3
"""
config.py のユニットテスト
==========================

extract_file_number() と extract_number_only() のテスト
"""
import sys
import unittest
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import extract_file_number, extract_number_only


class TestExtractFileNumber(unittest.TestCase):
    """extract_file_number() のテスト"""

    def test_loop_prefix(self):
        """Loopプレフィックス"""
        self.assertEqual(extract_file_number("Loop0001_タイトル.txt"), ("Loop", 1))
        self.assertEqual(extract_file_number("Loop0186_xxx.txt"), ("Loop", 186))

    def test_weekly_prefix(self):
        """Wプレフィックス（Weekly）"""
        self.assertEqual(extract_file_number("W0001_タイトル.txt"), ("W", 1))
        self.assertEqual(extract_file_number("W0047_xxx.txt"), ("W", 47))

    def test_monthly_prefix(self):
        """Mプレフィックス（Monthly）"""
        self.assertEqual(extract_file_number("M001_タイトル.txt"), ("M", 1))
        self.assertEqual(extract_file_number("M012_xxx.txt"), ("M", 12))

    def test_multi_decadal_prefix(self):
        """MDプレフィックス（Multi-decadal）- 2文字プレフィックスのテスト"""
        self.assertEqual(extract_file_number("MD01_タイトル.txt"), ("MD", 1))
        self.assertEqual(extract_file_number("MD03_xxx.txt"), ("MD", 3))

    def test_other_prefixes(self):
        """その他のプレフィックス（Q, A, T, D, C）"""
        self.assertEqual(extract_file_number("Q001_タイトル.txt"), ("Q", 1))
        self.assertEqual(extract_file_number("A01_タイトル.txt"), ("A", 1))
        self.assertEqual(extract_file_number("T01_タイトル.txt"), ("T", 1))
        self.assertEqual(extract_file_number("D01_タイトル.txt"), ("D", 1))
        self.assertEqual(extract_file_number("C01_タイトル.txt"), ("C", 1))

    def test_invalid_format(self):
        """無効な形式"""
        self.assertIsNone(extract_file_number("invalid.txt"))
        self.assertIsNone(extract_file_number(""))
        self.assertIsNone(extract_file_number("no_number.txt"))


class TestExtractNumberOnly(unittest.TestCase):
    """extract_number_only() のテスト"""

    def test_returns_number(self):
        """番号のみ返す"""
        self.assertEqual(extract_number_only("Loop0001_xxx.txt"), 1)
        self.assertEqual(extract_number_only("MD03_xxx.txt"), 3)

    def test_invalid_returns_none(self):
        """無効な形式はNone"""
        self.assertIsNone(extract_number_only("invalid.txt"))


if __name__ == "__main__":
    unittest.main()
