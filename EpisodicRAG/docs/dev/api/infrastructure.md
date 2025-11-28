[EpisodicRAG](../../../README.md) > [Docs](../../README.md) > [API](../API_REFERENCE.md) > Infrastructure

# Infrastructure層 API

外部関心事（ファイルI/O、ロギング）。

> 📖 用語・共通概念は [用語集](../../../README.md) を参照

```python
from infrastructure import load_json, save_json, log_info, log_error
from infrastructure.file_scanner import scan_files, get_max_numbered_file
```

---

## JSON操作（infrastructure/json_repository.py）

### load_json()

```python
def load_json(file_path: Path) -> Dict[str, Any]
```

JSONファイルを読み込む。

### save_json()

```python
def save_json(file_path: Path, data: Dict[str, Any], indent: int = 2) -> None
```

dictをJSONファイルに保存（親ディレクトリ自動作成）。

### load_json_with_template()

```python
def load_json_with_template(
    target_file: Path,
    template_file: Optional[Path] = None,
    default_factory: Optional[Callable[[], Dict[str, Any]]] = None,
    save_on_create: bool = True,
    log_message: Optional[str] = None
) -> Dict[str, Any]
```

JSONファイルを読み込む。存在しない場合はテンプレートまたはデフォルトから作成。

### file_exists()

```python
def file_exists(file_path: Path) -> bool
```

ファイルが存在するかチェック。

### ensure_directory()

```python
def ensure_directory(dir_path: Path) -> None
```

ディレクトリが存在することを保証する（なければ作成）。

### try_load_json()

```python
def try_load_json(file_path: Path) -> Optional[Dict[str, Any]]
```

JSONファイル読み込みを試行。失敗時は例外を投げずに`None`を返す。

### try_read_json_from_file()

```python
def try_read_json_from_file(file_path: Path) -> Optional[Dict[str, Any]]
```

ファイルからJSON読み込みを試行（`try_load_json`のエイリアス）。

### confirm_file_overwrite()

```python
def confirm_file_overwrite(
    file_path: Path,
    confirm_callback: Callable[[str], bool]
) -> bool
```

ファイル上書き確認。コールバック関数でユーザーに確認を求める。

```python
# 使用例
def my_confirm(message: str) -> bool:
    return input(f"{message} (y/n): ").lower() == 'y'

if confirm_file_overwrite(Path("output.txt"), my_confirm):
    # 上書き実行
```

---

## ファイルスキャン（infrastructure/file_scanner.py）

### scan_files()

```python
def scan_files(
    directory: Path,
    pattern: str = "*.txt",
    sort: bool = True
) -> List[Path]
```

指定ディレクトリ内のファイルをスキャン。

### get_files_by_pattern()

```python
def get_files_by_pattern(
    directory: Path,
    pattern: str,
    filter_func: Optional[Callable[[Path], bool]] = None
) -> List[Path]
```

パターンとフィルタ関数でファイルを取得。

### filter_files_after_number()

```python
def filter_files_after_number(
    files: List[Path],
    threshold: int,
    number_extractor: Callable[[str], Optional[int]]
) -> List[Path]
```

指定番号より大きいファイルのみをフィルタ。

### count_files()

```python
def count_files(directory: Path, pattern: str = "*.txt") -> int
```

パターンにマッチするファイル数をカウント。

### get_max_numbered_file()

```python
def get_max_numbered_file(
    directory: Path,
    pattern: str,
    number_extractor: Callable[[str], Optional[int]]
) -> Optional[int]
```

ディレクトリ内の最大番号を取得。

```python
from domain.file_naming import extract_number_only

# Loopファイルの最大番号を取得
max_loop = get_max_numbered_file(
    loops_path,
    "L*.txt",
    extract_number_only
)  # 186
```

---

## ロギング（infrastructure/logging_config.py）

### get_logger()

```python
def get_logger(name: str = "episodic_rag") -> logging.Logger
```

モジュールロガーを取得。

### setup_logging()

```python
def setup_logging(level: Optional[int] = None) -> logging.Logger
```

デフォルトのロギング設定をセットアップ。

### ユーティリティ関数

```python
def log_info(message: str) -> None
def log_warning(message: str) -> None
def log_error(message: str, exit_code: Optional[int] = None) -> None
```

環境変数でログ設定をカスタマイズ可能:
- `EPISODIC_RAG_LOG_LEVEL`: ログレベル (DEBUG, INFO, WARNING, ERROR)
- `EPISODIC_RAG_LOG_FORMAT`: ログフォーマット (simple, detailed)

---

## ユーザーインタラクション（infrastructure/user_interaction.py）

### get_default_confirm_callback()

```python
def get_default_confirm_callback() -> Callable[[str], bool]
```

標準入力を使用したデフォルトの確認コールバックを取得。

```python
callback = get_default_confirm_callback()
if callback("ファイルを上書きしますか？"):
    # 上書き実行
```

---

**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
