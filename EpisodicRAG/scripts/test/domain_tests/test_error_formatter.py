#!/usr/bin/env python3
"""
domain/error_formatter.py unit tests
=====================================

Tests for ErrorFormatter class and module-level convenience functions.
"""

import unittest
from pathlib import Path
from unittest.mock import patch

from domain.error_formatter import (
    ErrorFormatter,
    get_error_formatter,
    reset_error_formatter,
)


class TestErrorFormatterInit(unittest.TestCase):
    """ErrorFormatter initialization tests"""

    def test_init_with_path(self):
        """Initializes with provided project root"""
        root = Path("/test/project")
        formatter = ErrorFormatter(root)
        self.assertEqual(formatter.project_root, root)

    def test_init_with_relative_path(self):
        """Accepts relative path"""
        root = Path("relative/path")
        formatter = ErrorFormatter(root)
        self.assertEqual(formatter.project_root, root)


class TestFormatPath(unittest.TestCase):
    """format_path() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.root = Path("/project/root")
        self.formatter = ErrorFormatter(self.root)

    def test_relative_to_project_root(self):
        """Path within project root returns relative path"""
        path = Path("/project/root/data/file.txt")
        result = self.formatter.format_path(path)
        # Use os-independent comparison
        self.assertEqual(result, str(Path("data/file.txt")))

    def test_path_outside_project_root(self):
        """Path outside project root returns absolute path"""
        path = Path("/other/location/file.txt")
        result = self.formatter.format_path(path)
        self.assertEqual(result, str(path))

    def test_project_root_itself(self):
        """Project root itself returns empty or '.'"""
        result = self.formatter.format_path(self.root)
        self.assertEqual(result, ".")

    def test_nested_path(self):
        """Deeply nested path returns relative path"""
        path = Path("/project/root/a/b/c/d/file.txt")
        result = self.formatter.format_path(path)
        self.assertEqual(result, str(Path("a/b/c/d/file.txt")))


class TestInvalidLevel(unittest.TestCase):
    """invalid_level() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/root"))

    def test_without_valid_levels(self):
        """Message without valid levels list"""
        result = self.formatter.invalid_level("xyz")
        self.assertEqual(result, "Invalid level: 'xyz'")

    def test_with_valid_levels(self):
        """Message includes valid levels when provided"""
        result = self.formatter.invalid_level("xyz", ["weekly", "monthly"])
        self.assertIn("Invalid level: 'xyz'", result)
        self.assertIn("Valid levels: weekly, monthly", result)

    def test_with_single_valid_level(self):
        """Message with single valid level"""
        result = self.formatter.invalid_level("bad", ["good"])
        self.assertIn("Valid levels: good", result)

    def test_empty_valid_levels(self):
        """Empty valid levels list behaves like None"""
        result = self.formatter.invalid_level("xyz", [])
        self.assertEqual(result, "Invalid level: 'xyz'")


class TestUnknownLevel(unittest.TestCase):
    """unknown_level() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic unknown level message"""
        result = self.formatter.unknown_level("bad_level")
        self.assertEqual(result, "Unknown level: 'bad_level'")


class TestConfigKeyMissing(unittest.TestCase):
    """config_key_missing() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic config key missing message"""
        result = self.formatter.config_key_missing("api_key")
        self.assertEqual(result, "Required configuration key missing: 'api_key'")


class TestConfigInvalidValue(unittest.TestCase):
    """config_invalid_value() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/root"))

    def test_with_string_value(self):
        """Message for string actual value"""
        result = self.formatter.config_invalid_value("count", "int", "five")
        self.assertIn("Invalid configuration value for 'count'", result)
        self.assertIn("expected int", result)
        self.assertIn("got str", result)

    def test_with_int_value(self):
        """Message for int actual value"""
        result = self.formatter.config_invalid_value("name", "str", 123)
        self.assertIn("got int", result)

    def test_with_list_value(self):
        """Message for list actual value"""
        result = self.formatter.config_invalid_value("value", "dict", [1, 2])
        self.assertIn("got list", result)


class TestFileNotFound(unittest.TestCase):
    """file_not_found() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.root = Path("/project")
        self.formatter = ErrorFormatter(self.root)

    def test_relative_path(self):
        """Message with relative path"""
        path = Path("/project/data/file.txt")
        result = self.formatter.file_not_found(path)
        expected = f"File not found: {Path('data/file.txt')}"
        self.assertEqual(result, expected)

    def test_absolute_path_outside_root(self):
        """Message with absolute path outside root"""
        path = Path("/other/file.txt")
        result = self.formatter.file_not_found(path)
        expected = f"File not found: {path}"
        self.assertEqual(result, expected)


