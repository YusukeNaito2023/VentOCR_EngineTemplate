# VentOCR設定UIで表示される設定スキーマ。
# type: int, float, bool, list, multiselect
# engine_options.json のデフォルト値と対応させること。

ENGINE_SETTINGS_SCHEMA = {
    "initial_ocr": {
        "use_gpu": {
            "type": "bool",
            "default": True,
            "label": "Enable GPU Processing"
        },
        "sampling_size": {
            "type": "int",
            "default": 10,
            "label": "Sampling Interval (Frames)"
        },
    },
    "post_ocr": {
        "fps": {
            "type": "int",
            "default": 10,
            "label": "Video FPS"
        },
    },
}
