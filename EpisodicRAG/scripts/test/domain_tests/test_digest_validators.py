#!/usr/bin/env python3
"""
Digest Validators Tests
=======================

domain.validators.digest_validators のテスト
"""

import pytest

from domain.validators import is_valid_overall_digest


class TestIsValidOverallDigest:
    """is_valid_overall_digest のテスト"""

    # ==========================================================================
    # 基本的な有効ケース
    # ==========================================================================

    def test_valid_digest_with_files_returns_true(self) -> None:
        """有効なダイジェスト（ファイルあり）はTrueを返す"""
        digest = {"source_files": ["file1.txt", "file2.txt"]}
        assert is_valid_overall_digest(digest) is True

    def test_valid_digest_with_single_file_returns_true(self) -> None:
        """有効なダイジェスト（ファイル1つ）はTrueを返す"""
        digest = {"source_files": ["single.txt"]}
        assert is_valid_overall_digest(digest) is True

    def test_valid_digest_with_additional_fields_returns_true(self) -> None:
        """追加フィールドがあっても有効"""
        digest = {
            "source_files": ["file.txt"],
            "keywords": ["keyword1", "keyword2"],
            "abstract": "This is an abstract.",
            "impression": "This is an impression.",
        }
        assert is_valid_overall_digest(digest) is True

    # ==========================================================================
    # require_non_empty=True (デフォルト) のケース
    # ==========================================================================

    def test_empty_source_files_returns_false_by_default(self) -> None:
        """空のsource_filesはデフォルトでFalseを返す"""
        digest = {"source_files": []}
        assert is_valid_overall_digest(digest) is False

    def test_empty_source_files_with_require_non_empty_true_returns_false(self) -> None:
        """空のsource_filesはrequire_non_empty=TrueでFalseを返す"""
        digest = {"source_files": []}
        assert is_valid_overall_digest(digest, require_non_empty=True) is False

    # ==========================================================================
    # require_non_empty=False のケース
    # ==========================================================================

    def test_empty_source_files_with_require_non_empty_false_returns_true(self) -> None:
        """空のsource_filesはrequire_non_empty=FalseでTrueを返す"""
        digest = {"source_files": []}
        assert is_valid_overall_digest(digest, require_non_empty=False) is True

    def test_valid_digest_with_require_non_empty_false_returns_true(self) -> None:
        """有効なダイジェストはrequire_non_empty=FalseでもTrueを返す"""
        digest = {"source_files": ["file.txt"]}
        assert is_valid_overall_digest(digest, require_non_empty=False) is True

    # ==========================================================================
    # 無効なケース（型が不正）
    # ==========================================================================

    def test_none_returns_false(self) -> None:
        """NoneはFalseを返す"""
        assert is_valid_overall_digest(None) is False

    def test_string_returns_false(self) -> None:
        """文字列はFalseを返す"""
        assert is_valid_overall_digest("not a dict") is False

    def test_list_returns_false(self) -> None:
        """リストはFalseを返す"""
        assert is_valid_overall_digest(["source_files"]) is False

    def test_int_returns_false(self) -> None:
        """整数はFalseを返す"""
        assert is_valid_overall_digest(42) is False

    def test_empty_dict_returns_false(self) -> None:
        """空のdictはFalseを返す（source_filesキーがない）"""
        assert is_valid_overall_digest({}) is False

    # ==========================================================================
    # 無効なケース（キーが不正）
    # ==========================================================================

    def test_missing_source_files_key_returns_false(self) -> None:
        """source_filesキーがないとFalseを返す"""
        digest = {"keywords": ["keyword1"]}
        assert is_valid_overall_digest(digest) is False

    def test_source_files_not_a_list_returns_false_with_require_non_empty(self) -> None:
        """source_filesがリストでなくてもbool評価される（require_non_empty=True）"""
        # Pythonでは空文字列はfalsyなのでFalse
        digest = {"source_files": ""}
        assert is_valid_overall_digest(digest) is False

    def test_source_files_string_returns_true_with_require_non_empty(self) -> None:
        """source_filesが非空文字列だとtruthyなのでTrue（require_non_empty=True）"""
        # Pythonでは非空文字列はtruthyなのでTrue
        digest = {"source_files": "file.txt"}
        assert is_valid_overall_digest(digest) is True

    def test_source_files_none_returns_false(self) -> None:
        """source_filesがNoneだとFalse（require_non_empty=True）"""
        digest = {"source_files": None}
        assert is_valid_overall_digest(digest) is False

    # ==========================================================================
    # TypeGuard 型推論テスト
    # ==========================================================================

    def test_type_narrowing_works(self) -> None:
        """TypeGuardにより型が絞り込まれる"""
        digest: object = {"source_files": ["file.txt"]}
        if is_valid_overall_digest(digest):
            # このブロック内では digest は OverallDigestData として型推論される
            # source_files にアクセスできることを確認
            assert len(digest["source_files"]) == 1
