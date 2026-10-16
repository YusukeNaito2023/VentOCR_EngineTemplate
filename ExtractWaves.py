"""
波形抽出モジュール（extract_waves実装時に使用）。
core.pyのextract_waves()から呼び出される。
"""

import cv2
import numpy as np
import pandas as pd
import os

# グローバル設定
_config = {}
SMOOTHING = True
IMPUTATION = True


def set_config(settings):
    """engine_options.jsonの設定を反映する。"""
    global _config, SMOOTHING, IMPUTATION
    _config = settings
    ew_settings = settings.get("extract_waves", {})
    SMOOTHING = ew_settings.get("smoothing", True)
    IMPUTATION = ew_settings.get("imputation", True)


def BreathsToCSVs(breaths, frames, frames_root, output_dir, user_id,
                  overwrite=False, archive_dir=None):
    """
    呼吸ごとに波形データをCSVに書き出す。

    Args:
        breaths: pd.DataFrame - 呼吸レベルのDataFrame
        frames: pd.DataFrame - フレームレベルのDataFrame
        frames_root: str - フレーム画像のディレクトリパス
        output_dir: str - CSV出力先
        user_id: str
        overwrite: bool
        archive_dir: str or None

    Returns:
        (effective_count: int, breaths: pd.DataFrame)

    出力CSV形式:
        X, Wave1, Wave2, ...
        1, 123.4, 567.8, ...
    """
    os.makedirs(output_dir, exist_ok=True)
    effective_count = 0

    # TODO: 呼吸ごとのCSV書き出しロジックを実装
    # for i, row in breaths.iterrows():
    #     breath_num = row["BreathNumber"]
    #     csv_path = os.path.join(output_dir, f"{breath_num}.csv")
    #     if not overwrite and os.path.exists(csv_path):
    #         continue
    #     # 波形データを抽出してCSVに書き出す
    #     effective_count += 1

    # fields.txtの書き出し（archive_dirが指定されている場合）
    if archive_dir is not None:
        _write_fields_txt(archive_dir)

    print(f"[BreathsToCSVs] {effective_count} breaths written")
    return effective_count, breaths


def _write_fields_txt(archive_dir):
    """fields.txtを書き出す。波形名と出力フィールドを定義。"""
    os.makedirs(archive_dir, exist_ok=True)
    fields_path = os.path.join(archive_dir, "fields.txt")
    with open(fields_path, "w") as f:
        f.write("[waves]\n")
        # TODO: 波形名を記載
        # f.write("Pressure\n")
        # f.write("Flow\n")
        # f.write("Volume\n")
        f.write("\n")
        f.write("[fields]\n")
        # TODO: 出力フィールドを記載
        f.write("\n")
