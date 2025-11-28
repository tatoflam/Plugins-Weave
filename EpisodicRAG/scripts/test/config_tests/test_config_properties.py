#!/usr/bin/env python3
"""
設定Property-Based Tests
========================

設定（DigestConfig）の不変条件をHypothesisで検証。

不変条件:
    - 設定の読み込み→保存→読み込みでデータが保持される
    - 全レベルの閾値は正の整数
    - パス解決は絶対パスを返す
    - 設定構造は型安全
"""

import json
import tempfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from domain.constants import LEVEL_CONFIG, LEVEL_NAMES

# Property-Based Test マーカー
pytestmark = pytest.mark.property

# =============================================================================
# Strategies
# =============================================================================

# 有効なレベル名
valid_levels = st.sampled_from(LEVEL_NAMES)

# 有効なパス文字列（英数字とアンダースコア、ハイフン、スラッシュ）
valid_path_chars = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N"),
        whitelist_characters="_-/",
    ),
    min_size=1,
    max_size=50,
)

# 有効な閾値
valid_thresholds = st.integers(min_value=1, max_value=100)

# 有効な設定辞書
valid_config_dicts = st.fixed_dictionaries(
    {
        "base_dir": st.just("."),
        "paths": st.fixed_dictionaries(
            {
                "loops": st.just("data/Loops"),
                "digests": st.just("data/Digests"),
                "essences": st.just("data/Essences"),
            }
        ),
    }
)


# =============================================================================
# Config Loading Invariants
# =============================================================================


class TestConfigLoadingInvariants:
    """設定読み込みの不変条件"""

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_level_config_consistency(self, level):
        """
        LEVEL_CONFIGは一貫した構造を持つ
        """
        config = LEVEL_CONFIG[level]

        # 必須キーの存在
        assert "prefix" in config
        assert "digits" in config
        assert "dir_name" in config

        # 型の一貫性
        assert isinstance(config["prefix"], str)
        assert isinstance(config["digits"], int)
        assert isinstance(config["dir_name"], str)

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_dir_name_format(self, level):
        """
        dir_nameは "N_LevelName" 形式である
        """
        config = LEVEL_CONFIG[level]
        dir_name = config["dir_name"]

        # 数字_名前 の形式
        parts = dir_name.split("_", 1)
        assert len(parts) == 2, f"dir_nameは'N_Name'形式であること: {dir_name}"
        assert parts[0].isdigit(), f"dir_nameの先頭は数字であること: {dir_name}"


# =============================================================================
# Threshold Invariants
# =============================================================================


class TestConfigThresholdInvariants:
    """設定閾値の不変条件"""

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_threshold_from_level_config(self, level):
        """
        LEVEL_CONFIGから取得した閾値は妥当な値である
        """
        config = LEVEL_CONFIG[level]
        threshold = config.get("threshold", 5)  # デフォルト5

        assert threshold > 0, "閾値は正であること"
        assert threshold <= 100, "閾値は妥当な範囲内であること"

    @given(level=valid_levels)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_threshold_consistency_with_digest_config(self, level, temp_plugin_env):
        """
        DigestConfigとLEVEL_CONFIGの閾値が一致する
        """
        from config import DigestConfig

        digest_config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        level_config_threshold = LEVEL_CONFIG[level].get("threshold", 5)
        attr_name = f"{level.replace('-', '_')}_threshold"
        digest_config_threshold = getattr(digest_config, attr_name, 5)

        assert level_config_threshold == digest_config_threshold, (
            f"{level}の閾値がLEVEL_CONFIGとDigestConfigで一致すること"
        )


# =============================================================================
# Path Resolution Invariants
# =============================================================================


class TestPathResolutionInvariants:
    """パス解決の不変条件"""

    @given(level=valid_levels)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_level_dir_returns_absolute_path(self, level, temp_plugin_env):
        """
        get_level_dir()は絶対パスを返す
        """
        from config import DigestConfig

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        level_dir = config.get_level_dir(level)

        assert level_dir.is_absolute(), f"{level}のディレクトリは絶対パスであること"

    @given(level=valid_levels)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_level_dir_contains_level_name(self, level, temp_plugin_env):
        """
        get_level_dir()のパスにレベル関連の名前が含まれる
        """
        from config import DigestConfig

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        level_dir = config.get_level_dir(level)

        # パスにdir_nameが含まれる
        expected_dir_name = LEVEL_CONFIG[level]["dir_name"]
        assert expected_dir_name in str(level_dir), (
            f"{level}のディレクトリパスに{expected_dir_name}が含まれること"
        )


# =============================================================================
# Config Structure Invariants
# =============================================================================


class TestConfigStructureInvariants:
    """設定構造の不変条件"""

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_level_config_prefix_uniqueness(self, level):
        """
        各レベルのプレフィックスは一意である
        """
        prefixes = [LEVEL_CONFIG[l]["prefix"] for l in LEVEL_NAMES]
        # 注意: "L" は loop 用に予約されているが LEVEL_NAMES には含まれない
        assert len(prefixes) == len(set(prefixes)), "プレフィックスは一意であること"

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_level_config_dir_name_uniqueness(self, level):
        """
        各レベルのdir_nameは一意である
        """
        dir_names = [LEVEL_CONFIG[l]["dir_name"] for l in LEVEL_NAMES]
        assert len(dir_names) == len(set(dir_names)), "dir_nameは一意であること"

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_level_config_dir_name_ordering(self, level):
        """
        dir_nameの番号は階層順序と一致する
        """
        config = LEVEL_CONFIG[level]
        dir_name = config["dir_name"]

        # 番号を抽出
        dir_number = int(dir_name.split("_")[0])
        level_index = LEVEL_NAMES.index(level)

        # 番号は1から始まり、レベルインデックス+1と一致
        assert dir_number == level_index + 1, (
            f"{level}のdir_name番号は{level_index + 1}であること（実際: {dir_number}）"
        )


# =============================================================================
# JSON Roundtrip Invariants
# =============================================================================


class TestJSONRoundtripInvariants:
    """JSON読み書きの不変条件"""

    @given(config_data=valid_config_dicts)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_config_json_roundtrip(self, config_data):
        """
        設定JSONの書き込み→読み込みで内容が保持される
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(config_data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            assert loaded == config_data, "JSONラウンドトリップで内容が保持されること"
        finally:
            Path(temp_path).unlink()

    @given(
        threshold=valid_thresholds,
        level=valid_levels,
    )
    @settings(max_examples=50)
    def test_threshold_json_serializable(self, threshold, level):
        """
        閾値はJSON形式で保存可能である
        """
        data = {f"{level}_threshold": threshold}
        json_str = json.dumps(data)
        loaded = json.loads(json_str)

        assert loaded[f"{level}_threshold"] == threshold


# =============================================================================
# Fixture for temp_plugin_env
# =============================================================================


@pytest.fixture
def temp_plugin_env():
    """
    テスト用の一時プラグイン環境を提供
    """
    from test_helpers import TempPluginEnvironment

    with TempPluginEnvironment() as env:
        yield env
