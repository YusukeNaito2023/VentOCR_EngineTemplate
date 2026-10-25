"""
[Engine Name] VentOCR Engine
Runs OCR analysis on display video from [target ventilator name].

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

# Engine version (release number managed by the developer)
ENGINE_VERSION = "0.1.0"

# VentOCR version this engine was tested with
VENTOCR_TESTED = "0.5.5"


def _to_gray(color_frame):
    """Convert a color frame (BGR) to grayscale."""
    return np.dot(color_frame[..., :3], [0.114, 0.587, 0.299]).astype(np.uint8)


def _load_frame_from_disk(frames_dir, frame_index):
    """Load a color frame JPEG from disk (for random access)."""
    path = os.path.join(frames_dir, f"frame_{frame_index:08d}.jpg")
    return cv2.imread(path)


# ============================================================
# initial_ocr
# ============================================================

def initial_ocr(frames, total_frames, subfolder, settings={},
                progress_callback=None, frames_dir=None):
    """
    Run OCR analysis on all frames.

    Args:
        frames: generator of color frames (BGR, numpy arrays).
                Frames are passed one at a time. Do not convert to a list.
                Use frames_dir if you need random access to past frames.
        total_frames: int - total number of frames
        subfolder: str - segment identifier
        settings: dict - settings loaded from engine_options.json
        progress_callback: callable(current, total, message) or None
        frames_dir: str - directory of saved frame JPEGs (for random access)

    Returns:
        pd.DataFrame - required columns: Frame (int, 0-indexed), BreathMark (int, 0 or 1)
                       Engine-specific value columns may be added
    """
    # TODO: get the required parameters from settings
    # ocr_settings = settings.get("initial_ocr", {})

    data = []

    with tqdm(total=total_frames, desc="OCR Processing") as pbar:
        if progress_callback is not None:
            progress_callback(current=0, total=total_frames, message="Running OCR")

        for frame_count, color_frame in enumerate(frames):
            row = {
                "Frame": frame_count,
                "BreathMark": 0,
                # TODO: add engine-specific output columns
                # "VTE": "",
                # "VTE_raw": "",
                # "VTE_conf": "0.00",
            }

            # Convert the color frame to grayscale (if needed for OCR)
            gray = _to_gray(color_frame)

            # TODO: implement ROI extraction and OCR
            # roi = gray[y:y+h, x:x+w]
            # result = reader.readtext(roi)

            # TODO: implement BreathMark detection
            # Use color_frame to work with the color frame directly

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
    Post-process the initial_ocr result into a frame DataFrame and a breath DataFrame.

    Args:
        df: pd.DataFrame - output of initial_ocr
        Analyze_Id: int - analysis ID
        user_ID: str - user ID
        settings: dict - settings loaded from engine_options.json

    Returns:
        (df_frames, df_breaths): tuple of DataFrames
        Columns that must be added to df_frames:
            - BreathNumber (int, 1-indexed, cumulative sum of BreathMark)
            - Time (str, "HH:MM:SS:CC" format)
            - Alert (str, empty string or alert reason)
            - Abnormal (int, 0 or 1)
    """
    fps = settings.get("post_ocr", {}).get("fps", 10)
    df = df.copy()

    # BreathNumber: cumulative sum of BreathMark (1-indexed)
    df["BreathNumber"] = df["BreathMark"].cumsum()
    df.loc[df["BreathNumber"] == 0, "BreathNumber"] = 1

    # Generate timestamps
    df["Time"] = df["Frame"].apply(lambda f: _format_time(f, fps))

    # Initialize required columns
    if "Alert" not in df.columns:
        df["Alert"] = ""
    if "Abnormal" not in df.columns:
        df["Abnormal"] = 0

    df_frames = df

    # Aggregate to breath level (first frame of each BreathNumber)
    df_breaths = df.loc[df.groupby("BreathNumber")["Frame"].idxmin()].copy()

    print(f"[post_ocr] {len(df_frames)} frames, {len(df_breaths)} breaths")
    return df_frames, df_breaths


# ============================================================
# extract_waves (optional)
# ============================================================

# extract_waves is optional. VentOCR checks for it with hasattr(Engine, 'extract_waves').
# Engines that do not extract waveforms may delete or comment out this function.

# def extract_waves(df_frames, df_breaths, frames_root, output_dir, user_ID,
#                   settings={}, overwrite=False, archive_dir=None):
#     """
#     Extract waveform data to a CSV per breath.
#
#     Args:
#         df_frames: pd.DataFrame - output of post_ocr (including the Abnormal column)
#         df_breaths: pd.DataFrame - breath-level DataFrame
#         frames_root: str - directory path of frame images
#         output_dir: str - output directory for CSVs
#         user_ID: str
#         settings: dict
#         overwrite: bool - whether to overwrite existing CSVs
#         archive_dir: str or None - output location for fields.txt
#
#     Returns:
#         (effective_breaths_count: int, df_breaths: pd.DataFrame)
#
#     CSV format: X, Wave1, Wave2, ...  (first row is the header)
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
# Helper functions
# ============================================================

def _format_time(frame, fps):
    """Build an HH:MM:SS:CC timestamp from a frame number."""
    total_seconds = frame / fps
    s = int(total_seconds)
    centiseconds = int((total_seconds - s) * 100)
    h, rem = divmod(s, 3600)
    m, ss = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{ss:02d}:{centiseconds:02d}"
