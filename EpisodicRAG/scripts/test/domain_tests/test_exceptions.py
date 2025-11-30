#!/usr/bin/env python3
"""
domain/exceptions.py のユニットテスト
=====================================

カスタム例外クラスの構造と動作を検証。
- 例外階層の継承関係
- 各例外クラスのメッセージフォーマット
- 例外チェーン（from e）の動作確認
"""

from pathlib import Path

import pytest

from domain.exceptions import (
    ConfigError,
    CorruptedDataError,
    DiagnosticContext,
    DigestError,
    EpisodicRAGError,
    FileIOError,
    ValidationError,
)

# =============================================================================
# 例外階層テスト
# =============================================================================


class TestExceptionHierarchy:
    """例外階層の継承関係テスト"""

    @pytest.mark.unit
    def test_episodic_rag_error_inherits_from_exception(self):
        """EpisodicRAGError は Exception を継承"""
        assert issubclass(EpisodicRAGError, Exception)

    @pytest.mark.unit
    def test_config_error_inherits_from_episodic_rag_error(self):
        """ConfigError は EpisodicRAGError を継承"""
        assert issubclass(ConfigError, EpisodicRAGError)

    @pytest.mark.unit
    def test_digest_error_inherits_from_episodic_rag_error(self):
        """DigestError は EpisodicRAGError を継承"""
        assert issubclass(DigestError, EpisodicRAGError)

    @pytest.mark.unit
    def test_validation_error_inherits_from_episodic_rag_error(self):
        """ValidationError は EpisodicRAGError を継承"""
        assert issubclass(ValidationError, EpisodicRAGError)

    @pytest.mark.unit
    def test_file_io_error_inherits_from_episodic_rag_error(self):
        """FileIOError は EpisodicRAGError を継承"""
        assert issubclass(FileIOError, EpisodicRAGError)

    @pytest.mark.unit
    def test_corrupted_data_error_inherits_from_episodic_rag_error(self):
        """CorruptedDataError は EpisodicRAGError を継承"""
        assert issubclass(CorruptedDataError, EpisodicRAGError)


# =============================================================================
# EpisodicRAGError テスト
# =============================================================================


class TestEpisodicRAGError:
    """EpisodicRAGError のテスト"""

    @pytest.mark.unit
    def test_can_be_raised(self):
        """例外を発生させることができる"""
        with pytest.raises(EpisodicRAGError):
            raise EpisodicRAGError("Test error")

    @pytest.mark.unit
    def test_message_is_preserved(self):
        """エラーメッセージが保持される"""
        try:
            raise EpisodicRAGError("Test message")
        except EpisodicRAGError as e:
            assert str(e) == "Test message"

    @pytest.mark.unit
    def test_can_catch_all_subclasses(self):
        """すべてのサブクラスをキャッチできる"""
        errors = [
            ConfigError("config"),
            DigestError("digest"),
            ValidationError("validation"),
            FileIOError("fileio"),
            CorruptedDataError("corrupted"),
        ]
        for error in errors:
            with pytest.raises(EpisodicRAGError):
                raise error


# =============================================================================
# ConfigError テスト
# =============================================================================


class TestConfigError:
    """ConfigError のテスト"""

    @pytest.mark.unit
    def test_can_be_raised(self):
        """例外を発生させることができる"""
        with pytest.raises(ConfigError):
            raise ConfigError("Config not found")

    @pytest.mark.unit
    def test_message_is_preserved(self):
        """エラーメッセージが保持される"""
        try:
            raise ConfigError("Invalid config.json format")
        except ConfigError as e:
            assert "Invalid config.json format" in str(e)

    @pytest.mark.unit
    def test_can_be_caught_as_episodic_rag_error(self):
        """EpisodicRAGError としてキャッチできる"""
        with pytest.raises(EpisodicRAGError):
            raise ConfigError("Test")

    @pytest.mark.unit
    def test_unicode_message(self):
        """Unicode メッセージを扱える"""
        try:
            raise ConfigError("設定ファイルが見つかりません")
        except ConfigError as e:
            assert "設定ファイルが見つかりません" in str(e)


# =============================================================================
# DigestError テスト
# =============================================================================


class TestDigestError:
    """DigestError のテスト"""

    @pytest.mark.unit
    def test_can_be_raised(self):
        """例外を発生させることができる"""
        with pytest.raises(DigestError):
            raise DigestError("Digest generation failed")

    @pytest.mark.unit
    def test_message_is_preserved(self):
        """エラーメッセージが保持される"""
        try:
            raise DigestError("Shadow digest load failed")
        except DigestError as e:
            assert "Shadow digest load failed" in str(e)


# =============================================================================
# ValidationError テスト
# =============================================================================


class TestValidationError:
    """ValidationError のテスト"""

    @pytest.mark.unit
    def test_can_be_raised(self):
        """例外を発生させることができる"""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid data type")

    @pytest.mark.unit
    def test_message_is_preserved(self):
        """エラーメッセージが保持される"""
        try:
            raise ValidationError("source_files must be a list")
        except ValidationError as e:
            assert "source_files must be a list" in str(e)

    @pytest.mark.unit
    def test_can_include_context(self):
        """コンテキスト情報を含められる"""
        try:
            raise ValidationError("Expected dict, got list in 'overall_digest'")
        except ValidationError as e:
            assert "overall_digest" in str(e)


