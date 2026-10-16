"""
[Engine Name] VentOCR Engine
[対象人工呼吸器名]のディスプレイ映像からOCR解析を行う。

Interface:
    initial_ocr(frames, total_frames, subfolder, settings, progress_callback, frames_dir)
        -> pd.DataFrame

    post_ocr(df, Analyze_Id, user_ID, settings)
        -> (df_frames, df_breaths)

    extract_waves(df_frames, df_breaths, frames_root, output_dir, user_ID, settings, overwrite, archive_dir)
        -> (effective_breaths_count, df_breaths)
"""

from tqdm import tqdm
from . import Settings
import cv2
import pandas as pd
import numpy as np
import os

# Engineバージョン（開発者が管理するリリース番号）
ENGINE_VERSION = "0.1.0"

# このEngineが動作確認されたVentOCRのバージョン
VENTOCR_TESTED = "0.5.5"


def _to_gray(color_frame):
    """カラーフレーム (BGR) をグレースケールに変換する。"""
    return np.dot(color_frame[..., :3], [0.114, 0.587, 0.299]).astype(np.uint8)


def _load_frame_from_disk(frames_dir, frame_index):
    """ディスクからカラーフレームJPEGを読み込む（ランダムアクセス用）。"""
    path = os.path.join(frames_dir, f"frame_{frame_index:08d}.jpg")
    return cv2.imread(path)


# ============================================================
# initial_ocr
# ============================================================

def initial_ocr(frames, total_frames, subfolder, settings={},
                progress_callback=None, frames_dir=None):
    """
    全フレームからOCR解析を行う。

    Args:
        frames: カラーフレームのジェネレータ (BGR, numpy配列)。
                1枚ずつ順次渡される。list化禁止。
                過去フレームへのランダムアクセスが必要な場合は frames_dir を使用する。
        total_frames: int - 総フレーム数
        subfolder: str - セグメント識別子
        settings: dict - engine_options.jsonから読み込まれた設定
        progress_callback: callable(current, total, message) or None
        frames_dir: str - フレームJPEG保存ディレクトリ（ランダムアクセス用）

    Returns:
        pd.DataFrame - 必須列: Frame (int, 0-indexed), BreathMark (int, 0 or 1)
                       Engine固有の値列を追加可能
    """
    # TODO: settings から必要なパラメータを取得
    # ocr_settings = settings.get("initial_ocr", {})

    data = []

    with tqdm(total=total_frames, desc="OCR Processing") as pbar:
        if progress_callback is not None:
            progress_callback(current=0, total=total_frames, message="Running OCR")

        for frame_count, color_frame in enumerate(frames):
            row = {
                "Frame": frame_count,
                "BreathMark": 0,
                # TODO: Engine固有の出力列を追加
                # "VTE": "",
                # "VTE_raw": "",
                # "VTE_conf": "0.00",
            }

            # カラーフレームからグレースケールに変換（OCRに必要な場合）
            gray = _to_gray(color_frame)

            # TODO: ROIの抽出とOCR処理を実装
            # roi = gray[y:y+h, x:x+w]
            # result = reader.readtext(roi)

            # TODO: BreathMark検出ロジックを実装
            # カラーフレームを直接使う場合は color_frame を使用

            data.append(row)
            pbar.update(1)

            if progress_callback is not None and (frame_count % 100 == 0 or frame_count == total_frames - 1):
                progress_callback(current=frame_count, total=total_frames, message="Running OCR")

    df = pd.DataFrame(data)
    print(f"[initial_ocr] {total_frames} frames processed")
    return df


# ============================================================
# post_ocr
# ============================================================

def post_ocr(df, Analyze_Id, user_ID, settings={}):
    """
    initial_ocrの結果を後処理し、フレームDataFrameと呼吸DataFrameを生成する。

    Args:
        df: pd.DataFrame - initial_ocrの出力
        Analyze_Id: int - 解析ID
        user_ID: str - ユーザーID
        settings: dict - engine_options.jsonから読み込まれた設定

    Returns:
        (df_frames, df_breaths): tuple of DataFrames
        df_framesに追加必須の列:
            - BreathNumber (int, 1-indexed, BreathMarkの累積和)
            - Time (str, "HH:MM:SS:CC" 形式)
            - Alert (str, 空文字 or アラート理由)
            - Abnormal (int, 0 or 1)
    """
    fps = settings.get("post_ocr", {}).get("fps", 10)
    df = df.copy()

    # BreathNumber: BreathMarkの累積和（1-indexed）
    df["BreathNumber"] = df["BreathMark"].cumsum()
    df.loc[df["BreathNumber"] == 0, "BreathNumber"] = 1

    # タイムスタンプ生成
    df["Time"] = df["Frame"].apply(lambda f: _format_time(f, fps))

    # 必須列の初期化
    if "Alert" not in df.columns:
        df["Alert"] = ""
    if "Abnormal" not in df.columns:
        df["Abnormal"] = 0

    df_frames = df

    # 呼吸レベルの集約（各BreathNumberの最初のフレーム）
    df_breaths = df.loc[df.groupby("BreathNumber")["Frame"].idxmin()].copy()

    print(f"[post_ocr] {len(df_frames)} frames, {len(df_breaths)} breaths")
    return df_frames, df_breaths


# ============================================================
# extract_waves (オプション)
# ============================================================

# extract_wavesはオプション関数。VentOCRはhasattr(Engine, 'extract_waves')で存在確認する。
# 波形抽出が不要なEngineはこの関数を削除またはコメントアウトしてよい。

# def extract_waves(df_frames, df_breaths, frames_root, output_dir, user_ID,
#                   settings={}, overwrite=False, archive_dir=None):
#     """
#     呼吸ごとに波形データをCSVに抽出する。
#
#     Args:
#         df_frames: pd.DataFrame - post_ocrの出力（Abnormal列含む）
#         df_breaths: pd.DataFrame - 呼吸レベルのDataFrame
#         frames_root: str - フレーム画像のディレクトリパス
#         output_dir: str - CSV出力先ディレクトリ
#         user_ID: str
#         settings: dict
#         overwrite: bool - 既存CSVを上書きするか
#         archive_dir: str or None - fields.txt出力先
#
#     Returns:
#         (effective_breaths_count: int, df_breaths: pd.DataFrame)
#
#     CSV format: X, Wave1, Wave2, ...  (1行目がヘッダ)
#     """
#     from . import ExtractWaves as ew
#     ew.set_config(settings)
#     effective, df_breaths = ew.BreathsToCSVs(
#         df_breaths, df_frames, frames_root, output_dir, user_ID,
#         overwrite=overwrite, archive_dir=archive_dir,
#     )
#     print(f"[extract_waves] {effective} effective breaths")
#     return effective, df_breaths


# ============================================================
# ヘルパー関数
# ============================================================

def _format_time(frame, fps):
    """フレーム番号からHH:MM:SS:CC形式のタイムスタンプを生成。"""
    total_seconds = frame / fps
    s = int(total_seconds)
    centiseconds = int((total_seconds - s) * 100)
    h, rem = divmod(s, 3600)
    m, ss = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{ss:02d}:{centiseconds:02d}"
