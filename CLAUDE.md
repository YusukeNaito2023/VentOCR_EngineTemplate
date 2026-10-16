# CLAUDE.md — VentOCR Engine Development

## Project Context
このディレクトリはVentOCR Engine — 人工呼吸器ディスプレイ映像をOCR解析するプラグインモジュール。
VentOCR本体から `importlib.import_module(f"Engine.{engine_name}.core")` で動的に読み込まれる。

## Required Interface (core.py)

### Version Variables
```python
ENGINE_VERSION = "x.y.z"       # Engine開発バージョン
VENTOCR_TESTED = "0.5.5"       # 動作確認済みVentOCRバージョン
```

### initial_ocr(frames, total_frames, subfolder, settings={}, progress_callback=None, frames_dir=None) -> pd.DataFrame
- frames: **カラーフレーム (BGR) のジェネレータ**。1枚ずつ順次渡される。
  - **list化禁止** — 5時間録画で数TB消費するため
  - `for frame_count, color_frame in enumerate(frames):` でイテレートする
  - グレースケールが必要な場合: `gray = np.dot(color_frame[..., :3], [0.114, 0.587, 0.299]).astype(np.uint8)`
  - 過去フレームへのランダムアクセスが必要な場合: `cv2.imread(os.path.join(frames_dir, f"frame_{i:08d}.jpg"))`
- total_frames: int - 総フレーム数
- subfolder: str - セグメント識別子
- settings: dict - engine_options.json から読み込まれた設定
- progress_callback: callable(current=int, total=int, message=str) or None
- frames_dir: str - Main.pyがJPEG保存済みのディレクトリパス
- Returns: DataFrame。必須列: "Frame" (int, 0-indexed), "BreathMark" (int, 0 or 1)

### post_ocr(df, Analyze_Id, user_ID, settings={}) -> (df_frames, df_breaths)
- df: initial_ocrの出力DataFrame
- 追加必須列: BreathNumber (int, 1-indexed), Time (str, "HH:MM:SS:CC"), Alert (str), Abnormal (int, 0 or 1)
- Returns: (全行のdf_frames, 呼吸ごと1行のdf_breaths)

### extract_waves(...) -> (int, pd.DataFrame)  [オプション]
- VentOCRは `hasattr(Engine, 'extract_waves')` で存在確認する
- 呼吸ごとのCSVを output_dir に書き出す (列: X, Wave1, Wave2, ...)
- **archive_dir が指定された場合は fields.txt を必ず書き出す**（Label画面の波形表示に必須）

#### fields.txt フォーマット
```
[waves]
Wave1
Wave2
...

[fields]
Field1
Field2
...
```
- `[waves]` セクション: BreathCSVに含まれる波形列名を列挙（X列は除く）。Label画面はここに記載された列のみチャートに描画する。**このセクションが無いと波形が一切表示されない。**
- `[fields]` セクション: Breaths.csvに含まれる補助フィールド名を列挙（Label画面のテーブル表示用）

## Required Files
- `__init__.py` — 空（Pythonパッケージマーカー）
- `core.py` — ENGINE_VERSION, VENTOCR_TESTED + initial_ocr + post_ocr
- `Settings.py` — ROI座標定義
- `schema.py` — ENGINE_SETTINGS_SCHEMA（設定UIスキーマ）
- `engine_options.json` — デフォルト設定値
- `README.md` — Engine説明
- `CHANGELOG.md` — 更新履歴
- `layout.jpg` — 人工呼吸器のレイアウト参照画像
- `sample_frame.jpg` — 異常検出用リファレンス画像
- `sample.mp4` — テスト動画（3-5分）
- `test_spec.json` — 出力項目・精度基準の宣言
- `test.py` — テストスクリプト
- `expected_output/` — 正解CSV (Frames.csv, Breaths.csv)

## Rules for Claude
- このEngineディレクトリ外のファイルを変更しない
- ネットワーク呼び出し、subprocess、exec/evalを追加しない
- OCR・画像処理は initial_ocr 内で行う
- DataFrame後処理は post_ocr 内で行う
- Engine内モジュールは相対インポート: `from . import Settings`
- 設定は settings 引数から取得（ファイル直接読み込み禁止）
- フレーム画像は frames_dir/frame_{:08d}.jpg 形式
- progress_callback で進捗を報告する
- コメントは日本語で書く
