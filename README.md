<!-- ここから: VentOCR_EngineTemplate（このリポジトリ）の説明。新しいエンジンを作るときは、ここから下の「ここまで」までを消す -->
# VentOCR エンジンのひな形と約束事

VentOCR は人工呼吸器の画面の動画から数値（OCR）と波形を読み取る、研究用のデスクトップアプリです。
解析エンジンは機種ごとの公開リポジトリ（`VentOCR_<機種>`）で開発し、アプリが決まった版（タグ）を取り込みます。

- **エンジンとアプリの約束事: [ENGINE_API.md](ENGINE_API.md)**（正本はここ。エンジンはここに書かれたことだけを前提に作る）
- 新しいエンジン: このリポジトリを写して `VentOCR_<機種>` を作る（`core.py`・`schema.py`・`Settings.py`・`ExtractWaves.py`・`test.py` がひな形）
- エンジンのリポジトリ: `VentOCR_NAVA`（Servo-U NAVA。v1.0.0〜v1.3.0）・`VentOCR_PostNAVA`（Servo-U）・`VentOCR_Hamilton`・`VentOCR_V600`（Dräger V600 / Savina 300）・
  `VentOCR_Bennett980`（Puritan Bennett 980）
- ライセンス: MIT（[LICENSE](LICENSE)）。研究用のソフトウェアで、医療機器ではありません

<!-- ここまで -->

# [Engine Name] VentOCR Engine

## Supported Devices
- [対象人工呼吸器名]

## Description
[Engineの概要]

## Expected Layout
See `layout.jpg` for the ventilator display layout and ROI positions.

## Limitations
- [既知の制限事項]

## Author
- [開発者名]