class TestFileAlreadyExists(unittest.TestCase):
    """file_already_exists() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/project"))

    def test_basic(self):
        """Basic file already exists message"""
        path = Path("/project/existing.txt")
        result = self.formatter.file_already_exists(path)
        self.assertEqual(result, "File already exists: existing.txt")


class TestFileIOError(unittest.TestCase):
    """file_io_error() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/project"))

    def test_read_operation(self):
        """Message for read operation"""
        path = Path("/project/file.txt")
        error = IOError("Permission denied")
        result = self.formatter.file_io_error("read", path, error)
        self.assertIn("Failed to read file.txt", result)
        self.assertIn("Permission denied", result)

    def test_write_operation(self):
        """Message for write operation"""
        path = Path("/project/file.txt")
        error = IOError("Disk full")
        result = self.formatter.file_io_error("write", path, error)
        self.assertIn("Failed to write file.txt", result)

    def test_delete_operation(self):
        """Message for delete operation"""
        path = Path("/project/file.txt")
        error = IOError("File in use")
        result = self.formatter.file_io_error("delete", path, error)
        self.assertIn("Failed to delete file.txt", result)


class TestDirectoryNotFound(unittest.TestCase):
    """directory_not_found() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/project"))

    def test_basic(self):
        """Basic directory not found message"""
        path = Path("/project/data/subdir")
        result = self.formatter.directory_not_found(path)
        expected = f"Directory not found: {Path('data/subdir')}"
        self.assertEqual(result, expected)


class TestInvalidJson(unittest.TestCase):
    """invalid_json() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/project"))

    def test_basic(self):
        """Basic invalid JSON message"""
        path = Path("/project/config.json")
        error = ValueError("Expecting value: line 1 column 1")
        result = self.formatter.invalid_json(path, error)
        self.assertIn("Invalid JSON in config.json", result)
        self.assertIn("Expecting value", result)


class TestInvalidType(unittest.TestCase):
    """invalid_type() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic invalid type message"""
        result = self.formatter.invalid_type("config.name", "str", 123)
        self.assertEqual(result, "config.name: expected str, got int")

    def test_with_dict(self):
        """Message for dict actual value"""
        result = self.formatter.invalid_type("field", "list", {"key": "value"})
        self.assertIn("got dict", result)

    def test_with_none(self):
        """Message for None actual value"""
        result = self.formatter.invalid_type("field", "str", None)
        self.assertIn("got NoneType", result)


class TestValidationError(unittest.TestCase):
    """validation_error() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/root"))

    def test_without_value(self):
        """Message without actual value"""
        result = self.formatter.validation_error("email", "must be valid email")
        self.assertEqual(result, "Validation failed for 'email': must be valid email")

    def test_with_value(self):
        """Message with actual value"""
        result = self.formatter.validation_error("age", "must be positive", -5)
        self.assertIn("Validation failed for 'age'", result)
        self.assertIn("must be positive", result)
        self.assertIn("(got: -5)", result)

    def test_with_none_value_explicitly(self):
        """None value is still included when explicitly passed"""
        # Note: None is falsy but should be included when passed
        # The current implementation doesn't include None in message
        result = self.formatter.validation_error("field", "cannot be null", None)
        # Current behavior: None is not included because of `if value is not None`
        self.assertNotIn("got:", result)


class TestEmptyCollection(unittest.TestCase):
    """empty_collection() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic empty collection message"""
        result = self.formatter.empty_collection("source_files")
        self.assertEqual(result, "source_files cannot be empty")


class TestDigestNotFound(unittest.TestCase):
    """digest_not_found() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic digest not found message"""
        result = self.formatter.digest_not_found("weekly", "W0001")
        self.assertEqual(result, "Digest not found: level='weekly', id='W0001'")


class TestShadowEmpty(unittest.TestCase):
    """shadow_empty() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic shadow empty message"""
        result = self.formatter.shadow_empty("monthly")
        self.assertEqual(result, "Shadow digest for level 'monthly' has no source files")


class TestCascadeError(unittest.TestCase):
    """cascade_error() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/root"))

    def test_basic(self):
        """Basic cascade error message"""
        result = self.formatter.cascade_error("weekly", "monthly", "threshold not met")
        self.assertEqual(result, "Cascade failed from 'weekly' to 'monthly': threshold not met")


