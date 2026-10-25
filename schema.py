# Settings schema shown in the VentOCR settings UI.
# type: int, float, bool, list, multiselect
# Keep it consistent with the default values in engine_options.json.

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
