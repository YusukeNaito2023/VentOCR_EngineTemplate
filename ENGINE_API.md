# VentOCR エンジンの約束事（engine_api 1）

VentOCR のアプリ（Mac・Windows のデスクトップ版）と、解析エンジン（人工呼吸器の機種ごとの OCR・波形抽出）の間の約束事です。
エンジンを作る・直すときは、この文書に書かれたことだけを前提にしてください。ここに無い動き（アプリの内部の関数など）に頼ると、
アプリの更新で動かなくなることがあります。

- **この文書の正本は `VentOCR_EngineTemplate`（エンジンのひな形のリポジトリ。公開）にある**。アプリ（VentOCR。非公開）の担当者もここを直す
- アプリ側の実装: `ventocr_core/pipeline.py`（解析の流れ）、`ventocr_core/runtime/Global_Setting.py`・`progress_io.py`（エンジンに渡す部品）、
  `ventocr_desktop/data/package.py`（結果の読み込み）
- この約束事を変えるときは、アプリとエンジンの担当者で相談し、**版（engine_api）を上げて**ここに記録する（末尾の「変更履歴」）

---

## 1. エンジンのリポジトリとフォルダ

- エンジンは機種ごとに1つの git リポジトリ（`VentOCR_<機種>`。例 `VentOCR_Hamilton`）。**リポジトリの中身がそのまま1つのエンジンのフォルダ**になる
- アプリは、エンジンのリポジトリの決まったタグを `ventocr_core/runtime/Engine/<engine_key>/` に取り込む（git submodule）。
  同じリポジトリの別のタグを、別のエンジンキーとして並べて取り込める（NAVA: `VentOCR_NAVA` の v1.0.0〜v1.3.0 を `nava_ventocr`〜`nava_ventocr_v1_3` に）
- ライセンスは MIT（各リポジトリの `LICENSE`）
- 利用者は、アプリの「解析 > エンジン…」→「GitHub から探す…」で、公開されているエンジンのタグをダウンロードして入れられる（VentOCR 0.2.8 から）。
  アプリが探すのは**信頼する所有者（既定は YusukeNaito2023。利用者が増やせる）の、名前が `VentOCR_` で始まる公開リポジトリ**の**タグ**だけ。
  タグの `manifest.json` の `engine_key` がエンジンキー（入れるフォルダの名前）になり、`engine_key` の無いタグは一覧に出ない。
  入れたエンジンは、アプリに付属の同じエンジンキーのエンジンより優先される（フォルダの優先順は §9）

```
<engine_key>/                 アプリに取り込まれたときのフォルダ名 = エンジンキー（例: hamilton_ventocr）。解析結果・DB にはこの名前で記録される
├── __init__.py               空でよい（Python のパッケージとして読み込む）
├── core.py                   必須。下の関数と ENGINE_VERSION
├── manifest.json             必須（無くても動くが、名前・版・表示項目が出ない）
├── schema.py                 任意。設定項目（ENGINE_SETTINGS_SCHEMA）
├── engine_options.json       任意。設定の既定値
├── README.md                 任意。「解析 > エンジン…」の「説明」タブに表示
├── layout.jpg                任意。「画面レイアウト」タブに表示（基準にした呼吸器の画面）
├── CHANGELOG.md              推奨。版ごとの変更
├── LICENSE                   MIT
└── その他                    Settings.py・ExtractWaves.py・基準画像など、自由
```

- フォルダ名が `_` で始まるものは一覧に出ない（ひな形・作業用）
- エンジンは `Engine.<engine_key>` というパッケージとして読み込まれる。**エンジン内のファイルは相対 import**（`from . import Settings`）で読む。
  ほかのエンジンを import しない
- 自分のフォルダのファイル（基準画像など）は `os.path.dirname(os.path.abspath(__file__))` を基準に開く。カレントディレクトリ基準にしない
- サンプル動画・作業ファイル（`temp/`・`_runtime_models/`・`__pycache__/`）はリポジトリに入れない（`.gitignore`）。
  配布物を作るとき（アプリの `tools/make_dist.py`）も `*.mp4`・`*.mov` などの動画・`temp/`・`_runtime_models/` は除かれる