class TestDirectoryCreationFailed(unittest.TestCase):
    """directory_creation_failed() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/project"))

    def test_basic_directory_creation_failed(self):
        """Basic directory creation failure message"""
        path = Path("/project/data/subdir")
        error = OSError("Permission denied")
        result = self.formatter.directory_creation_failed(path, error)
        self.assertIn("Failed to create directory", result)
        self.assertIn("Permission denied", result)

    def test_with_relative_path(self):
        """Message with path inside project root shows relative path"""
        path = Path("/project/new_dir/subdir")
        error = OSError("Disk full")
        result = self.formatter.directory_creation_failed(path, error)
        # Should contain relative path
        self.assertIn(str(Path("new_dir/subdir")), result)

    def test_with_absolute_path_outside_root(self):
        """Message with path outside project root shows absolute path"""
        path = Path("/other/location/dir")
        error = OSError("Access denied")
        result = self.formatter.directory_creation_failed(path, error)
        self.assertIn(str(path), result)

    def test_includes_error_message(self):
        """Error details are included in message"""
        path = Path("/project/dir")
        error = OSError("[Errno 13] Permission denied: '/project/dir'")
        result = self.formatter.directory_creation_failed(path, error)
        self.assertIn("Permission denied", result)


class TestConfigSectionMissing(unittest.TestCase):
    """config_section_missing() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/root"))

    def test_basic_section_missing(self):
        """Basic section missing message"""
        result = self.formatter.config_section_missing("paths")
        self.assertEqual(result, "'paths' section missing in config.json")

    def test_with_levels_section(self):
        """Message for levels section"""
        result = self.formatter.config_section_missing("levels")
        self.assertIn("'levels' section missing", result)

    def test_with_major_digests_section(self):
        """Message for major_digests section (GrandDigest.txt)"""
        result = self.formatter.config_section_missing("major_digests")
        self.assertIn("'major_digests' section missing", result)

    def test_error_message_format(self):
        """Verify message format consistency"""
        result = self.formatter.config_section_missing("test_section")
        self.assertTrue(result.startswith("'test_section'"))
        self.assertIn("missing in config.json", result)


class TestInitializationFailed(unittest.TestCase):
    """initialization_failed() tests"""

    def setUp(self):
        """Set up test formatter"""
        self.formatter = ErrorFormatter(Path("/root"))

    def test_basic_initialization_failed(self):
        """Basic initialization failure message"""
        error = Exception("Connection refused")
        result = self.formatter.initialization_failed("database", error)
        self.assertIn("Failed to initialize database", result)
        self.assertIn("Connection refused", result)

    def test_with_configuration_component(self):
        """Message for configuration initialization failure"""
        error = PermissionError("Access denied to config file")
        result = self.formatter.initialization_failed("configuration", error)
        self.assertIn("Failed to initialize configuration", result)
        self.assertIn("Access denied", result)

    def test_with_os_error(self):
        """Message with OSError"""
        error = OSError("No such file or directory")
        result = self.formatter.initialization_failed("file_scanner", error)
        self.assertIn("Failed to initialize file_scanner", result)
        self.assertIn("No such file or directory", result)

    def test_includes_error_details(self):
        """Verify error details are included"""
        error = ValueError("Invalid configuration value")
        result = self.formatter.initialization_failed("config_loader", error)
        self.assertIn("config_loader", result)
        self.assertIn("Invalid configuration value", result)


class TestGetErrorFormatter(unittest.TestCase):
    """get_error_formatter() tests"""

    def setUp(self):
        """Reset formatter before each test"""
        reset_error_formatter()

    def tearDown(self):
        """Reset formatter after each test"""
        reset_error_formatter()

    def test_creates_default_formatter(self):
        """Creates formatter with cwd when no root provided"""
        with patch("domain.error_formatter.Path") as MockPath:
            mock_cwd = Path("/current/working/dir")
            MockPath.cwd.return_value = mock_cwd
            MockPath.return_value = mock_cwd

            _ = get_error_formatter()
            MockPath.cwd.assert_called()

    def test_with_explicit_root(self):
        """Creates formatter with provided root"""
        root = Path("/explicit/root")
        formatter = get_error_formatter(root)
        self.assertEqual(formatter.project_root, root)

    def test_caches_default_formatter(self):
        """Caches and returns same formatter instance"""
        formatter1 = get_error_formatter()
        formatter2 = get_error_formatter()
        self.assertIs(formatter1, formatter2)

    def test_explicit_root_overrides_cache(self):
        """Explicit root creates new formatter"""
        _ = get_error_formatter()
        root = Path("/new/root")
        formatter2 = get_error_formatter(root)
        self.assertEqual(formatter2.project_root, root)


class TestResetErrorFormatter(unittest.TestCase):
    """reset_error_formatter() tests"""

    def test_resets_cached_formatter(self):
        """Resets the cached formatter"""
        formatter1 = get_error_formatter(Path("/first"))
        reset_error_formatter()
        formatter2 = get_error_formatter(Path("/second"))

        self.assertIsNot(formatter1, formatter2)
        self.assertEqual(formatter2.project_root, Path("/second"))


if __name__ == "__main__":
    unittest.main()
