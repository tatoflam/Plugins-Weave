# エラーリカバリーパターン

EpisodicRAGプラグインで使用されているエラーハンドリングと
リカバリーパターンのリファレンスドキュメント。

> **対象読者**: AIエージェント（Claude Code）、人間開発者
> **想定ユースケース**: エラーハンドリング実装時のパターン参照、既存実装の理解

## このドキュメントの目的

1. **既存実装パターンの説明**: EpisodicRAGで採用されているエラー処理の実装例
2. **ベストプラクティスの提示**: 新規実装時に参考となる推奨パターン
3. **テストケースとの対応**: 各パターンに対応するテストケースの参照

---

## 目次

**基本エラーパターン**
- [1. ファイル権限エラー](#1-ファイル権限エラー)
- [2. ディスク容量エラー](#2-ディスク容量エラー)
- [3. JSON破損・フォーマットエラー](#3-json破損フォーマットエラー)
- [4. ファイル存在エラー](#4-ファイル存在エラー)
- [5. エンコーディングエラー](#5-エンコーディングエラー)
- [6. 同時アクセスエラー](#6-同時アクセスエラー)
- [7. 境界値・エッジケース](#7-境界値エッジケース)

**実装リファレンス**
- [8. JSON読み込み関数の使い分け](#8-json読み込み関数の使い分け)
- [9. Strategy / Chain of Responsibility パターン](#9-strategy--chain-of-responsibility-パターン)
- [10. スキル CLI のエラー処理パターン](#10-スキル-cli-のエラー処理パターン)

**システム構造**
- [11. 外部パスアクセス制御](#11-外部パスアクセス制御)
- [12. 例外階層](#12-例外階層)
- [13. 参照](#13-参照)

---

## 概要

このドキュメントでは、`infrastructure/json_repository/`パッケージおよび
関連テスト（`test_error_recovery.py`）で実装されているエラー処理パターンを解説します。

---

## 1. ファイル権限エラー

### パターン

```python
try:
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
except IOError as e:
    raise FileIOError(f"Failed to write {file_path}: {e}") from e
```

### 対応するテスト

- `test_save_json_permission_denied` - 読み取り専用ファイルへの書き込み
- `test_load_json_permission_denied` - アクセス権限なしファイルの読み込み
- `test_save_json_directory_not_writable` - 書き込み不可ディレクトリ

### ベストプラクティス

- `PermissionError`を`FileIOError`にラップして一貫したエラー階層を維持
- Windows/Unix間の権限モデルの違いを考慮（テストでは`skipif`を使用）

---

## 2. ディスク容量エラー

### パターン

```python
# OSError 28 = ENOSPC (No space left on device)
try:
    save_json(file_path, data)
except OSError as e:
    if e.errno == 28:
        # ディスク容量不足の処理
        raise FileIOError(f"Disk full: {e}") from e
```

### 対応するテスト

- `test_save_json_disk_full_simulation` - ディスク容量不足シミュレーション
- `test_save_json_io_error_simulation` - 一般的なI/Oエラー

### ベストプラクティス

- 本番環境では事前にディスク容量をチェック
- 大容量データの書き込み前に一時ファイルを使用

---

## 3. JSON破損・フォーマットエラー

### パターン

```python
def safe_read_json(file_path: Path, raise_on_error: bool = True) -> Optional[Dict[str, Any]]:
    """JSONファイルを安全に読み込む共通ヘルパー"""
    formatter = get_error_formatter()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        if raise_on_error:
            raise FileIOError(formatter.file.invalid_json(file_path, e)) from e
        return None
    except IOError as e:
        if raise_on_error:
            raise FileIOError(formatter.file.file_io_error("read", file_path, e)) from e
        return None
```

### 対応するテスト

- `test_load_json_invalid_json` - 不正なJSON構文
- `test_load_json_empty_file` - 空ファイル
- `test_load_json_truncated` - 途中で切れたJSON
- `test_load_json_binary_content` - バイナリコンテンツ

### ベストプラクティス

- `json.JSONDecodeError`を明示的にキャッチ
- エラーメッセージにファイルパスと元のエラーを含める
- バッチ処理では`raise_on_error=False`でスキップ可能に

---

## 4. ファイル存在エラー

### パターン

```python
def load_json(file_path: Path) -> Dict[str, Any]:
    if not file_path.exists():
        raise FileIOError(f"File not found: {file_path}")
    # ...
```

### 対応するテスト

- `test_load_json_nonexistent` - 存在しないファイル
- `test_load_json_directory_instead_of_file` - ディレクトリをファイルとして指定

### ベストプラクティス

- ファイル操作前に`exists()`チェック
- 明確なエラーメッセージでパスを含める

---

## 5. エンコーディングエラー

### パターン

```python
# 常にUTF-8を使用
with open(file_path, 'r', encoding='utf-8') as f:
    return json.load(f)
```

### 対応するテスト

- `test_load_json_utf8_bom` - UTF-8 BOM付きファイル
- `test_load_json_utf16` - UTF-16エンコードファイル
- `test_save_and_load_unicode` - Unicode文字の保存と読み込み

### ベストプラクティス

- 常に`encoding='utf-8'`を明示
- `ensure_ascii=False`で日本語などを正しく保存
- BOM付きファイルは別途処理が必要

---

## 6. 同時アクセスエラー

### パターン

```python
# ファイルロック検出
# Windows: OSError with errno 32 (ERROR_SHARING_VIOLATION)
try:
    save_json(file_path, data)
except OSError as e:
    if e.errno == 32:  # Windows: sharing violation
        # リトライまたはエラー報告
        raise FileIOError(f"File is locked: {file_path}") from e
```

### 対応するテスト

- `test_save_json_file_locked_simulation` - ファイルロックシミュレーション

### ベストプラクティス

- ファイルロックライブラリの使用を検討（`filelock`等）
- 一時ファイルに書き込み後にリネーム（アトミック操作）

---

## 7. 境界値・エッジケース

### 対応するテスト

- `test_save_and_load_empty_dict` - 空のdict
- `test_save_and_load_nested_structure` - 深くネストした構造
- `test_save_and_load_large_list` - 大きなリスト（10000要素）
- `test_save_and_load_special_keys` - 特殊なキー名（空文字、スペース、タブ）

### ベストプラクティス

- 空データも有効なケースとして処理
- 深いネストや大きなデータでのメモリ使用に注意
- 特殊文字を含むキーも正しく処理

---

## 8. JSON読み込み関数の使い分け

| 関数 | 用途 | エラー時の動作 |
|------|------|----------------|
| `safe_read_json()` | 共通ヘルパー | `raise_on_error`で制御 |
| `load_json()` | 必須ファイルの読み込み | 例外をスロー |
| `try_load_json()` | オプショナルファイル | デフォルト値を返却 |
| `try_read_json_from_file()` | バッチ処理向け | None/デフォルト返却 |
| `load_json_with_template()` | テンプレート付き | 3段階フォールバック |

### 使用例

```python
# 必須ファイル（設定ファイル等）
config = load_json(config_path)  # 失敗時は例外

# オプショナルファイル（キャッシュ等）
cache = try_load_json(cache_path, default={})  # 失敗時は空dict

# バッチ処理
for file in files:
    data = try_read_json_from_file(file)
    if data is None:
        continue  # スキップして次へ

# テンプレート付き読み込み（3段階フォールバック）
data = load_json_with_template(
    target_file=config_path,
    template_file=template_path,
    default_factory=lambda: {"version": "1.0"},
    save_on_create=True,
)
# 1. 既存ファイル → 2. テンプレート → 3. ファクトリ関数
```

---

## 9. Strategy / Chain of Responsibility パターン

`json_repository/`パッケージは2つのGoFデザインパターンを採用し、
フォールバックロジックを宣言的に表現しています。

### LoadStrategy 基底クラス

```python
class LoadStrategy(ABC, Generic[T]):
    """JSON読み込み戦略の抽象基底クラス"""

    @abstractmethod
    def load(self, context: LoadContext) -> Optional[T]:
        """読み込みを試行、成功時はT、失敗時はNone"""
        ...

    @abstractmethod
    def get_description(self) -> str:
        """戦略の説明（デバッグ用）"""
        ...
```

### 具象戦略クラス

| クラス | 責務 | 試行順序 |
|--------|------|----------|
| `FileLoadStrategy` | 既存ファイルから読み込み | 1 |
| `TemplateLoadStrategy` | テンプレートから初期化 | 2 |
| `FactoryLoadStrategy` | ファクトリ関数から生成 | 3 |
| `DefaultLoadStrategy` | 空dictを返す（最終フォールバック） | 4 |

### ChainedLoader の動作フロー

```python
class ChainedLoader(Generic[T]):
    def load(self, context: LoadContext) -> Optional[T]:
        for strategy in self._strategies:
            logger.debug(f"Trying: {strategy.get_description()}")
            result = strategy.load(context)
            if result is not None:
                return result
        return None
```

### エラー時の挙動

- 各戦略内でエラーが発生した場合は `None` を返し、次の戦略へ
- `FileLoadStrategy` で `raise_on_error=True` の場合は例外をスロー
- `DefaultLoadStrategy` が最後にあるため、必ず結果が返る

---

## 10. スキル CLI のエラー処理パターン

v4.0.0でスキルがPythonスクリプト化され、構造化されたエラー処理が導入されました。

### SetupResult status別エラー処理 (digest_setup.py)

```python
@dataclass
class SetupResult:
    status: str  # "ok" | "error" | "already_configured"
    created: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    external_paths_detected: List[str] = field(default_factory=list)
    error: Optional[str] = None
```

### 使用パターン

```python
result = manager.init(config_data, force=args.force)
if result.status == "error":
    output_error(result.error)
elif result.status == "already_configured":
    # 既存設定がある場合の処理
    pass
else:  # "ok"
    output_json(asdict(result))
```

### ConfigEditor のエラー処理 (digest_config.py)

```python
# FileNotFoundError: 設定ファイルが見つからない
except FileNotFoundError as e:
    output_error(str(e), {"action": "Run @digest-setup first"})

# JSONDecodeError: 設定ファイルが破損
except json.JSONDecodeError as e:
    output_error(f"Config file is corrupted: {e}", {"action": "Run @digest-setup to recreate"})
```

---

## 11. 外部パスアクセス制御

v4.0.0で導入された`trusted_external_paths`によるセキュリティ検証。

### 概要

`config.json`の`trusted_external_paths`は、永続化パス外へのアクセスを許可するホワイトリスト。

### 永続化パス *(v5.2.0+)*

設定ファイルは永続化パス `~/.claude/plugins/.episodicrag/` に保存されます。

```python
from infrastructure.config import get_persistent_config_dir, get_config_path

# 永続化ディレクトリ
config_dir = get_persistent_config_dir()  # ~/.claude/plugins/.episodicrag/

# 設定ファイルパス
config_path = get_config_path()  # ~/.claude/plugins/.episodicrag/config.json
```

### パス検証ロジック

```python
def _validate_path_security(self, resolved_path: Path) -> None:
    """パスが許可された範囲内かを検証"""
    # 永続化ディレクトリ内は常に許可
    persistent_dir = get_persistent_config_dir()
    if self._is_subpath(resolved_path, persistent_dir):
        return

    # trusted_external_paths 内は許可
    for trusted_path in self.trusted_external_paths:
        if self._is_subpath(resolved_path, Path(trusted_path).expanduser()):
            return

    raise ConfigError(f"Access denied: {resolved_path} is outside trusted paths")
```

### ベストプラクティス

- `base_dir` は絶対パス必須（v5.2.0+、相対パスはエラー）
- 絶対パスまたは `~` で始まるパスのみ`trusted_external_paths`に登録
- 外部パス検出時は`external_paths_detected`としてユーザーに警告
- セキュリティのためデフォルトは空配列

> 📖 詳細: [ARCHITECTURE.md](ARCHITECTURE.md#ディレクトリ構成)

---

## 12. 例外階層

```
EpisodicRAGError (Base exception)
├── ConfigError         (Configuration issues)
├── DigestError         (Digest processing failures)
├── ValidationError     (Input validation failures)
├── FileIOError         (File I/O failures)
└── CorruptedDataError  (Data integrity issues)
```

---

## 13. 参照

- 実装: `../../scripts/infrastructure/json_repository/`
  - `operations.py` - 基本操作（safe_read_json, load_json, save_json等）
  - `load_strategy.py` - Strategy Pattern実装
  - `chained_loader.py` - Chain of Responsibility実装
- テスト: `../../scripts/test/integration_tests/test_error_recovery.py`
- 例外定義: `../../scripts/domain/exceptions.py`

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
