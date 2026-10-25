"""
Waveform extraction module (used when implementing extract_waves).
Called from extract_waves() in core.py.
"""

import cv2
import numpy as np
import pandas as pd
import os

# Global settings
_config = {}
SMOOTHING = True
IMPUTATION = True


def set_config(settings):
    """Apply the settings from engine_options.json."""
    global _config, SMOOTHING, IMPUTATION
    _config = settings
    ew_settings = settings.get("extract_waves", {})
    SMOOTHING = ew_settings.get("smoothing", True)
    IMPUTATION = ew_settings.get("imputation", True)


def BreathsToCSVs(breaths, frames, frames_root, output_dir, user_id,
                  overwrite=False, archive_dir=None):
    """
    Write waveform data to a CSV per breath.

    Args:
        breaths: pd.DataFrame - breath-level DataFrame
        frames: pd.DataFrame - frame-level DataFrame
        frames_root: str - directory path of frame images
        output_dir: str - output directory for CSVs
        user_id: str
        overwrite: bool
        archive_dir: str or None

    Returns:
        (effective_count: int, breaths: pd.DataFrame)

    Output CSV format:
        X, Wave1, Wave2, ...
        1, 123.4, 567.8, ...
    """
    os.makedirs(output_dir, exist_ok=True)
    effective_count = 0

    # TODO: implement writing one CSV per breath
    # for i, row in breaths.iterrows():
    #     breath_num = row["BreathNumber"]
    #     csv_path = os.path.join(output_dir, f"{breath_num}.csv")
    #     if not overwrite and os.path.exists(csv_path):
    #         continue
    #     # Extract the waveform data and write it to the CSV
    #     effective_count += 1

    # Write fields.txt (when archive_dir is given)
    if archive_dir is not None:
        _write_fields_txt(archive_dir)

    print(f"[BreathsToCSVs] {effective_count} breaths written")
    return effective_count, breaths


def _write_fields_txt(archive_dir):
    """Write fields.txt, which defines the wave names and output fields."""
    os.makedirs(archive_dir, exist_ok=True)
    fields_path = os.path.join(archive_dir, "fields.txt")
    with open(fields_path, "w") as f:
        f.write("[waves]\n")
        # TODO: list the wave names
        # f.write("Pressure\n")
        # f.write("Flow\n")
        # f.write("Volume\n")
        f.write("\n")
        f.write("[fields]\n")
        # TODO: list the output fields
        f.write("\n")
