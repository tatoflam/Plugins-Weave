#!/usr/bin/env python3
"""
file_detector DEBUGログのテスト
================================

FileDetectorのDEBUGレベルトレースが正しく出力されることを検証。

Usage:
    pytest scripts/test/application_tests/shadow/test_file_detector_logging.py -v
"""

import logging
from typing import TYPE_CHECKING

import pytest

from domain.constants import LOG_PREFIX_DECISION, LOG_PREFIX_FILE, LOG_PREFIX_STATE

if TYPE_CHECKING:
    from application.shadow import FileDetector


class TestFileDetectorLogging:
    """FileDetectorのDEBUGログ出力テスト"""

    @pytest.mark.unit
    def test_logs_find_new_files_start(
        self, file_detector: "FileDetector", caplog: pytest.LogCaptureFixture
    ) -> None:
        """find_new_files開始時にログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            file_detector.find_new_files("weekly")

        assert LOG_PREFIX_STATE in caplog.text
        assert "find_new_files" in caplog.text
        assert "weekly" in caplog.text

    @pytest.mark.unit
    def test_logs_detection_criteria(
        self, file_detector: "FileDetector", caplog: pytest.LogCaptureFixture
    ) -> None:
        """検出条件（detection_level, max_num）をログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            file_detector.find_new_files("weekly")

        assert LOG_PREFIX_DECISION in caplog.text
        assert "detection_level" in caplog.text

    @pytest.mark.unit
    def test_logs_detection_result(
        self, file_detector: "FileDetector", caplog: pytest.LogCaptureFixture
    ) -> None:
        """検出結果をログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            file_detector.find_new_files("weekly")

        assert LOG_PREFIX_FILE in caplog.text
        assert "found" in caplog.text

    @pytest.mark.unit
    def test_not_shown_at_info_level(
        self, file_detector: "FileDetector", caplog: pytest.LogCaptureFixture
    ) -> None:
        """INFOレベルではDEBUGログは表示されない"""
        with caplog.at_level(logging.INFO, logger="episodic_rag"):
            file_detector.find_new_files("weekly")

        assert LOG_PREFIX_STATE not in caplog.text

    @pytest.mark.unit
    def test_logs_max_file_number(
        self, file_detector: "FileDetector", caplog: pytest.LogCaptureFixture
    ) -> None:
        """max_numがログに含まれる"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            file_detector.find_new_files("weekly")

        assert "max_num" in caplog.text