## 2. 版

| どこ | 何を書く | 使われ方 |
|---|---|---|
| `core.py` の `ENGINE_VERSION = "1.4.0"` | エンジンの版（文字列） | **解析結果に記録される版**（`manifest.json` の `engine_version`）。行頭に文字列で書く（アプリは import せずに正規表現でも読む） |
| `manifest.json` の `version` | 同じ値 | 「解析 > エンジン…」の表示。`ENGINE_VERSION` と違うと注意が出る |
| `manifest.json` の `engine_api` | この約束事の版（いまは `1`） | アプリが対応する版より大きいと、アプリはそのエンジンを使わない（「VentOCR を更新してください」） |

- 解析結果が変わる変更は、版を上げる。アプリに取り込んでもらう版には **タグ `v<版>`**（例 `v1.4.0`）を付ける
- 古い結果を同じ版で解析し直せるよう、**結果が大きく変わる版は新しいエンジンキー**（例: `nava_ventocr_v1_4`。アプリに新しいフォルダとして
  取り込む）にするのが基本（NAVA はこの方式。manifest の `engine_key` も変える）。小さな修正は同じエンジンキーのまま版を上げてよい（Hamilton はこの方式）
- `ENGINE_VERSION` と `manifest.json` の `version` は必ずそろえる

## 3. 関数（core.py）

解析は次の順に進む。アプリが動画を 60 秒ごとに分割し、10 fps の固定フレームレートに変換してから、エンジンを呼ぶ。

```
動画 ─ 分割（60秒）─┬─ initial_ocr（区間ごと・並列。別プロセス）─┐
                     └─ …                                         ├─ 結合 ─ post_ocr ─ extract_waves（任意）─ 結果
```

### 3.1 `initial_ocr(frames, total_frames, subfolder, settings, progress_callback=None, frames_dir=None) -> pd.DataFrame`（必須）

1区間（約 60 秒）の各フレームを読む。**区間ごとに別プロセス**（multiprocessing の spawn）で、並列に呼ばれる。

| 引数 | 内容 |
|---|---|
| `frames` | フレームの反復子（BGR の `numpy.ndarray`）。受け取った時点で、そのフレームは `frames_dir/frame_%08d.jpg` に保存済み |
| `total_frames` | この区間のフレーム数（int） |
| `subfolder` | 区間の番号（5桁の文字列。例 `"00003"`） |
| `settings` | 設定（§6）。`settings.get("initial_ocr", {})` で読む |
| `progress_callback(current, total, message="")` | 進み具合（キーワード引数で呼んでよい）。`message` は使われない |
| `frames_dir` | この区間のフレーム画像のフォルダ（`./temp/<user_id>/Frames/<subfolder>`） |

戻り値: 1フレーム1行の DataFrame。
- **必須の列**: `Frame`（区間内の 0 からのフレーム番号）
- アプリは CSV に書いて読み直す（`index=False`）ので、値は CSV で表せる型にする
- そのほかの列（OCR の値・確からしさ・掃引の位置など）は自由。§7 の列名にすると、アプリが使う

### 3.2 `post_ocr(df, Analyze_Id, user_ID, settings) -> (df_frames, df_breaths)`（必須）

全区間を結合した表を受け取り、呼吸に区切る。元のプロセスで1回呼ばれる。

| 引数 | 内容 |
|---|---|
| `df` | 全区間の `initial_ocr` の結果を区間の順につないだ表。アプリが次の列を足している: `Frame`（**動画全体の通し番号。1 から**。元の値は `iFrame` に移す）、`iFrame`（区間内の番号）、`source_file`（`"output_00003.csv"` の形） |
| `Analyze_Id` | いつも `1`（サーバー版の名残） |
| `user_ID` | 作業用の名前（`"job_YYYYmmdd_HHMMSS"`）。§5 のフォルダの名前に使う |
| `settings` | 設定（§6）。`settings.get("post_ocr", {})` |