# =============================================================================
# FileIOError テスト
# =============================================================================


class TestFileIOError:
    """FileIOError のテスト"""

    @pytest.mark.unit
    def test_can_be_raised(self):
        """例外を発生させることができる"""
        with pytest.raises(FileIOError):
            raise FileIOError("File not found")

    @pytest.mark.unit
    def test_message_is_preserved(self):
        """エラーメッセージが保持される"""
        try:
            raise FileIOError("Cannot write to /path/to/file.json")
        except FileIOError as e:
            assert "Cannot write to" in str(e)

    @pytest.mark.unit
    def test_distinct_from_builtin_ioerror(self):
        """組み込みのIOErrorとは別"""
        # FileIOError は EpisodicRAGError を継承しているため、
        # 組み込みの IOError/OSError とは異なる
        try:
            raise FileIOError("Test")
        except IOError:
            pytest.fail("Should not be caught as IOError")
        except EpisodicRAGError:
            pass  # Expected


# =============================================================================
# CorruptedDataError テスト
# =============================================================================


class TestCorruptedDataError:
    """CorruptedDataError のテスト"""

    @pytest.mark.unit
    def test_can_be_raised(self):
        """例外を発生させることができる"""
        with pytest.raises(CorruptedDataError):
            raise CorruptedDataError("JSON file corrupted")

    @pytest.mark.unit
    def test_message_is_preserved(self):
        """エラーメッセージが保持される"""
        try:
            raise CorruptedDataError("Integrity check failed for GrandDigest.txt")
        except CorruptedDataError as e:
            assert "Integrity check failed" in str(e)


# =============================================================================
# 例外チェーンテスト
# =============================================================================


class TestExceptionChaining:
    """例外チェーン（from e）のテスト"""

    @pytest.mark.unit
    def test_config_error_chaining(self):
        """ConfigError で例外チェーンが機能する"""
        original = ValueError("Original error")
        try:
            try:
                raise original
            except ValueError as e:
                raise ConfigError("Config error") from e
        except ConfigError as e:
            assert e.__cause__ is original

    @pytest.mark.unit
    def test_file_io_error_chaining(self):
        """FileIOError で例外チェーンが機能する"""
        original = OSError("Permission denied")
        try:
            try:
                raise original
            except OSError as e:
                raise FileIOError(f"Cannot read file: {e}") from e
        except FileIOError as e:
            assert e.__cause__ is original

    @pytest.mark.unit
    def test_corrupted_data_error_chaining(self):
        """CorruptedDataError で例外チェーンが機能する"""
        import json

        original = json.JSONDecodeError("Expecting value", "", 0)
        try:
            try:
                raise original
            except json.JSONDecodeError as e:
                raise CorruptedDataError(f"Invalid JSON: {e}") from e
        except CorruptedDataError as e:
            assert e.__cause__ is original

    @pytest.mark.unit
    def test_chain_preserves_traceback(self):
        """例外チェーンでトレースバックが保持される"""
        import traceback

        try:
            try:
                raise ValueError("inner")
            except ValueError as e:
                raise ConfigError("outer") from e
        except ConfigError as e:
            tb = traceback.format_exception(type(e), e, e.__traceback__)
            tb_str = "".join(tb)
            assert "ValueError" in tb_str
            assert "inner" in tb_str
            assert "ConfigError" in tb_str
            assert "outer" in tb_str


# =============================================================================
# 実用パターンテスト
# =============================================================================


class TestPracticalUsagePatterns:
    """実用的な使用パターンのテスト"""

    @pytest.mark.unit
    def test_selective_catch(self):
        """特定の例外を選択的にキャッチ"""
        caught = []

        def raise_various_errors(error_type: str):
            if error_type == "config":
                raise ConfigError("config")
            elif error_type == "digest":
                raise DigestError("digest")
            elif error_type == "validation":
                raise ValidationError("validation")

        for error_type in ["config", "digest", "validation"]:
            try:
                raise_various_errors(error_type)
            except ConfigError:
                caught.append("config")
            except DigestError:
                caught.append("digest")
            except ValidationError:
                caught.append("validation")

        assert caught == ["config", "digest", "validation"]

    @pytest.mark.unit
    def test_catch_all_episodic_rag_errors(self):
        """すべてのEpisodicRAGエラーを一括キャッチ"""
        errors = [
            ConfigError("1"),
            DigestError("2"),
            ValidationError("3"),
            FileIOError("4"),
            CorruptedDataError("5"),
        ]

        caught_count = 0
        for error in errors:
            try:
                raise error
            except EpisodicRAGError:
                caught_count += 1

        assert caught_count == 5

    @pytest.mark.unit
    def test_error_message_formatting(self):
        """エラーメッセージのフォーマット"""
        # ファイルパスを含むエラー
        file_error = FileIOError("Cannot read file: /path/to/config.json")
        assert "/path/to/config.json" in str(file_error)

        # 型情報を含むエラー
        type_error = ValidationError("Expected dict, got <class 'list'>")
        assert "dict" in str(type_error)
        assert "list" in str(type_error)

        # コンテキスト情報を含むエラー
        context_error = ConfigError("Missing required key 'base_dir' in config.json")
        assert "base_dir" in str(context_error)


