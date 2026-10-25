import os

# ============================================================
# ROI coordinates
# ============================================================

# ROIs per resolution: (height, width) -> {"key name": [x, y, w, h]}
# Measure the coordinates on sample_frame.jpg and set them here
ROI_BY_RESOLUTION = {
    # Example: 1280x720
    (720, 1280): {
        # "VTE": [x, y, w, h],
        # "BreathMark": [x, y, w, h],
    },
    # Example: 1920x1080
    # (1080, 1920): {
    #     "VTE": [x, y, w, h],
    #     "BreathMark": [x, y, w, h],
    # },
}

# Default resolution (fallback when no entry in ROI_BY_RESOLUTION matches)
DEFAULT_RESOLUTION = (720, 1280)
DEFAULT_ROIs = ROI_BY_RESOLUTION.get(DEFAULT_RESOLUTION, {})

# ============================================================
# Common settings
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Reference image for abnormality detection
REFERENCE_IMAGE_PATH = os.path.join(BASE_DIR, "sample_frame.jpg")

# ROIs for abnormality detection (x1, y1, x2, y2)
ROI_LIST_Abnormal_Detection = [
    # TODO: define as needed
]