戻り値:
- `df_frames`: フレームごとの表 → `Frames.csv`。**`Frame`・`source_file`・`iFrame` を残すこと**（アプリがフレームの位置を引くのに使う）
- `df_breaths`: 呼吸ごとの表 → `Breaths.csv`（§7.1）
- どちらもアプリが **行番号付き**で CSV に書く（先頭に名前の無い列ができる。アプリは読むときに捨てる）
- `extract_waves` を持たないエンジンは、ここで呼吸ごとの波形 `GS.Dir_BreathCSVs(user_ID)/<呼吸番号>.csv` を書く（§7.3）。
  **波形が1つも無くても `GS.Dir_BreathCSVs(user_ID)` のフォルダは作る**（無いと結果の保存で止まる）

### 3.3 `extract_waves(df_frames, df_breaths, frames_root, output_dir, user_ID, settings, archive_dir=None) -> (int, pd.DataFrame)`（任意）

あれば `post_ocr` のあとに呼ばれる（無ければ呼ばれない。`hasattr` で判断）。

| 引数 | 内容 |
|---|---|
| `df_frames`, `df_breaths` | `post_ocr` の戻り値。`df_frames` は**その場で書き換えてよい**（呼吸を区切り直したとき、`Frames.csv` も書き直される） |
| `frames_root` | 動画全体の通し番号のフレーム画像（`./temp/<user_id>/Frames/_flat/frame_%08d.jpg`。`Frame` と同じ番号） |
| `output_dir` | 呼吸ごとの波形 CSV を書くフォルダ（作成済み） |
| `archive_dir` | 結果に一緒に入れたいファイルを置くフォルダ（作成済み。§7.5） |

戻り値: `(波形を書き出した呼吸の数, df_breaths)`。`df_breaths` は書き換えたものを返す（`Breaths.csv` が書き直される）。

### 3.4 そのほか

- `ENGINE_VERSION`（§2）
- 関数の中で `print` してよい（アプリのログに出る。標準出力はアプリが使うので、エンジンの出力は標準エラーに回される）。
  `tqdm` の進み具合の行はログから除かれる
- 例外を出すと、その区間（initial_ocr）は1回だけやり直され、それでも失敗すると結果に `failed_segments` として記録される。
  `post_ocr`・`extract_waves` の例外は解析の失敗になる

## 4. アプリが用意する部品

エンジンは次の2つを**トップレベルのモジュールとして** import できる（`import Global_Setting as GS`）。

### 4.1 `Global_Setting`

| 名前 | 内容 |
|---|---|
| `FPS` | `10`（変換後のフレームレート） |
| `SEG_TIME` | `60`（分割の秒数） |
| `FFMPEG_BIN`, `FFPROBE_BIN` | ffmpeg・ffprobe のパス（アプリが版を固定して入れたもの） |
| `CHAR_CODE` | `"utf-8"` |
| `DB_FILE` | `None`（デスクトップ版は DB を使わない） |
| `f_DEBUG` | `False` |
| `Dir_Base(user_id)` | `./temp/<user_id>` |
| `Dir_Frames(user_id)` | `…/Frames`（区間ごとのフレーム画像 `<5桁>/frame_%08d.jpg` と、通し番号の `_flat/`） |
| `Dir_Outputs(user_id)` | `…/outputs`（ここに `BreathCSV_Report.csv` を書くと結果に入る） |
| `Dir_BreathCSVs(user_id)` | `…/BreathCSVs`（呼吸ごとの波形 CSV） |
| `Dir_Converted(user_id)` | `…/converted`（変換後の区間動画。読むだけ） |
| `Dir_Inputs(user_id)` | `…/inputs` |
| `Archive_Dir_For(user_id, analyze_id)` | `…/archive`（§7.5） |
| `Dir_Archive(user_id)` | 古いエンジンのための互換。新しいエンジンは使わない |

パスはすべて**カレントディレクトリ基準**。アプリは解析の作業フォルダに移動（chdir）してからエンジンを呼ぶ（区間のプロセスも同じ）。

### 4.2 `progress_io`

`report_overall(user_id, analyze_id, *, stage=None, message=None, current=None, total=None, **kwargs)`:
`post_ocr`・`extract_waves` の中の進み具合をアプリの「解析状況」に出す（`stage` は `"post_processing"` か `"extract_waves"`）。
失敗しても例外は出さない。無くても動くよう、`try: import progress_io` で読むとよい。