# =============================================================================
# DiagnosticContext テスト
# =============================================================================


class TestDiagnosticContext:
    """DiagnosticContext のテスト"""

    @pytest.mark.unit
    def test_to_dict_all_fields(self):
        """全フィールドを設定した場合のto_dict"""
        test_path = Path("/path/to/config.json")
        ctx = DiagnosticContext(
            config_path=test_path,
            current_level="weekly",
            file_count=3,
            threshold=5,
            last_operation="add_files_to_shadow",
            additional_info={"extra": "data"},
        )
        result = ctx.to_dict()

        # Pathは文字列に変換されるが、OS依存のセパレータを使用
        assert result["config_path"] == str(test_path)
        assert result["current_level"] == "weekly"
        assert result["file_count"] == 3
        assert result["threshold"] == 5
        assert result["last_operation"] == "add_files_to_shadow"
        assert result["extra"] == "data"

    @pytest.mark.unit
    def test_to_dict_partial_fields(self):
        """一部フィールドのみ設定した場合のto_dict"""
        ctx = DiagnosticContext(
            current_level="monthly",
            file_count=10,
        )
        result = ctx.to_dict()

        assert "current_level" in result
        assert "file_count" in result
        assert "config_path" not in result
        assert "threshold" not in result
        assert "last_operation" not in result

    @pytest.mark.unit
    def test_to_dict_empty(self):
        """空のコンテキストのto_dict"""
        ctx = DiagnosticContext()
        result = ctx.to_dict()
        assert result == {}

    @pytest.mark.unit
    def test_str_representation(self):
        """__str__の文字列表現"""
        ctx = DiagnosticContext(
            current_level="weekly",
            file_count=3,
            threshold=5,
        )
        result = str(ctx)

        assert "current_level=weekly" in result
        assert "file_count=3" in result
        assert "threshold=5" in result

    @pytest.mark.unit
    def test_str_empty_context(self):
        """空のコンテキストの__str__"""
        ctx = DiagnosticContext()
        assert str(ctx) == ""

    @pytest.mark.unit
    def test_additional_info_merged(self):
        """additional_infoがto_dictにマージされる"""
        ctx = DiagnosticContext(
            current_level="weekly",
            additional_info={"key1": "value1", "key2": 42},
        )
        result = ctx.to_dict()

        assert result["current_level"] == "weekly"
        assert result["key1"] == "value1"
        assert result["key2"] == 42


# =============================================================================
# EpisodicRAGError コンテキスト付きテスト
# =============================================================================


class TestEpisodicRAGErrorWithContext:
    """EpisodicRAGError のコンテキスト付きテスト"""

    @pytest.mark.unit
    def test_str_with_context(self):
        """コンテキスト付きエラーの__str__"""
        ctx = DiagnosticContext(
            current_level="weekly",
            file_count=3,
        )
        error = EpisodicRAGError("Processing failed", context=ctx)
        result = str(error)

        assert "Processing failed" in result
        assert "[Context:" in result
        assert "current_level=weekly" in result
        assert "file_count=3" in result

    @pytest.mark.unit
    def test_str_without_context(self):
        """コンテキストなしエラーの__str__"""
        error = EpisodicRAGError("Simple error")
        result = str(error)

        assert result == "Simple error"
        assert "[Context:" not in result

    @pytest.mark.unit
    def test_str_with_empty_context(self):
        """空のコンテキストを持つエラーの__str__"""
        ctx = DiagnosticContext()
        error = EpisodicRAGError("Error with empty context", context=ctx)
        result = str(error)

        # 空のコンテキストは表示されない
        assert result == "Error with empty context"

    @pytest.mark.unit
    def test_context_attribute_accessible(self):
        """context属性にアクセスできる"""
        ctx = DiagnosticContext(current_level="monthly")
        error = EpisodicRAGError("Error", context=ctx)

        assert error.context is ctx
        assert error.context.current_level == "monthly"

    @pytest.mark.unit
    def test_subclass_with_context(self):
        """サブクラスでもコンテキストが機能する"""
        ctx = DiagnosticContext(
            current_level="weekly",
            threshold=5,
        )
        error = DigestError("Digest processing failed", context=ctx)
        result = str(error)

        assert "Digest processing failed" in result
        assert "current_level=weekly" in result
        assert "threshold=5" in result

    @pytest.mark.unit
    def test_context_with_path(self):
        """Pathを含むコンテキスト"""
        test_path = Path("/home/user/config.json")
        ctx = DiagnosticContext(
            config_path=test_path,
        )
        error = ConfigError("Config error", context=ctx)
        result = str(error)

        # OS依存のパス形式を考慮
        assert f"config_path={test_path}" in result
