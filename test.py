"""
Engine validation script.
Runs initial_ocr -> post_ocr -> (extract_waves) on sample.mp4, compares the result
with the reference CSVs in expected_output/, and judges PASS/FAIL by the criteria in test_spec.json.

Usage:
    python test.py
    python test.py --engine-dir /path/to/engine
"""

import json
import os
import sys
import importlib
import cv2
import pandas as pd
import numpy as np


def _load_test_spec(engine_dir):
    """Load test_spec.json."""
    spec_path = os.path.join(engine_dir, "test_spec.json")
    if not os.path.exists(spec_path):
        raise FileNotFoundError(f"test_spec.json not found: {spec_path}")
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _frame_generator(video_path, frames_dir):
    """Yield color frames from the video, also saving each as a JPEG."""
    os.makedirs(frames_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_path = os.path.join(frames_dir, f"frame_{frame_count:08d}.jpg")
        cv2.imwrite(frame_path, frame)
        yield frame
        frame_count += 1
    cap.release()


def _evaluate_metric(actual_values, expected_values, metric_def):
    """Evaluate according to the metric."""
    metric = metric_def["metric"]
    threshold = metric_def["threshold"]

    if metric == "match_rate":
        tolerance = metric_def.get("tolerance", 0)
        matches = 0
        total = 0
        for a, e in zip(actual_values, expected_values):
            if pd.isna(a) or pd.isna(e):
                continue
            total += 1
            if abs(float(a) - float(e)) <= tolerance:
                matches += 1
        value = matches / total if total > 0 else 0.0
        return {"metric": metric, "value": round(value, 4), "threshold": threshold, "passed": value >= threshold}

    elif metric == "count_tolerance":
        actual_count = int(sum(1 for v in actual_values if v == 1))
        expected_count = int(sum(1 for v in expected_values if v == 1))
        diff = abs(actual_count - expected_count)
        return {"metric": metric, "value": diff, "threshold": threshold, "passed": diff <= threshold}

    elif metric == "rmse":
        pairs = [(float(a), float(e)) for a, e in zip(actual_values, expected_values) if not pd.isna(a) and not pd.isna(e)]
        if not pairs:
            return {"metric": metric, "value": float("inf"), "threshold": threshold, "passed": False}
        mse = sum((a - e) ** 2 for a, e in pairs) / len(pairs)
        value = mse ** 0.5
        return {"metric": metric, "value": round(value, 4), "threshold": threshold, "passed": value <= threshold}

    elif metric == "correlation":
        a_arr = np.array([float(a) for a, e in zip(actual_values, expected_values) if not pd.isna(a) and not pd.isna(e)])
        e_arr = np.array([float(e) for a, e in zip(actual_values, expected_values) if not pd.isna(a) and not pd.isna(e)])
        if len(a_arr) < 2:
            return {"metric": metric, "value": 0.0, "threshold": threshold, "passed": False}
        value = float(np.corrcoef(a_arr, e_arr)[0, 1])
        return {"metric": metric, "value": round(value, 4), "threshold": threshold, "passed": value >= threshold}

    else:
        return {"metric": metric, "value": None, "threshold": threshold, "passed": False}


def run_test(engine_dir="."):
    """Main test runner."""
    engine_dir = os.path.abspath(engine_dir)
    print(f"Engine directory: {engine_dir}")

    # Load test_spec.json
    spec = _load_test_spec(engine_dir)
    video_path = os.path.join(engine_dir, spec["sample_video"])
    if not os.path.exists(video_path):
        print(f"ERROR: Sample video not found: {video_path}")
        sys.exit(1)

    expected_dir = os.path.join(engine_dir, "expected_output")
    if not os.path.exists(expected_dir):
        print(f"ERROR: expected_output directory not found: {expected_dir}")
        sys.exit(1)

    # Load the engine
    sys.path.insert(0, os.path.dirname(engine_dir))
    engine_name = os.path.basename(engine_dir)
    engine = importlib.import_module(f"{engine_name}.core")

    # Load engine_options.json
    options_path = os.path.join(engine_dir, "engine_options.json")
    with open(options_path, "r", encoding="utf-8") as f:
        engine_options = json.load(f)

    # Extract and analyze frames
    frames_dir = os.path.join(engine_dir, "_test_frames")
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    print(f"Total frames: {total_frames}")
    print("Running initial_ocr...")
    frames = _frame_generator(video_path, frames_dir)
    df_ocr = engine.initial_ocr(frames, total_frames, "test", engine_options, frames_dir=frames_dir)

    print("Running post_ocr...")
    df_frames, df_breaths = engine.post_ocr(df_ocr, 0, "test", engine_options)

    # Load the reference data
    expected_frames = pd.read_csv(os.path.join(expected_dir, "Frames.csv"))

    # Evaluate
    results = {}
    all_passed = True
    for key, metric_def in spec.get("outputs", {}).items():
        if key not in df_frames.columns or key not in expected_frames.columns:
            results[key] = {"metric": metric_def["metric"], "value": None, "threshold": metric_def["threshold"], "passed": False}
            all_passed = False
            continue
        result = _evaluate_metric(df_frames[key], expected_frames[key], metric_def)
        results[key] = result
        if not result["passed"]:
            all_passed = False

    # Build the report
    report = {
        "engine": engine_name,
        "engine_version": getattr(engine, "ENGINE_VERSION", "unknown"),
        "ventocr_tested": getattr(engine, "VENTOCR_TESTED", "unknown"),
        "total_frames": total_frames,
        "passed": all_passed,
        "results": results,
    }

    print("\n" + "=" * 60)
    print(f"Engine: {engine_name} v{report['engine_version']}")
    print(f"Result: {'PASSED' if all_passed else 'FAILED'}")
    print("-" * 60)
    for key, res in results.items():
        status = "PASS" if res["passed"] else "FAIL"
        print(f"  [{status}] {key}: {res['metric']} = {res['value']} (threshold: {res['threshold']})")
    print("=" * 60)

    # Write JSON
    report_path = os.path.join(engine_dir, "test_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved: {report_path}")

    # Delete the test frames
    import shutil
    if os.path.exists(frames_dir):
        shutil.rmtree(frames_dir)

    return report


if __name__ == "__main__":
    engine_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    report = run_test(engine_dir)
    sys.exit(0 if report["passed"] else 1)