### 4.3 OCR のモデル

EasyOCR のモデルは、アプリが解析の前に `./_runtime_models/easyocr` に用意する（craft・english_g2 など）。
エンジンは `easyocr.Reader(["en"], model_storage_directory=os.path.join(".", "_runtime_models", "easyocr"), ...)` で使う。
GPU（CUDA / Apple MPS）は EasyOCR・PyTorch が自動で使う（設定 `use_gpu` を持つエンジンはそれに従う）。

### 4.4 使えるライブラリ

アプリの環境（アプリの `constraints.txt` で版を固定）に入っているものだけ: `numpy`・`pandas`・`opencv-python-headless`（cv2）・
`easyocr`・`torch`・`torchvision`・`matplotlib`・`tqdm`・`scipy`・`scikit-image`・`Pillow` と Python 3.14 の標準ライブラリ。
**新しいライブラリが必要なときは、アプリの担当者に相談する**（アプリの更新が必要。エンジンだけでは入れられない）。

## 5. 作業フォルダ

```
<作業フォルダ>/                        カレントディレクトリ（アプリが用意。解析ごとに消える）
├── _runtime_models/easyocr/           OCR のモデル（§4.3）
└── temp/<user_id>/
    ├── Frames/00000/frame_00000000.jpg   区間ごと（区間内の番号、0 から）
    ├── Frames/_flat/frame_00000001.jpg   動画全体の通し番号（1 から。区間ごとの画像へのリンク）
    ├── outputs/  BreathCSVs/  archive/  converted/  …
```

- `temp/<user_id>/` は解析の前後に消される。ここ以外（カレントディレクトリの直下など）に書いたファイルは残ってしまうので、書かない
  （古い NAVA が書く `breath.csv`・`frames.csv`・`temp/Cdyn_ROIs_*` はアプリが消している）

## 6. 設定（schema.py・engine_options.json）

設定は `{"initial_ocr": {キー: 値}, "post_ocr": {キー: 値}}` の形で各関数に渡る。
アプリの「動画を解析」の画面で利用者が変えられ、値は解析結果に記録される。

`schema.py` の `ENGINE_SETTINGS_SCHEMA = {段階: {キー: 項目}}`。項目は辞書で、次のキーを使える。

| キー | 内容 |
|---|---|
| `type` | `"bool"`（チェック）・`"int"`（整数）・`"float"`（小数）・`"multiselect"`（複数選択。値はリスト）。ほかの型は画面では変えられない（既定値のまま渡る） |
| `default` | 既定値 |
| `label` | 画面の表示名（無ければキー） |
| `choices` | `multiselect` の選択肢（リスト） |
| `choice_labels` | 選択肢の表示名 `{値: 表示名}` |
| `primary` | `true` にすると画面の上に大きく出す（よく変える項目。ほかは「詳細設定」に入る） |

- `engine_options.json` があれば、それが既定値（無ければ `default` から作る）。どちらにも無いキーは解析の前に除かれる
- `min`・`max`・単一選択・文字列の入力は、いまは画面が対応していない（必要ならアプリの担当者に相談）

## 7. 出力

### 7.1 Breaths.csv（`post_ocr`・`extract_waves` の `df_breaths`）

1呼吸1行。アプリが使う列（ほかの列は「呼吸プロパティ」の詳細データと CSV の書き出しにそのまま出る）:

| 列 | 必須 | 内容・使われ方 |
|---|---|---|
| `BreathNumber` | **必須** | 呼吸番号（1 から、重複なし）。波形 CSV のファイル名と対応する。呼吸の分割・除外・書き出しで使う |
| `Frame` | **必須** | 呼吸の開始フレーム（動画全体の通し番号）。開始時刻 = `Frame / FPS`。キャプチャーの基準・並べ替え・編集に使う |
| `Alert` | 推奨 | 空でなければ「Alert」の呼吸（呼吸リストで色が付き、絞り込める）。中身（理由の文字）はチャートに表示される |
| `Start_File_Name`, `End_File_Name` | 推奨 | 波形を読んだ区間の最初と最後のフレーム画像のパス（`.../Frames/<5桁>/frame_%08d.jpg` か `.../_flat/frame_%08d.jpg`）。**キャプチャーの再生範囲**と、波形の時刻の計算に使う。無いとキャプチャーが出ない |
| `Wave_T0`, `Wave_Rate` | 推奨 | 波形の最初の点の時刻（動画の先頭からの秒）と、1秒あたりの点の数。波形の各点の時刻 = `Wave_T0 + i / Wave_Rate`。**いちばん確かな時刻**で、あればこれを使う |
| `X_Start`, `Sweep_Cursor_Start`, `Sweep_Cursor_End` | 任意 | NAVA 系の掃引: 波形の左端、開始・終了画像の掃引位置（消去帯の右端。画面の x）。`Wave_T0` が無いときの時刻と、キャプチャーの走査線に使う。3つそろって使われる |
| `Region_X_Start`, `Sweep_Start`, `Sweep_End` | 任意 | Bennett 980 の掃引（終了画像の掃引線 = 波形の右端）。3つそろって使われる |
| `P_min`/`P_max`, `F_min`/`F_max`, `V_min`/`V_max`, `E_min`/`E_max`, `Pes_min`/`Pes_max` | 任意 | 呼吸器の画面の縦軸の範囲（Pressure・Flow・Volume・Edi・Pes）。チャートの縦軸に使う |
| `Start_Time`, `End_Time` | 任意 | 呼吸の開始・終了（秒）。あれば `Frame` より優先 |
| `Status` | 非推奨 | あるとその値がそのまま状態になる（`Normal`・`Alert` 以外だと絞り込みが効かない）。使わず `Alert` で表す |
| `Excluded`, `Split_From` | **使わない** | アプリが書く列（除外・分割）。エンジンは出さない |

- `manifest.json` の `breath_summary` に挙げた列が「呼吸プロパティ」のサマリーに出る（§8）

### 7.2 Frames.csv（`df_frames`）

| 列 | 必須 | 内容 |
|---|---|---|
| `Frame`, `source_file`, `iFrame` | **必須** | アプリが足した列（§3.2）。消さない |
| `Sweep_X` | 任意 | そのフレームでのペン先の画面上の x（解析した動画の画素）。あれば**キャプチャーの走査線はこれを使う**（いちばん確か）。掃引を毎フレーム追跡するエンジン（Hamilton・postnava・V600）が出している |
| そのほか | 任意 | アプリは読まない（結果には残る） |

### 7.3 BreathCSVs/<呼吸番号>.csv（呼吸ごとの波形）

- ファイル名は `BreathNumber` の数字だけ（`12.csv`）。この呼吸の波形が無ければ書かない
- 列: `X` と、`Pressure`・`Flow`・`Volume`・`Edi`・`Pes` のうち読んだもの（ほかの列名はチャートに出ない）
- 1行 = 画面の1列（掃引の向きに連続）。行の数と `Wave_Rate` から時刻が決まる
- `X` の意味はエンジンごとに違ってよい（通し番号・画面の列・折り返しを展開した位置）。アプリは `X` を画面の位置としては使わない
  （`Wave_T0`・`Wave_Rate` も掃引の列も無い古い結果だけ、時刻の割り振りに `X` の間隔を使う）
- 呼吸の分割には 3 行以上必要

### 7.4 BreathCSV_Report.csv（任意）

`GS.Dir_Outputs(user_id)` に書くと結果に入る（波形を書いた・書かなかった理由の一覧など。アプリは読まない）。

### 7.5 archive_dir（任意）

`GS.Archive_Dir_For(user_id, Analyze_Id)` に置いたファイルは、結果のフォルダの直下にそのまま入る
（いまのエンジンは `fields.txt`・`scale_meta.json` を置いている。アプリは読まない）。

## 8. manifest.json

