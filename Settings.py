import os

# ============================================================
# ROI座標定義
# ============================================================

# 解像度ごとのROI定義: (height, width) -> {"キー名": [x, y, w, h]}
# sample_frame.jpgから座標を計測して設定する
ROI_BY_RESOLUTION = {
    # 例: 1280x720
    (720, 1280): {
        # "VTE": [x, y, w, h],
        # "BreathMark": [x, y, w, h],
    },
    # 例: 1920x1080
    # (1080, 1920): {
    #     "VTE": [x, y, w, h],
    #     "BreathMark": [x, y, w, h],
    # },
}

# デフォルト解像度（ROI_BY_RESOLUTIONに一致しない場合のフォールバック）
DEFAULT_RESOLUTION = (720, 1280)
DEFAULT_ROIs = ROI_BY_RESOLUTION.get(DEFAULT_RESOLUTION, {})

# ============================================================
# 共通設定
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 異常検出用リファレンス画像
REFERENCE_IMAGE_PATH = os.path.join(BASE_DIR, "sample_frame.jpg")

# 異常検出用ROI (x1, y1, x2, y2)
ROI_LIST_Abnormal_Detection = [
    # TODO: 必要に応じて定義
]
