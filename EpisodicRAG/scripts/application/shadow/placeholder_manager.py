#!/usr/bin/env python3
"""
Placeholder Manager
===================

PLACEHOLDER管理（更新・保持判定）
"""
from domain.constants import PLACEHOLDER_LIMITS, PLACEHOLDER_MARKER, PLACEHOLDER_END
from domain.types import OverallDigestData
from infrastructure import log_info


class PlaceholderManager:
    """PLACEHOLDERの管理クラス"""

    def update_or_preserve(
        self,
        overall_digest: OverallDigestData,
        total_files: int
    ) -> None:
        """
        PLACEHOLDERの更新または既存分析の保持

        Args:
            overall_digest: overall_digestデータ
            total_files: 総ファイル数
        """
        abstract = overall_digest.get("abstract", "")
        is_placeholder = (
            not abstract or
            (isinstance(abstract, str) and PLACEHOLDER_MARKER in abstract)
        )

        if is_placeholder:
            limits = PLACEHOLDER_LIMITS
            overall_digest["abstract"] = (
                f"{PLACEHOLDER_MARKER}: {total_files}ファイル分の全体統合分析 "
                f"({limits['abstract_chars']}文字程度){PLACEHOLDER_END}"
            )
            overall_digest["impression"] = (
                f"{PLACEHOLDER_MARKER}: 所感・展望 "
                f"({limits['impression_chars']}文字程度){PLACEHOLDER_END}"
            )
            overall_digest["keywords"] = [
                f"{PLACEHOLDER_MARKER}: keyword{i}{PLACEHOLDER_END}"
                for i in range(1, limits["keyword_count"] + 1)
            ]
            log_info(f"Initialized placeholder for {total_files} file(s)")
        else:
            log_info(f"Preserved existing analysis (now {total_files} file(s) total)")
            log_info(f"Claude should re-analyze all {total_files} files to integrate new content")