| キー | 必須 | 内容・使われ方 |
|---|---|---|
| `version` | **必須** | 版（§2。`ENGINE_VERSION` と同じ） |
| `engine_api` | **必須**（無ければ 1 とみなす） | この約束事の版 |
| `display_name` | **必須** | 画面の表示名（例 `"NAVA v1.3"`） |
| `ventilator` | 推奨 | 対応する人工呼吸器の機種（例 `"Servo-U"`）。「解析 > エンジン…」の機種での絞り込みに使う |
| `description`, `developer` | 推奨 | 説明・開発者（表示と検索） |
| `breath_summary` | 推奨 | 「呼吸プロパティ」のサマリーに出す Breaths.csv の列（リスト。無い列は飛ばす） |
| `labels` | 任意 | 列の表示名 `{列名: 表示名}`（サマリー・詳細データ） |
| `accuracy` | 任意 | 列ごとの `{"unit": 単位, "method": …, "threshold": …}`。`unit` はサマリーの項目名に「（単位）」で付く |
| `base_resolution`, `supported_resolutions` | 推奨 | 基準にした動画の解像度（表示のみ） |
| `has_extract_waves` | 任意 | `extract_waves` を持つか（表示のみ） |
| `output_columns` | 任意 | `{"frames": [...], "breaths": [...]}`（表示のみ） |
| `engine_key` | **必須**（アプリからダウンロードしてもらうとき） | エンジンキー。英字で始まる英数字と `_`（例 `"hamilton_ventocr"`）。§1・§2 |
| `ventocr_min` | 任意 | 必要なアプリの版（いまは表示のみ。段階2でアプリが確かめる予定） |

## 9. 開発の手順

アプリのソースが無くても、インストールした VentOCR でエンジンを試せる。
エンジンのリポジトリは、**エンジンキーの名前のフォルダに clone する**（アプリは `Engine.<エンジンキー>` として読み込むため）。

```sh
# 例: Hamilton のエンジンを ~/work/engines/hamilton_ventocr に
git clone https://github.com/<所有者>/VentOCR_Hamilton ~/work/engines/hamilton_ventocr

# Mac（Windows は %LOCALAPPDATA%\VentOCR\venv\Scripts\python.exe と %LOCALAPPDATA%\VentOCR\app）
PY="$HOME/Library/Application Support/VentOCR/venv/bin/python"
APP="$HOME/Library/Application Support/VentOCR/app"

# 使えるエンジンと、その版・フォルダ（作業中のエンジンのフォルダが並ぶ親フォルダを --engine-dir で足す）
cd "$APP" && "$PY" -m ventocr_core --list-engines --engine-dir ~/work/engines

# 解析（同じ名前ならアプリに入っているエンジンより --engine-dir のものが優先される）
cd "$APP" && "$PY" -m ventocr_core 動画.mov --out 出力フォルダ --work-root 作業フォルダ \
    --engine hamilton_ventocr --engine-dir ~/work/engines
```

- 画面（VentOCR のアプリ）で試すときは、環境変数 `VENTOCR_ENGINE_PATH` に作業中のフォルダを入れて起動する
  （Mac: ターミナルで `VENTOCR_ENGINE_PATH=~/work/engines "$PY" -m ventocr_desktop`）。
  「解析 > エンジン…」のフォルダの欄に「追加のフォルダ」と出る
- 出力フォルダを VentOCR の「ファイル > 解析結果を取り込む…」で開くと、チャート・キャプチャーで確かめられる
- 新しいエンジンは、このリポジトリ（`VentOCR_EngineTemplate`）を写して作る（新しいリポジトリ `VentOCR_<機種>` にする）

## 10. 変更履歴

- 2026-10-17: アプリ（0.2.8）が GitHub からエンジンをダウンロードできるようになったことを §1 に、manifest.json の `engine_key` を §8 に書いた。
  エンジンを探すフォルダは「VENTOCR_ENGINE_PATH → ダウンロードしたエンジン → アプリに付属のエンジン」の順（約束事の中身は変わらないので engine_api は 1 のまま）

- 2026-10-17: エンジンを機種ごとのリポジトリ（`VentOCR_<機種>`）に分け、この文書を `VentOCR_EngineTemplate` に移した（約束事の中身は変わらないので engine_api は 1 のまま）
- engine_api 1（2026-10-17）: この文書を作成（Web 版から引き継いだ形をそのまま記述）。`--engine-dir`・`VENTOCR_ENGINE_PATH` を追加
