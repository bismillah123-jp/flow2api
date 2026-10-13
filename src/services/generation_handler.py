"""Generation handler for Flow2API"""

import asyncio
import base64
import json
import math
import time
from pathlib import Path
from typing import Optional, AsyncGenerator, List, Dict, Any
from ..core.logger import debug_logger
from ..core.config import config
from ..core.monitoring import record_generation_result
from ..core.models import Task, RequestLog
from ..core.account_tiers import (
    PAYGATE_TIER_NOT_PAID,
    get_paygate_tier_label,
    get_required_paygate_tier_for_model,
    normalize_user_paygate_tier,
    supports_model_for_tier,
)
from .file_cache import FileCache


def _video_poll_attempt_budget(
    timeout_seconds: float,
    poll_interval: float,
    *,
    upsample: bool = False,
) -> int:
    interval = max(0.1, float(poll_interval or 0))
    timeout = max(interval, float(timeout_seconds or 0))
    attempts = max(1, math.ceil(timeout / interval))
    return attempts * (3 if upsample else 1)


# Model configuration
MODEL_CONFIG = {
    # Generate gambar - GEM_PIX_2 (Gemini 3.0 Pro)
    "gemini-3.0-pro-image-landscape": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE",
    },
    "gemini-3.0-pro-image-portrait": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_PORTRAIT",
    },
    "gemini-3.0-pro-image-square": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_SQUARE",
    },
    "gemini-3.0-pro-image-four-three": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE_FOUR_THREE",
    },
    "gemini-3.0-pro-image-three-four": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR",
    },
    # Generate gambar - GEM_PIX_2 (Gemini 3.0 Pro) versi upscale 2K
    "gemini-3.0-pro-image-landscape-2k": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_2K",
    },
    "gemini-3.0-pro-image-portrait-2k": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_PORTRAIT",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_2K",
    },
    "gemini-3.0-pro-image-square-2k": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_SQUARE",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_2K",
    },
    "gemini-3.0-pro-image-four-three-2k": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE_FOUR_THREE",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_2K",
    },
    "gemini-3.0-pro-image-three-four-2k": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_2K",
    },
    # Generate gambar - GEM_PIX_2 (Gemini 3.0 Pro) versi upscale 4K
    "gemini-3.0-pro-image-landscape-4k": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_4K",
    },
    "gemini-3.0-pro-image-portrait-4k": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_PORTRAIT",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_4K",
    },
    "gemini-3.0-pro-image-square-4k": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_SQUARE",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_4K",
    },
    "gemini-3.0-pro-image-four-three-4k": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE_FOUR_THREE",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_4K",
    },
    "gemini-3.0-pro-image-three-four-4k": {
        "type": "image",
        "model_name": "GEM_PIX_2",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_4K",
    },
    # Generate gambar - BELUGA (Nano Banana 2.1)
    "gemini-3.1-flash-image-landscape": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE",
    },
    "gemini-3.1-flash-image-portrait": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_PORTRAIT",
    },
    "gemini-3.1-flash-image-square": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_SQUARE",
    },
    "gemini-3.1-flash-image-four-three": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE_FOUR_THREE",
    },
    "gemini-3.1-flash-image-three-four": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR",
    },
    "gemini-3.1-flash-image-landscape-2k": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_2K",
    },
    "gemini-3.1-flash-image-portrait-2k": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_PORTRAIT",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_2K",
    },
    "gemini-3.1-flash-image-square-2k": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_SQUARE",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_2K",
    },
    "gemini-3.1-flash-image-four-three-2k": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE_FOUR_THREE",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_2K",
    },
    "gemini-3.1-flash-image-three-four-2k": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_2K",
    },
    "gemini-3.1-flash-image-landscape-4k": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_4K",
    },
    "gemini-3.1-flash-image-portrait-4k": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_PORTRAIT",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_4K",
    },
    "gemini-3.1-flash-image-square-4k": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_SQUARE",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_4K",
    },
    "gemini-3.1-flash-image-four-three-4k": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_LANDSCAPE_FOUR_THREE",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_4K",
    },
    "gemini-3.1-flash-image-three-four-4k": {
        "type": "image",
        "model_name": "BELUGA",
        "aspect_ratio": "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR",
        "upsample": "UPSAMPLE_IMAGE_RESOLUTION_4K",
    },
    # ========== Text-to-video (T2V) ==========
    # nggak dukung upload gambar, cuma pakai prompt teks
    # veo_3_1_t2v_fast_portrait (portrait)
    # nama model upstream: veo_3_1_t2v_fast_portrait
    "veo_3_1_t2v_fast_portrait": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast_portrait",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": False,
        "use_v2_model_config": True,
    },
    # veo_3_1_t2v_fast_landscape (landscape)
    # nama model upstream: veo_3_1_t2v_fast
    "veo_3_1_t2v_fast_landscape": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": False,
        "use_v2_model_config": True,
    },
    # veo_3_1_t2v_fast_ultra (portrait/landscape)
    "veo_3_1_t2v_fast_portrait_ultra": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast_portrait_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": False,
        "use_v2_model_config": True,
    },
    "veo_3_1_t2v_fast_ultra": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": False,
        "use_v2_model_config": True,
    },
    # veo_3_1_t2v_fast_ultra_relaxed (portrait/landscape)
    "veo_3_1_t2v_fast_portrait_ultra_relaxed": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast_portrait_ultra_relaxed",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": False,
        "use_v2_model_config": True,
    },
    "veo_3_1_t2v_fast_ultra_relaxed": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast_ultra_relaxed",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": False,
        "use_v2_model_config": True,
    },
    # veo_3_1_t2v (portrait/landscape)
    "veo_3_1_t2v_portrait": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast_portrait",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": False,
        "use_v2_model_config": True,
    },
    "veo_3_1_t2v_landscape": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": False,
        "use_v2_model_config": True,
    },
    # veo_3_1_t2v_lite (portrait/landscape)
    "veo_3_1_t2v_lite_portrait": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_lite",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": False,
        "use_v2_model_config": True,
        "allow_tier_upgrade": False,
    },
    "veo_3_1_t2v_lite_landscape": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_lite",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": False,
        "use_v2_model_config": True,
        "allow_tier_upgrade": False,
    },
    # ========== Model first-last frame (I2V - Image to Video) ==========
    # dukung 1-2 gambar: 1 jadi first frame, 2 jadi first-last frame
    # veo_3_1_i2v_s_fast_fl (perlu tambah portrait/landscape)
    "veo_3_1_i2v_s_fast_portrait_fl": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_s_fast_portrait_fl",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 1,
        "max_images": 2,
    },
    "veo_3_1_i2v_s_fast_fl": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_s_fast_fl",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 1,
        "max_images": 2,
    },
    # veo_3_1_i2v_s_fast_ultra (portrait/landscape)
    "veo_3_1_i2v_s_fast_portrait_ultra_fl": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_s_fast_portrait_ultra_fl",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 1,
        "max_images": 2,
    },
    "veo_3_1_i2v_s_fast_ultra_fl": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_s_fast_ultra_fl",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 1,
        "max_images": 2,
    },
    # veo_3_1_i2v_s_fast_ultra_relaxed (perlu tambah portrait/landscape)
    "veo_3_1_i2v_s_fast_portrait_ultra_relaxed": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_s_fast_portrait_ultra_relaxed",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 1,
        "max_images": 2,
    },
    "veo_3_1_i2v_s_fast_ultra_relaxed": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_s_fast_ultra_relaxed",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 1,
        "max_images": 2,
    },
    # veo_3_1_i2v_s (perlu tambah portrait/landscape)
    "veo_3_1_i2v_s_portrait": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_s",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 1,
        "max_images": 2,
    },
    "veo_3_1_i2v_s_landscape": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_s",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 1,
        "max_images": 2,
    },
    # veo_3_1_i2v_lite (portrait/landscape, cuma first frame)
    "veo_3_1_i2v_lite_portrait": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_lite",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 1,
        "max_images": 1,
        "use_v2_model_config": True,
        "allow_tier_upgrade": False,
    },
    "veo_3_1_i2v_lite_landscape": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_lite",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 1,
        "max_images": 1,
        "use_v2_model_config": True,
        "allow_tier_upgrade": False,
    },
    # veo_3_1_interpolation_lite (portrait/landscape, first-last frame)
    "veo_3_1_interpolation_lite_portrait": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_interpolation_lite",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 2,
        "max_images": 2,
        "use_v2_model_config": True,
        "allow_tier_upgrade": False,
    },
    "veo_3_1_interpolation_lite_landscape": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_interpolation_lite",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 2,
        "max_images": 2,
        "use_v2_model_config": True,
        "allow_tier_upgrade": False,
    },
    # ========== Generate multi-gambar (R2V - Reference Images to Video) ==========
    # protokol upstream sekarang maksimal 3 gambar referensi
    # veo_3_1_r2v_fast (portrait/landscape)
    "veo_3_1_r2v_fast_portrait": {
        "type": "video",
        "video_type": "r2v",
        "model_key": "veo_3_1_r2v_fast_portrait",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 0,
        "max_images": 3,
    },
    "veo_3_1_r2v_fast": {
        "type": "video",
        "video_type": "r2v",
        "model_key": "veo_3_1_r2v_fast_landscape",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 0,
        "max_images": 3,
    },
    # veo_3_1_r2v_fast_ultra (portrait/landscape)
    "veo_3_1_r2v_fast_portrait_ultra": {
        "type": "video",
        "video_type": "r2v",
        "model_key": "veo_3_1_r2v_fast_portrait_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 0,
        "max_images": 3,
    },
    "veo_3_1_r2v_fast_ultra": {
        "type": "video",
        "video_type": "r2v",
        "model_key": "veo_3_1_r2v_fast_landscape_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 0,
        "max_images": 3,
    },
    # veo_3_1_r2v_fast_ultra_relaxed (portrait/landscape)
    "veo_3_1_r2v_fast_portrait_ultra_relaxed": {
        "type": "video",
        "video_type": "r2v",
        "model_key": "veo_3_1_r2v_fast_portrait_ultra_relaxed",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 0,
        "max_images": 3,
    },
    "veo_3_1_r2v_fast_ultra_relaxed": {
        "type": "video",
        "video_type": "r2v",
        "model_key": "veo_3_1_r2v_fast_landscape_ultra_relaxed",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 0,
        "max_images": 3,
    },
    # ========== Upscale video (Video Upsampler) ==========
    # cuma 3.1 yang dukung, harus generate video dulu baru upscale, bisa butuh 30 menit
    # T2V versi upscale 4K
    "veo_3_1_t2v_fast_portrait_4k": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast_portrait",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": False,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_4K",
            "model_key": "veo_3_1_upsampler_4k",
        },
    },
    "veo_3_1_t2v_fast_4k": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": False,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_4K",
            "model_key": "veo_3_1_upsampler_4k",
        },
    },
    "veo_3_1_t2v_fast_portrait_ultra_4k": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast_portrait_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": False,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_4K",
            "model_key": "veo_3_1_upsampler_4k",
        },
    },
    "veo_3_1_t2v_fast_ultra_4k": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": False,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_4K",
            "model_key": "veo_3_1_upsampler_4k",
        },
    },
    # T2V versi upscale 1080P
    "veo_3_1_t2v_fast_portrait_1080p": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast_portrait",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": False,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_1080P",
            "model_key": "veo_3_1_upsampler_1080p",
        },
    },
    "veo_3_1_t2v_fast_1080p": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": False,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_1080P",
            "model_key": "veo_3_1_upsampler_1080p",
        },
    },
    "veo_3_1_t2v_fast_portrait_ultra_1080p": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast_portrait_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": False,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_1080P",
            "model_key": "veo_3_1_upsampler_1080p",
        },
    },
    "veo_3_1_t2v_fast_ultra_1080p": {
        "type": "video",
        "video_type": "t2v",
        "model_key": "veo_3_1_t2v_fast_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": False,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_1080P",
            "model_key": "veo_3_1_upsampler_1080p",
        },
    },
    # I2V versi upscale 4K
    "veo_3_1_i2v_s_fast_portrait_ultra_fl_4k": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_s_fast_portrait_ultra_fl",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 1,
        "max_images": 2,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_4K",
            "model_key": "veo_3_1_upsampler_4k",
        },
    },
    "veo_3_1_i2v_s_fast_ultra_fl_4k": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_s_fast_ultra_fl",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 1,
        "max_images": 2,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_4K",
            "model_key": "veo_3_1_upsampler_4k",
        },
    },
    # I2V versi upscale 1080P
    "veo_3_1_i2v_s_fast_portrait_ultra_fl_1080p": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_s_fast_portrait_ultra_fl",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 1,
        "max_images": 2,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_1080P",
            "model_key": "veo_3_1_upsampler_1080p",
        },
    },
    "veo_3_1_i2v_s_fast_ultra_fl_1080p": {
        "type": "video",
        "video_type": "i2v",
        "model_key": "veo_3_1_i2v_s_fast_ultra_fl",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 1,
        "max_images": 2,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_1080P",
            "model_key": "veo_3_1_upsampler_1080p",
        },
    },
    # R2V versi upscale 4K
    "veo_3_1_r2v_fast_portrait_ultra_4k": {
        "type": "video",
        "video_type": "r2v",
        "model_key": "veo_3_1_r2v_fast_portrait_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 0,
        "max_images": 3,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_4K",
            "model_key": "veo_3_1_upsampler_4k",
        },
    },
    "veo_3_1_r2v_fast_ultra_4k": {
        "type": "video",
        "video_type": "r2v",
        "model_key": "veo_3_1_r2v_fast_landscape_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 0,
        "max_images": 3,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_4K",
            "model_key": "veo_3_1_upsampler_4k",
        },
    },
    # R2V versi upscale 1080P
    "veo_3_1_r2v_fast_portrait_ultra_1080p": {
        "type": "video",
        "video_type": "r2v",
        "model_key": "veo_3_1_r2v_fast_portrait_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 0,
        "max_images": 3,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_1080P",
            "model_key": "veo_3_1_upsampler_1080p",
        },
    },
    "veo_3_1_r2v_fast_ultra_1080p": {
        "type": "video",
        "video_type": "r2v",
        "model_key": "veo_3_1_r2v_fast_landscape_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 0,
        "max_images": 3,
        "upsample": {
            "resolution": "VIDEO_RESOLUTION_1080P",
            "model_key": "veo_3_1_upsampler_1080p",
        },
    },
    # ========== Lanjutin video (Extend - Video Continuation) ==========
    # lanjutkan video yang sudah digenerate 7 detik, maksimal 20x (paling panjang 148 detik)
    # wajib kasih mediaGenerationId video sumber
    # VEO 3.1 Extend (portrait/landscape)
    "veo_3_1_extend_portrait": {
        "type": "video",
        "video_type": "extend",
        "model_key": "veo_3_1_extend_fast_portrait_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": False,
        "requires_video_id": True,
    },
    "veo_3_1_extend": {
        "type": "video",
        "video_type": "extend",
        "model_key": "veo_3_1_extend_fast_ultra",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": False,
        "requires_video_id": True,
    },
    # ========== Gemini Omni Flash ==========
    # 2026-05-26 hasil test request upstream asli:
    # - teks murni -> YhhmEf, videoModelKey=abra_t2v_8s
    # - gambar referensi -> MZZa6b, videoModelKey=abra_r2v_8s
    "omni": {
        "type": "video",
        "video_type": "omni",
        "model_key": "abra_t2v_8s",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "supports_images": True,
        "min_images": 0,
        "max_images": 3,
        "use_v2_model_config": True,
        "allow_tier_upgrade": False,
        "reference_model_key": "abra_r2v_8s",
        "reference_duration": 8,
        "reference_model_display_name": "Omni Flash",
    },
    "omni_portrait": {
        "type": "video",
        "video_type": "omni",
        "model_key": "abra_t2v_8s",
        "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
        "supports_images": True,
        "min_images": 0,
        "max_images": 3,
        "use_v2_model_config": True,
        "allow_tier_upgrade": False,
        "reference_model_key": "abra_r2v_8s",
        "reference_duration": 8,
        "reference_model_display_name": "Omni Flash",
    },
}


def _make_t2v_config(
    model_key: str,
    aspect_ratio: str,
    *,
    use_v2_model_config: bool = False,
    allow_tier_upgrade: bool = True,
    upsample: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {
        "type": "video",
        "video_type": "t2v",
        "model_key": model_key,
        "aspect_ratio": aspect_ratio,
        "supports_images": False,
    }
    if use_v2_model_config:
        cfg["use_v2_model_config"] = True
    if not allow_tier_upgrade:
        cfg["allow_tier_upgrade"] = False
    if upsample:
        cfg["upsample"] = upsample
    return cfg


def _make_i2v_config(
    model_key: str,
    aspect_ratio: str,
    *,
    min_images: int = 1,
    max_images: int = 2,
    use_v2_model_config: bool = False,
    allow_tier_upgrade: bool = True,
    upsample: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {
        "type": "video",
        "video_type": "i2v",
        "model_key": model_key,
        "aspect_ratio": aspect_ratio,
        "supports_images": True,
        "min_images": min_images,
        "max_images": max_images,
    }
    if use_v2_model_config:
        cfg["use_v2_model_config"] = True
    if not allow_tier_upgrade:
        cfg["allow_tier_upgrade"] = False
    if upsample:
        cfg["upsample"] = upsample
    return cfg


def _apply_veo_3_1_model_updates():
    """Keep the public aliases aligned with the current Veo 3.1 model families."""
    landscape = "VIDEO_ASPECT_RATIO_LANDSCAPE"
    portrait = "VIDEO_ASPECT_RATIO_PORTRAIT"

    def add_alias(alias: str, target: str):
        MODEL_CONFIG[alias] = dict(MODEL_CONFIG[target])

    def add_default_duration_aliases(
        base_alias: str,
        landscape_target: str,
        portrait_target: str,
        *,
        fl_suffix: bool = False,
    ):
        if fl_suffix:
            add_alias(f"{base_alias}_8s_fl", landscape_target)
            add_alias(f"{base_alias}_portrait_8s_fl", portrait_target)
            add_alias(f"{base_alias}_landscape_8s_fl", landscape_target)
            return

        add_alias(f"{base_alias}_8s", landscape_target)
        add_alias(f"{base_alias}_portrait_8s", portrait_target)
        add_alias(f"{base_alias}_landscape_8s", landscape_target)

    def add_default_duration_upsample_aliases(
        base_alias: str,
        resolution_name: str,
        landscape_target: str,
        portrait_target: str,
    ):
        add_alias(f"{base_alias}_8s_{resolution_name}", landscape_target)
        add_alias(f"{base_alias}_portrait_8s_{resolution_name}", portrait_target)
        add_alias(f"{base_alias}_landscape_8s_{resolution_name}", landscape_target)

    # Non-fast/non-lite Veo 3.1 aliases must call Quality upstream keys.
    MODEL_CONFIG["veo_3_1_t2v_landscape"].update({"model_key": "veo_3_1_t2v"})
    MODEL_CONFIG["veo_3_1_t2v_portrait"].update({"model_key": "veo_3_1_t2v_portrait"})
    MODEL_CONFIG["veo_3_1_i2v_s_landscape"].update({"model_key": "veo_3_1_i2v_s_fl"})
    MODEL_CONFIG["veo_3_1_i2v_s_portrait"].update(
        {"model_key": "veo_3_1_i2v_s_portrait_fl"}
    )
    MODEL_CONFIG["veo_3_1_extend"].update({"model_key": "veo_3_1_extend_landscape"})
    MODEL_CONFIG["veo_3_1_extend_portrait"].update(
        {"model_key": "veo_3_1_extend_portrait"}
    )

    for seconds in (4, 6):
        suffix = f"{seconds}s"

        # T2V duration variants.
        MODEL_CONFIG[f"veo_3_1_t2v_fast_{suffix}"] = _make_t2v_config(
            f"veo_3_1_t2v_fast_{suffix}", landscape
        )
        MODEL_CONFIG[f"veo_3_1_t2v_fast_portrait_{suffix}"] = _make_t2v_config(
            f"veo_3_1_t2v_fast_{suffix}", portrait
        )
        MODEL_CONFIG[f"veo_3_1_t2v_lite_{suffix}_landscape"] = _make_t2v_config(
            f"veo_3_1_t2v_lite_{suffix}",
            landscape,
            use_v2_model_config=True,
            allow_tier_upgrade=False,
        )
        MODEL_CONFIG[f"veo_3_1_t2v_lite_{suffix}_portrait"] = _make_t2v_config(
            f"veo_3_1_t2v_lite_{suffix}",
            portrait,
            use_v2_model_config=True,
            allow_tier_upgrade=False,
        )
        MODEL_CONFIG[f"veo_3_1_t2v_{suffix}"] = _make_t2v_config(
            f"veo_3_1_t2v_quality_{suffix}", landscape
        )
        MODEL_CONFIG[f"veo_3_1_t2v_portrait_{suffix}"] = _make_t2v_config(
            f"veo_3_1_t2v_quality_{suffix}", portrait
        )

        # I2V duration variants. FL keys are used for 2 images; the single-image path strips "_fl".
        MODEL_CONFIG[f"veo_3_1_i2v_s_fast_{suffix}_fl"] = _make_i2v_config(
            f"veo_3_1_i2v_s_fast_{suffix}_fl", landscape
        )
        MODEL_CONFIG[f"veo_3_1_i2v_s_fast_portrait_{suffix}_fl"] = _make_i2v_config(
            f"veo_3_1_i2v_s_fast_{suffix}_fl", portrait
        )
        MODEL_CONFIG[f"veo_3_1_i2v_lite_{suffix}_landscape"] = _make_i2v_config(
            f"veo_3_1_i2v_s_lite_{suffix}",
            landscape,
            min_images=1,
            max_images=1,
            use_v2_model_config=True,
            allow_tier_upgrade=False,
        )
        MODEL_CONFIG[f"veo_3_1_i2v_lite_{suffix}_portrait"] = _make_i2v_config(
            f"veo_3_1_i2v_s_lite_{suffix}",
            portrait,
            min_images=1,
            max_images=1,
            use_v2_model_config=True,
            allow_tier_upgrade=False,
        )
        MODEL_CONFIG[f"veo_3_1_interpolation_lite_{suffix}_landscape"] = (
            _make_i2v_config(
            f"veo_3_1_i2v_s_lite_{suffix}_fl",
            landscape,
            min_images=2,
            max_images=2,
            use_v2_model_config=True,
            allow_tier_upgrade=False,
        )
        )
        MODEL_CONFIG[f"veo_3_1_interpolation_lite_{suffix}_portrait"] = (
            _make_i2v_config(
            f"veo_3_1_i2v_s_lite_{suffix}_fl",
            portrait,
            min_images=2,
            max_images=2,
            use_v2_model_config=True,
            allow_tier_upgrade=False,
        )
        )
        MODEL_CONFIG[f"veo_3_1_i2v_s_{suffix}"] = _make_i2v_config(
            f"veo_3_1_i2v_s_quality_{suffix}_fl", landscape
        )
        MODEL_CONFIG[f"veo_3_1_i2v_s_portrait_{suffix}"] = _make_i2v_config(
            f"veo_3_1_i2v_s_quality_{suffix}_fl", portrait
        )

        for resolution_name, resolution, upsampler_model_key in (
            ("4k", "VIDEO_RESOLUTION_4K", "veo_3_1_upsampler_4k"),
            ("1080p", "VIDEO_RESOLUTION_1080P", "veo_3_1_upsampler_1080p"),
        ):
            upsample = {"resolution": resolution, "model_key": upsampler_model_key}
            MODEL_CONFIG[f"veo_3_1_t2v_{suffix}_{resolution_name}"] = _make_t2v_config(
                f"veo_3_1_t2v_quality_{suffix}", landscape, upsample=upsample
            )
            MODEL_CONFIG[f"veo_3_1_t2v_portrait_{suffix}_{resolution_name}"] = (
                _make_t2v_config(
                f"veo_3_1_t2v_quality_{suffix}", portrait, upsample=upsample
            )
            )
            MODEL_CONFIG[f"veo_3_1_i2v_s_{suffix}_{resolution_name}"] = (
                _make_i2v_config(
                f"veo_3_1_i2v_s_quality_{suffix}_fl", landscape, upsample=upsample
            )
            )
            MODEL_CONFIG[f"veo_3_1_i2v_s_portrait_{suffix}_{resolution_name}"] = (
                _make_i2v_config(
                f"veo_3_1_i2v_s_quality_{suffix}_fl", portrait, upsample=upsample
            )
            )

    for resolution_name, resolution, upsampler_model_key in (
        ("4k", "VIDEO_RESOLUTION_4K", "veo_3_1_upsampler_4k"),
        ("1080p", "VIDEO_RESOLUTION_1080P", "veo_3_1_upsampler_1080p"),
    ):
        upsample = {"resolution": resolution, "model_key": upsampler_model_key}
        MODEL_CONFIG[f"veo_3_1_t2v_{resolution_name}"] = _make_t2v_config(
            "veo_3_1_t2v", landscape, upsample=upsample
        )
        MODEL_CONFIG[f"veo_3_1_t2v_portrait_{resolution_name}"] = _make_t2v_config(
            "veo_3_1_t2v_portrait", portrait, upsample=upsample
        )
        MODEL_CONFIG[f"veo_3_1_i2v_s_{resolution_name}"] = _make_i2v_config(
            "veo_3_1_i2v_s_fl", landscape, upsample=upsample
        )
        MODEL_CONFIG[f"veo_3_1_i2v_s_portrait_{resolution_name}"] = _make_i2v_config(
            "veo_3_1_i2v_s_portrait_fl", portrait, upsample=upsample
        )

    for seconds in (4, 6):
        suffix = f"{seconds}s"

        # Explicit landscape names for /v1/models; short landscape names remain compatible.
        add_alias(f"veo_3_1_t2v_fast_landscape_{suffix}", f"veo_3_1_t2v_fast_{suffix}")
        add_alias(f"veo_3_1_t2v_landscape_{suffix}", f"veo_3_1_t2v_{suffix}")
        add_alias(
            f"veo_3_1_i2v_s_fast_landscape_{suffix}_fl",
            f"veo_3_1_i2v_s_fast_{suffix}_fl",
        )
        add_alias(f"veo_3_1_i2v_s_landscape_{suffix}", f"veo_3_1_i2v_s_{suffix}")

        add_alias(
            f"veo_3_1_t2v_lite_landscape_{suffix}",
            f"veo_3_1_t2v_lite_{suffix}_landscape",
        )
        add_alias(
            f"veo_3_1_t2v_lite_portrait_{suffix}", f"veo_3_1_t2v_lite_{suffix}_portrait"
        )
        add_alias(
            f"veo_3_1_i2v_lite_landscape_{suffix}",
            f"veo_3_1_i2v_lite_{suffix}_landscape",
        )
        add_alias(
            f"veo_3_1_i2v_lite_portrait_{suffix}", f"veo_3_1_i2v_lite_{suffix}_portrait"
        )
        add_alias(
            f"veo_3_1_interpolation_lite_landscape_{suffix}",
            f"veo_3_1_interpolation_lite_{suffix}_landscape",
        )
        add_alias(
            f"veo_3_1_interpolation_lite_portrait_{suffix}",
            f"veo_3_1_interpolation_lite_{suffix}_portrait",
        )

        for resolution_name in ("4k", "1080p"):
            add_alias(
                f"veo_3_1_t2v_landscape_{suffix}_{resolution_name}",
                f"veo_3_1_t2v_{suffix}_{resolution_name}",
            )
            add_alias(
                f"veo_3_1_i2v_s_landscape_{suffix}_{resolution_name}",
                f"veo_3_1_i2v_s_{suffix}_{resolution_name}",
            )

    for resolution_name in ("4k", "1080p"):
        add_alias(
            f"veo_3_1_t2v_landscape_{resolution_name}", f"veo_3_1_t2v_{resolution_name}"
        )
        add_alias(
            f"veo_3_1_i2v_s_landscape_{resolution_name}",
            f"veo_3_1_i2v_s_{resolution_name}",
        )

    add_alias("veo_3_1_r2v_fast_landscape", "veo_3_1_r2v_fast")
    add_alias("veo_3_1_r2v_fast_landscape_ultra", "veo_3_1_r2v_fast_ultra")
    add_alias(
        "veo_3_1_r2v_fast_landscape_ultra_relaxed", "veo_3_1_r2v_fast_ultra_relaxed"
    )
    add_alias("veo_3_1_r2v_fast_landscape_ultra_4k", "veo_3_1_r2v_fast_ultra_4k")
    add_alias("veo_3_1_r2v_fast_landscape_ultra_1080p", "veo_3_1_r2v_fast_ultra_1080p")

    add_default_duration_aliases(
        "veo_3_1_t2v_fast",
        "veo_3_1_t2v_fast_landscape",
        "veo_3_1_t2v_fast_portrait",
    )
    add_default_duration_aliases(
        "veo_3_1_t2v",
        "veo_3_1_t2v_landscape",
        "veo_3_1_t2v_portrait",
    )
    add_default_duration_aliases(
        "veo_3_1_i2v_s_fast",
        "veo_3_1_i2v_s_fast_fl",
        "veo_3_1_i2v_s_fast_portrait_fl",
        fl_suffix=True,
    )
    add_default_duration_aliases(
        "veo_3_1_i2v_s",
        "veo_3_1_i2v_s_landscape",
        "veo_3_1_i2v_s_portrait",
    )
    add_default_duration_aliases(
        "veo_3_1_r2v_fast",
        "veo_3_1_r2v_fast",
        "veo_3_1_r2v_fast_portrait",
    )
    add_alias("veo_3_1_r2v_fast_ultra_8s", "veo_3_1_r2v_fast_ultra")
    add_alias("veo_3_1_r2v_fast_portrait_ultra_8s", "veo_3_1_r2v_fast_portrait_ultra")
    add_alias("veo_3_1_r2v_fast_landscape_ultra_8s", "veo_3_1_r2v_fast_ultra")
    add_alias(
        "veo_3_1_r2v_fast_ultra_relaxed_8s",
        "veo_3_1_r2v_fast_ultra_relaxed",
    )
    add_alias(
        "veo_3_1_r2v_fast_portrait_ultra_relaxed_8s",
        "veo_3_1_r2v_fast_portrait_ultra_relaxed",
    )
    add_alias(
        "veo_3_1_r2v_fast_landscape_ultra_relaxed_8s",
        "veo_3_1_r2v_fast_ultra_relaxed",
    )

    add_alias("veo_3_1_t2v_lite_8s_landscape", "veo_3_1_t2v_lite_landscape")
    add_alias("veo_3_1_t2v_lite_8s_portrait", "veo_3_1_t2v_lite_portrait")
    add_alias("veo_3_1_t2v_lite_landscape_8s", "veo_3_1_t2v_lite_landscape")
    add_alias("veo_3_1_t2v_lite_portrait_8s", "veo_3_1_t2v_lite_portrait")
    add_alias("veo_3_1_i2v_lite_8s_landscape", "veo_3_1_i2v_lite_landscape")
    add_alias("veo_3_1_i2v_lite_8s_portrait", "veo_3_1_i2v_lite_portrait")
    add_alias("veo_3_1_i2v_lite_landscape_8s", "veo_3_1_i2v_lite_landscape")
    add_alias("veo_3_1_i2v_lite_portrait_8s", "veo_3_1_i2v_lite_portrait")
    add_alias(
        "veo_3_1_interpolation_lite_8s_landscape",
        "veo_3_1_interpolation_lite_landscape",
    )
    add_alias(
        "veo_3_1_interpolation_lite_8s_portrait",
        "veo_3_1_interpolation_lite_portrait",
    )
    add_alias(
        "veo_3_1_interpolation_lite_landscape_8s",
        "veo_3_1_interpolation_lite_landscape",
    )
    add_alias(
        "veo_3_1_interpolation_lite_portrait_8s",
        "veo_3_1_interpolation_lite_portrait",
    )

    for resolution_name in ("4k", "1080p"):
        add_default_duration_upsample_aliases(
            "veo_3_1_t2v",
            resolution_name,
            f"veo_3_1_t2v_{resolution_name}",
            f"veo_3_1_t2v_portrait_{resolution_name}",
        )
        add_default_duration_upsample_aliases(
            "veo_3_1_i2v_s",
            resolution_name,
            f"veo_3_1_i2v_s_{resolution_name}",
            f"veo_3_1_i2v_s_portrait_{resolution_name}",
        )


_apply_veo_3_1_model_updates()


def _apply_current_flow_model_catalog():
    """Expose the current Flow model families while retaining hidden legacy aliases."""
    landscape = "VIDEO_ASPECT_RATIO_LANDSCAPE"
    portrait = "VIDEO_ASPECT_RATIO_PORTRAIT"

    for config_entry in MODEL_CONFIG.values():
        config_entry["listed"] = False

    def register(model_id: str, config_entry: Dict[str, Any], display_name: str):
        config_entry = dict(config_entry)
        config_entry["listed"] = True
        config_entry["display_name"] = display_name
        MODEL_CONFIG[model_id] = config_entry

    image_variants = [
        (model_id, dict(entry)) for model_id, entry in MODEL_CONFIG.items()
        if entry.get("type") == "image"
        and model_id.startswith("gemini-3.1-flash-image-")
        and entry.get("model_name") == "BELUGA"
    ]
    for model_id, entry in image_variants:
        entry["model_name"] = "BELUGA"
        register(model_id, entry, "Nano Banana 2.1")
        lite_entry = dict(entry)
        lite_entry["model_name"] = "HARBOR_SEAL"
        register(
            model_id.replace("gemini-3.1-flash-image-", "gemini-3.1-flash-lite-image-", 1),
            lite_entry,
            "Nano Banana 2 Lite",
        )

    def t2v(model_key: str, aspect_ratio: str) -> Dict[str, Any]:
        return _make_t2v_config(
            model_key,
            aspect_ratio,
            use_v2_model_config=True,
            allow_tier_upgrade=False,
        )

    def i2v(model_key: str, aspect_ratio: str, max_images: int = 2) -> Dict[str, Any]:
        return _make_i2v_config(
            model_key,
            aspect_ratio,
            min_images=1,
            max_images=max_images,
            use_v2_model_config=True,
            allow_tier_upgrade=False,
        )

    def r2v(model_key: str, aspect_ratio: str) -> Dict[str, Any]:
        return {
            "type": "video",
            "video_type": "r2v",
            "model_key": model_key,
            "aspect_ratio": aspect_ratio,
            "supports_images": True,
            "min_images": 1,
            "max_images": 3,
            "use_v2_model_config": True,
            "allow_tier_upgrade": False,
        }

    def extend(model_key: str, aspect_ratio: str) -> Dict[str, Any]:
        return {
            "type": "video",
            "video_type": "extend",
            "model_key": model_key,
            "aspect_ratio": aspect_ratio,
            "supports_images": False,
            "use_v2_model_config": True,
            "allow_tier_upgrade": False,
        }

    # Veo 3.1 Lite. Hasil test 2026-09: akun Pro ke semua lite (termasuk varian *_low_priority)
    # semuanya return MODEL_ACCESS_DENIED, seri veo butuh subscription lebih tinggi; key tetap default upstream.
    for seconds, key in (
        (4, "veo_3_1_t2v_lite_4s"),
        (6, "veo_3_1_t2v_lite_6s"),
        (8, "veo_3_1_t2v_lite"),
    ):
        for orientation, ratio in (("landscape", landscape), ("portrait", portrait)):
            register(
                f"veo-3.1-lite-{seconds}s-{orientation}",
                t2v(key, ratio),
                f"Veo 3.1 - Lite · {seconds}s · {orientation}",
            )

    # Veo 3.1 Fast. Current 4s/6s consumer access uses relaxed usage keys.
    for seconds, landscape_key, portrait_key in (
        (4, "veo_3_1_t2v_fast_4s_relaxed", "veo_3_1_t2v_fast_4s_relaxed"),
        (6, "veo_3_1_t2v_fast_6s_relaxed", "veo_3_1_t2v_fast_6s_relaxed"),
        (8, "veo_3_1_t2v_fast", "veo_3_1_t2v_fast_portrait"),
    ):
        register(
            f"veo-3.1-fast-{seconds}s-landscape",
            t2v(landscape_key, landscape),
            f"Veo 3.1 - Fast · {seconds}s · landscape",
        )
        register(
            f"veo-3.1-fast-{seconds}s-portrait",
            t2v(portrait_key, portrait),
            f"Veo 3.1 - Fast · {seconds}s · portrait",
        )

    # Veo 3.1 Quality.
    for seconds, landscape_key, portrait_key in (
        (4, "veo_3_1_t2v_quality_4s", "veo_3_1_t2v_quality_4s"),
        (6, "veo_3_1_t2v_quality_6s", "veo_3_1_t2v_quality_6s"),
        (8, "veo_3_1_t2v", "veo_3_1_t2v_portrait"),
    ):
        register(
            f"veo-3.1-quality-{seconds}s-landscape",
            t2v(landscape_key, landscape),
            f"Veo 3.1 - Quality · {seconds}s · landscape",
        )
        register(
            f"veo-3.1-quality-{seconds}s-portrait",
            t2v(portrait_key, portrait),
            f"Veo 3.1 - Quality · {seconds}s · portrait",
        )

    # Omni 1.1 Flash (upstream family key: abra). This is verified by a live
    # generation using abra_t2v_4s.
    for seconds in (4, 6, 8, 10):
        for orientation, ratio in (("landscape", landscape), ("portrait", portrait)):
            register(
                f"omni-1.1-flash-{seconds}s-{orientation}",
                {
                    "type": "video",
                    "video_type": "omni",
                    "model_key": f"abra_t2v_{seconds}s",
                    "reference_model_key": f"abra_r2v_{seconds}s",
                    "reference_duration": seconds,
                    "aspect_ratio": ratio,
                    "supports_images": True,
                    "min_images": 0,
                    "max_images": 3,
                    "use_v2_model_config": True,
                    "allow_tier_upgrade": False,
                },
                f"Omni 1.1 Flash · {seconds}s · {orientation}",
            )

    # Current image-to-video and reference-video variants.
    for seconds, lite_key, fast_key, quality_key in (
        (
            4,
            "veo_3_1_i2v_s_lite_4s_fl",
            "veo_3_1_i2v_s_fast_4s_fl_relaxed",
            "veo_3_1_i2v_s_quality_4s_fl",
        ),
        (
            6,
            "veo_3_1_i2v_s_lite_6s_fl",
            "veo_3_1_i2v_s_fast_6s_fl_relaxed",
            "veo_3_1_i2v_s_quality_6s_fl",
        ),
    ):
        for family, key in (
            ("lite", lite_key),
            ("fast", fast_key),
            ("quality", quality_key),
        ):
            for orientation, ratio in (
                ("landscape", landscape),
                ("portrait", portrait),
            ):
                register(
                    f"veo-3.1-{family}-i2v-{seconds}s-{orientation}",
                    i2v(key, ratio),
                    f"Veo 3.1 - {family.title()} I2V · {seconds}s · {orientation}",
                )

    for orientation, ratio, fast_key in (
        ("landscape", landscape, "veo_3_1_r2v_fast_landscape"),
        ("portrait", portrait, "veo_3_1_r2v_fast_portrait"),
    ):
        register(
            f"veo-3.1-fast-r2v-8s-{orientation}",
            r2v(fast_key, ratio),
            f"Veo 3.1 - Fast R2V · 8s · {orientation}",
        )
        register(
            f"veo-3.1-lite-r2v-8s-{orientation}",
            r2v("veo_3_1_r2v_lite", ratio),
            f"Veo 3.1 - Lite R2V · 8s · {orientation}",
        )

    for orientation, ratio, fast_key, quality_key in (
        (
            "landscape",
            landscape,
            "veo_3_1_extend_fast_landscape_ultra_relaxed",
            "veo_3_1_extend_landscape",
        ),
        (
            "portrait",
            portrait,
            "veo_3_1_extend_fast_portrait_ultra_relaxed",
            "veo_3_1_extend_portrait",
        ),
    ):
        register(
            f"veo-3.1-fast-extend-8s-{orientation}",
            extend(fast_key, ratio),
            f"Veo 3.1 - Fast Extend · {orientation}",
        )
        register(
            f"veo-3.1-quality-extend-8s-{orientation}",
            extend(quality_key, ratio),
            f"Veo 3.1 - Quality Extend · {orientation}",
        )
        register(
            f"veo-3.1-lite-extend-8s-{orientation}",
            extend("veo_3_1_extension_lite", ratio),
            f"Veo 3.1 - Lite Extend · {orientation}",
        )

    register(
        "veo-3.1-lite",
        t2v("veo_3_1_t2v_lite", landscape),
        "Veo 3.1 - Lite · 8s · landscape",
    )
    register(
        "veo-3.1-fast",
        t2v("veo_3_1_t2v_fast", landscape),
        "Veo 3.1 - Fast · 8s · landscape",
    )
    register(
        "veo-3.1-quality",
        t2v("veo_3_1_t2v", landscape),
        "Veo 3.1 - Quality · 8s · landscape",
    )
    register(
        "omni-1.1-flash",
        {
            "type": "video",
            "video_type": "omni",
            "model_key": "abra_t2v_8s",
            "reference_model_key": "abra_r2v_8s",
            "reference_duration": 8,
            "aspect_ratio": landscape,
            "supports_images": True,
            "min_images": 0,
            "max_images": 3,
            "use_v2_model_config": True,
            "allow_tier_upgrade": False,
        },
        "Omni 1.1 Flash · 8s · landscape",
    )


_apply_current_flow_model_catalog()


def _known_video_model_keys() -> set[str]:
    return {
        cfg["model_key"]
        for cfg in MODEL_CONFIG.values()
        if cfg.get("type") == "video" and cfg.get("model_key")
    }


def _resolve_tier_two_model_key(model_key: str) -> str:
    """Only upgrade to an ultra key when that exact upstream key is known valid."""
    if "ultra" in model_key:
        return model_key
    if "_fl" in model_key:
        candidate = model_key.replace("_fl", "_ultra_fl")
    else:
        candidate = model_key + "_ultra"
    return candidate if candidate in _known_video_model_keys() else model_key


class GenerationHandler:
    """Handler generate terpadu"""

    def __init__(
        self,
        flow_client,
        token_manager,
        load_balancer,
        db,
        concurrency_manager,
        proxy_manager,
    ):
        cache_dir = Path(__file__).resolve().parents[2] / "tmp"
        self.flow_client = flow_client
        self.token_manager = token_manager
        self.load_balancer = load_balancer
        self.db = db
        self.concurrency_manager = concurrency_manager
        self.proxy_manager = proxy_manager
        self.file_cache = FileCache(
            cache_dir=str(cache_dir),
            default_timeout=config.cache_timeout,
            proxy_manager=proxy_manager,
            flow_client=flow_client,
        )

    def _create_generation_result(self) -> Dict[str, Any]:
        """????????????????"""
        return dict(success=False, error_message=None, error_emitted=False)

    def _create_response_state(self) -> Dict[str, Any]:
        """Bikin status response independen per request, biar request konkuren nggak saling ngotorin."""
        return {
            "url": None,
            "generated_assets": None,
            "base_url": None,
        }

    def _mark_generation_failed(
        self, generation_result: Optional[Dict[str, Any]], error_message: str
    ):
        """????????????????????"""
        if isinstance(generation_result, dict):
            generation_result["success"] = False
            generation_result["error_message"] = error_message
            generation_result["error_emitted"] = True

    def _mark_generation_succeeded(self, generation_result: Optional[Dict[str, Any]]):
        """???????"""
        if isinstance(generation_result, dict):
            generation_result["success"] = True
            generation_result["error_message"] = None
            generation_result["error_emitted"] = False

    async def _resolve_video_asset(
        self,
        token,
        operation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse aset video ikut logika upstream sekarang: status ditentukan media, URL diambil via redirect dua tahap."""
        metadata = (operation.get("operation") or {}).get("metadata", {}) or {}
        video_info = (
            metadata.get("video", {}) if isinstance(metadata.get("video"), dict) else {}
        )
        project_id = (
            str(operation.get("projectId") or video_info.get("projectId") or "").strip()
            or None
        )
        media_name = (
            operation.get("mediaName")
            or video_info.get("mediaName")
        )
        # as29s indexes by generation operation id, not mediaName; the two are
        # distinct UUIDs and the wrong one comes back as code=[5] (NOT_FOUND).
        media_generation_id = (
            video_info.get("mediaGenerationId")
            or operation.get("name")
            or (operation.get("operation") or {}).get("name")
        )
        media_lookup_id = media_generation_id or media_name

        # response polling jwpduf mungkin sudah bawa direct link flow-content bertanda tangan (sama dengan path gambar),
        # langsung pakai ulang; cuma kalau nggak ada direct link baru tukar via as29s (sebagian model kayak abra
        # nama media nggak diterima as29s, bakal return code=[5]).
        video_url = str(video_info.get("fifeUrl") or "").strip()
        if not video_url and media_lookup_id:
            video_url = (
                await self.flow_client.get_media_url_redirect(
                    getattr(token, "st", ""),
                    media_lookup_id,
                    media_url_type="MEDIA_URL_TYPE_FULL_MEDIA",
                    google_cookies=getattr(token, "google_cookies", None),
                    token_id=getattr(token, "id", None),
                    project_id=project_id,
                )
                or ""
            )

        import re as _re

        uuid_match = _re.search(r"/video/([0-9a-f-]{36})", video_url or "")
        video_media_id = (
            uuid_match.group(1)
            if uuid_match
            else str(media_generation_id or media_lookup_id or "")
        )

        return {
            "media_name": media_name or media_generation_id,
            "video_url": video_url,
            "video_media_id": video_media_id,
            "aspect_ratio": video_info.get("aspectRatio", "VIDEO_ASPECT_RATIO_LANDSCAPE"),
            "model": video_info.get("model"),
            "duration": video_info.get("duration"),
            "metadata": metadata,
            "video_info": video_info,
        }

    def _normalize_error_message(self, error_message: Any, max_length: int = 1000) -> str:
        """Normalisasi teks error, biar nggak kepanjangan."""
        text = str(error_message or "").strip() or "Error tidak dikenal"
        if len(text) <= max_length:
            return text
        return f"{text[:max_length - 3]}..."

    def _resolve_video_model_key_for_tier(self, model_config: Dict[str, Any], user_tier: str) -> tuple[str, Optional[str]]:
        """Sesuaikan key model video berdasarkan tier akun."""
        model_key = model_config["model_key"]
        allow_tier_upgrade = bool(model_config.get("allow_tier_upgrade", True))

        if user_tier == "PAYGATE_TIER_TWO":
            if allow_tier_upgrade and "ultra" not in model_key:
                upgraded_model_key = _resolve_tier_two_model_key(model_key)
                if upgraded_model_key != model_key:
                    return (
                        upgraded_model_key,
                        f"TIER_TWO akun otomatis switch ke model ultra: {upgraded_model_key}",
                    )
            return model_key, None

        if user_tier == "PAYGATE_TIER_ONE" and "ultra" in model_key:
            model_key = model_key.replace("_ultra_fl", "_fl").replace("_ultra", "")
            return model_key, f"TIER_ONE akun otomatis switch ke model standar: {model_key}"

        return model_key, None

    async def _fail_video_task(
        self, operations: Optional[List[Dict[str, Any]]], error_message: str
    ):
        """Tutup task video ke status gagal, biar nggak nyangkut processing."""
        if not operations:
            return

        operation = operations[0] if operations else {}
        task_id = (operation.get("operation") or {}).get("name")
        if not task_id:
            return

        try:
            await self.db.update_task(
                task_id,
                status="failed",
                error_message=self._normalize_error_message(error_message),
                completed_at=time.time(),
            )
        except Exception as exc:
            debug_logger.log_error(f"[VIDEO] Gagal update status gagal task: {exc}")

    async def check_token_availability(self, is_image: bool, is_video: bool) -> bool:
        """Cek ketersediaan Token

        Args:
            is_image: apakah cek Token generate gambar
            is_video: apakah cek Token generate video

        Returns:
            True = ada Token tersedia, False = nggak ada Token tersedia
        """
        token_obj = await self.load_balancer.select_token(
            for_image_generation=is_image, for_video_generation=is_video
        )
        return token_obj is not None

    async def handle_generation(
        self,
        model: str,
        prompt: str,
        images: Optional[List[bytes]] = None,
        stream: bool = False,
        base_url_override: Optional[str] = None,
        video_media_id: Optional[str] = None,
    ) -> AsyncGenerator:
        """Entry point generate terpadu

        Args:
            model: nama model
            prompt: prompt
            images: list gambar (format bytes)
            stream: apakah output streaming
        """
        start_time = time.time()
        token = None
        generation_type = None
        pending_token_state = {"active": False}
        request_id = f"gen-{int(start_time * 1000)}-{id(asyncio.current_task())}"
        perf_trace: Dict[str, Any] = {
            "request_id": request_id,
            "model": model,
            "status": "processing",
        }
        generation_result = self._create_generation_result()
        response_state = self._create_response_state()
        response_state["base_url"] = (base_url_override or "").strip().rstrip(
            "/"
        ) or None
        request_log_state: Dict[str, Any] = {"id": None, "progress": 0}

        # cegah chain konkuren pakai ulang konteks fingerprint request sebelumnya
        if hasattr(self.flow_client, "clear_request_fingerprint"):
            self.flow_client.clear_request_fingerprint()

        # 1. validasi model
        if model not in MODEL_CONFIG:
            error_msg = f"Model nggak didukung: {model}"
            debug_logger.log_error(error_msg)
            record_generation_result("unknown", "invalid", time.time() - start_time)
            yield self._create_error_response(error_msg, status_code=400)
            return

        model_config = MODEL_CONFIG[model]
        generation_type = model_config["type"]
        video_type_for_op = model_config.get("video_type", "")
        request_operation = (
            "extend_video"
            if video_type_for_op == "extend"
            else f"generate_{generation_type}"
        )
        prompt_for_log = (
            prompt if len(prompt) <= 2000 else f"{prompt[:2000]}...(truncated)"
        )
        request_payload = {
            "model": model,
            "prompt": prompt_for_log,
            "has_images": images is not None and len(images) > 0,
        }
        debug_logger.log_info(
            f"[GENERATION] Mulai generate - model: {model}, tipe: {generation_type}, Prompt: {prompt[:50]}..."
        )

        # tampilin info mulai ke user
        if stream:
            yield self._create_stream_chunk(
                f"✨ Tugas pembuatan {'video' if generation_type == 'video' else 'gambar'} dimulai\n",
                role="assistant",
            )
            request_log_state["id"] = await self._log_request(
                token_id=None,
                operation=request_operation,
                request_data=request_payload,
                response_data={
                    "status": "processing",
                    "status_text": "started",
                    "progress": 0,
                    "request_id": request_id,
                },
                status_code=102,
                duration=0,
                status_text="started",
                progress=0,
            )

        # 2. pilih Token
        debug_logger.log_info(f"[GENERATION] Lagi milih Token yang tersedia...")
        token_select_started_at = time.time()

        if generation_type == "image":
            token = await self.load_balancer.select_token(
                for_image_generation=True,
                model=model,
                reserve=False,
                enforce_concurrency_filter=False,
                track_pending=True,
            )
        else:
            token = await self.load_balancer.select_token(
                for_video_generation=True,
                model=model,
                reserve=False,
                enforce_concurrency_filter=False,
                track_pending=True,
            )
        perf_trace["token_select_ms"] = int(
            (time.time() - token_select_started_at) * 1000
        )

        if not token:
            error_msg = None
            if self.load_balancer and hasattr(
                self.load_balancer, "get_unavailable_reason"
            ):
                error_msg = await self.load_balancer.get_unavailable_reason(
                    for_image_generation=(generation_type == "image"),
                    for_video_generation=(generation_type == "video"),
                    model=model,
                )
            if not error_msg:
                error_msg = self._get_no_token_error_message(generation_type)
            debug_logger.log_error(f"[GENERATION] {error_msg}")
            record_generation_result(
                generation_type, "no_token", time.time() - start_time
            )
            await self._log_request(
                token_id=None,
                operation=request_operation,
                request_data=request_payload,
                response_data={"error": error_msg, "performance": perf_trace},
                status_code=503,
                duration=time.time() - start_time,
                log_id=request_log_state.get("id"),
                status_text="failed",
                progress=request_log_state.get("progress", 0),
            )
            if stream:
                yield self._create_stream_chunk(f"Error: {error_msg}\n")
            yield self._create_error_response(error_msg, status_code=503)
            return

        debug_logger.log_info(f"[GENERATION] Token kepilih: {token.id} ({token.email})")
        pending_token_state["active"] = True
        await self._update_request_log_progress(
            request_log_state,
            token_id=token.id,
            status_text="token_selected",
            progress=8,
            response_extra={"token_email": token.email},
        )

        try:
            # 3. pastikan AT valid
            debug_logger.log_info(f"[GENERATION] Cek validitas AT Token...")
            if stream:
                yield self._create_stream_chunk("Menginisialisasi lingkungan...\n")

            await self._update_request_log_progress(
                request_log_state,
                token_id=token.id,
                status_text="token_ready",
                progress=15,
            )
            ensure_at_started_at = time.time()
            token = await self.token_manager.ensure_valid_token(token)
            perf_trace["ensure_at_ms"] = int(
                (time.time() - ensure_at_started_at) * 1000
            )
            if not token:
                error_msg = "AT Token nggak valid atau gagal refresh"
                debug_logger.log_error(f"[GENERATION] {error_msg}")
                record_generation_result(
                    generation_type, "failed", time.time() - start_time
                )
                if stream:
                    yield self._create_stream_chunk(f"Error: {error_msg}\n")
                yield self._create_error_response(error_msg, status_code=503)
                return

            # 4. pastikan Project ada
            debug_logger.log_info(f"[GENERATION] Cek/bikin Project...")

            if not supports_model_for_tier(model, token.user_paygate_tier):
                required_tier = get_required_paygate_tier_for_model(model)
                error_msg = (
                    "Model ini butuh akun "
                    + get_paygate_tier_label(required_tier)
                    + ": "
                    + model
                )
                debug_logger.log_error(f"[GENERATION] {error_msg}")
                record_generation_result(
                    generation_type, "failed", time.time() - start_time
                )
                if stream:
                    yield self._create_stream_chunk(f"Error: {error_msg}\n")
                yield self._create_error_response(error_msg, status_code=403)
                return

            ensure_project_started_at = time.time()
            project_id = await self.token_manager.ensure_project_exists(token.id)
            perf_trace["ensure_project_ms"] = int(
                (time.time() - ensure_project_started_at) * 1000
            )
            debug_logger.log_info(f"[GENERATION] Project ID: {project_id}")
            await self._update_request_log_progress(
                request_log_state,
                token_id=token.id,
                status_text="project_ready",
                progress=22,
                response_extra={"project_id": project_id},
            )
            prefill_action = (
                "IMAGE_GENERATION" if generation_type == "image" else "VIDEO_GENERATION"
            )
            await self.flow_client.prefill_remote_browser_pool(
                project_id=project_id,
                action=prefill_action,
                token_id=token.id,
            )

            # 5. proses berdasarkan tipe
            generation_pipeline_started_at = time.time()
            if generation_type == "image":
                debug_logger.log_info(f"[GENERATION] Mulai proses generate gambar...")
                async for chunk in self._handle_image_generation(
                    token,
                    project_id,
                    model_config,
                    prompt,
                    images,
                    stream,
                    perf_trace=perf_trace,
                    generation_result=generation_result,
                    response_state=response_state,
                    request_log_state=request_log_state,
                    pending_token_state=pending_token_state,
                ):
                    yield chunk
            else:  # video
                debug_logger.log_info(f"[GENERATION] Mulai proses generate video...")
                async for chunk in self._handle_video_generation(
                    token,
                    project_id,
                    model_config,
                    prompt,
                    images,
                    stream,
                    perf_trace=perf_trace,
                    generation_result=generation_result,
                    response_state=response_state,
                    request_log_state=request_log_state,
                    pending_token_state=pending_token_state,
                    video_media_id=video_media_id,
                ):
                    yield chunk
            perf_trace["generation_pipeline_ms"] = int(
                (time.time() - generation_pipeline_started_at) * 1000
            )

            # 6. catat pemakaian
            if not generation_result.get("success"):
                error_msg = generation_result.get("error_message") or "Generate nggak selesai dengan sukses"
                debug_logger.log_warning(
                    f"[GENERATION] Generate nggak sukses, nggak potong kuota: {error_msg}"
                )
                if token:
                    await self.token_manager.record_error(token.id)
                duration = time.time() - start_time
                record_generation_result(generation_type, "failed", duration)
                perf_trace["status"] = "failed"
                perf_trace["total_ms"] = int(duration * 1000)
                perf_trace["error"] = error_msg
                prompt_for_log = (
                    prompt if len(prompt) <= 2000 else f"{prompt[:2000]}...(truncated)"
                )
                await self._log_request(
                    token.id if token else None,
                    request_operation,
                    request_payload,
                    {"error": error_msg, "performance": perf_trace},
                    500,
                    duration,
                    log_id=request_log_state.get("id"),
                    status_text="failed",
                    progress=request_log_state.get("progress", 0),
                )
                if not generation_result.get("error_emitted"):
                    if stream:
                        yield self._create_stream_chunk(f"Error: {error_msg}\n")
                    yield self._create_error_response(error_msg, status_code=500)
                return

            is_video = generation_type == "video"
            await self.token_manager.record_usage(token.id, is_video=is_video)

            # reset hitungan error (bersihin hitungan error beruntun saat request sukses)
            await self.token_manager.record_success(token.id)

            debug_logger.log_info(f"[GENERATION] ✅ Generate selesai dengan sukses")

            # 7. catat log sukses
            duration = time.time() - start_time
            record_generation_result(generation_type, "success", duration)
            perf_trace["status"] = "success"
            perf_trace["total_ms"] = int(duration * 1000)
            # simpan prompt yang lebih lengkap di log, biar halaman admin nggak cuma lihat yang kependek
            prompt_for_log = (
                prompt if len(prompt) <= 2000 else f"{prompt[:2000]}...(truncated)"
            )

            # bangun data response, termasuk URL hasil generate
            response_data = {
                "status": "success",
                "model": model,
                "prompt": prompt_for_log,
                "performance": perf_trace,
            }

            # tambahin URL hasil generate (kalau ada)
            if response_state.get("url"):
                response_data["url"] = response_state["url"]
            if response_state.get("generated_assets"):
                response_data["generated_assets"] = response_state["generated_assets"]
            image_perf = (
                perf_trace.get("image_generation", {})
                if isinstance(perf_trace, dict)
                else {}
            )
            video_perf = (
                perf_trace.get("video_generation", {})
                if isinstance(perf_trace, dict)
                else {}
            )
            debug_logger.log_info(
                f"[PERF] [{request_id}] total={perf_trace.get('total_ms', 0)}ms, "
                f"select={perf_trace.get('token_select_ms', 0)}ms, "
                f"ensure_at={perf_trace.get('ensure_at_ms', 0)}ms, "
                f"project={perf_trace.get('ensure_project_ms', 0)}ms, "
                f"pipeline={perf_trace.get('generation_pipeline_ms', 0)}ms, "
                f"slot_wait={image_perf.get('slot_wait_ms', 0)}ms, "
                f"launch_queue={image_perf.get('launch_queue_wait_ms', 0)}ms, "
                f"launch_stagger={image_perf.get('launch_stagger_wait_ms', 0)}ms, "
                f"video_slot_wait={video_perf.get('slot_wait_ms', 0)}ms"
            )

            await self._log_request(
                token.id,
                request_operation,
                request_payload,
                response_data,
                200,
                duration,
                log_id=request_log_state.get("id"),
                status_text="completed",
                progress=100,
            )

        except asyncio.CancelledError:
            error_msg = "Generate dibatalkan: koneksi client putus"
            debug_logger.log_warning(f"[GENERATION] ⚠️ {error_msg}")
            duration = time.time() - start_time
            record_generation_result(
                generation_type or "unknown", "cancelled", duration
            )
            perf_trace["status"] = "failed"
            perf_trace["total_ms"] = int(duration * 1000)
            perf_trace["error"] = error_msg
            prompt_for_log = (
                prompt if len(prompt) <= 2000 else f"{prompt[:2000]}...(truncated)"
            )
            await self._log_request(
                token.id if token else None,
                request_operation if generation_type else "generate_unknown",
                request_payload if "request_payload" in locals() else {"model": model},
                {"error": error_msg, "performance": perf_trace},
                499,
                duration,
                log_id=request_log_state.get("id"),
                status_text="failed",
                progress=request_log_state.get("progress", 0),
            )
            raise
        except Exception as e:
            error_msg = f"Gagal membuat: {str(e)}"
            debug_logger.log_error(f"[GENERATION] Generate gagal: {error_msg}")
            if token:
                if self._should_count_token_error(e):
                    await self.token_manager.record_error(token.id)
                else:
                    debug_logger.log_info(
                        f"[GENERATION] Lewati hitungan error token: token_id={token.id}, reason={str(e)[:200]}"
                    )

            # simpan dulu status gagal final ke DB, baru return error response, biar log nggak mentok di 102.
            duration = time.time() - start_time
            record_generation_result(generation_type or "unknown", "failed", duration)
            perf_trace["status"] = "failed"
            perf_trace["total_ms"] = int(duration * 1000)
            perf_trace["error"] = error_msg
            prompt_for_log = (
                prompt if len(prompt) <= 2000 else f"{prompt[:2000]}...(truncated)"
            )
            await self._log_request(
                token.id if token else None,
                request_operation if generation_type else "generate_unknown",
                request_payload if "request_payload" in locals() else {"model": model},
                {"error": error_msg, "performance": perf_trace},
                500,
                duration,
                log_id=request_log_state.get("id"),
                status_text="failed",
                progress=request_log_state.get("progress", 0),
            )
            if stream:
                yield self._create_stream_chunk(f"Error: {error_msg}\n")
            yield self._create_error_response(error_msg, status_code=500)
        finally:
            if pending_token_state.get("active") and token and self.load_balancer:
                await self.load_balancer.release_pending(
                    token.id,
                    for_image_generation=(generation_type == "image"),
                    for_video_generation=(generation_type == "video"),
                )
                pending_token_state["active"] = False

    def _get_no_token_error_message(self, generation_type: str) -> str:
        """Ambil detail error saat nggak ada Token tersedia"""
        if generation_type == "image":
            return "Tidak ada Akun/Token yang aktif untuk pembuatan gambar. Status akun saat ini sedang nonaktif atau sesi Cookie Google belum terhubung."
        else:
            return "Tidak ada Akun/Token yang aktif untuk pembuatan video. Status akun saat ini sedang nonaktif atau sesi Cookie Google belum terhubung."

    def _should_count_token_error(self, error: Exception) -> bool:
        """Tentukan apakah failure harus dihitung sebagai error beruntun token.

        kegagalan ambil reCAPTCHA, error provider captcha, atau resource captcha kurang biasanya bukan salah akunnya;
        kalau dihitung sebagai error beruntun, token bisa ke-disable otomatis pas regression test atau proxy goyang.
        """
        error_text = str(error or "").strip().lower()
        if not error_text:
            return True

        non_token_fault_markers = (
            "failed to obtain recaptcha token",
            "recaptcha evaluation failed",
            "verifikasi recaptcha gagal",
            "error recaptcha",
            "public_error_unusual_activity",
            "too much traffic",
            "error_no_slot_available",
            "resource jasa captcha kurang",
            "resource jasa captcha keblokir",
            "yescaptcha",
            "capsolver",
            "captcharun",
            "twocaptcha",
            "2captcha",
            "capmonster",
            "ezcaptcha",
        )
        if any(marker in error_text for marker in non_token_fault_markers):
            return False

        if "nggak ada token tersedia buat" in error_text:
            return False

        return True

    async def _handle_image_generation(
        self,
        token,
        project_id: str,
        model_config: dict,
        prompt: str,
        images: Optional[List[bytes]],
        stream: bool,
        perf_trace: Optional[Dict[str, Any]] = None,
        generation_result: Optional[Dict[str, Any]] = None,
        response_state: Optional[Dict[str, Any]] = None,
        request_log_state: Optional[Dict[str, Any]] = None,
        pending_token_state: Optional[Dict[str, bool]] = None,
    ) -> AsyncGenerator:
        """Proses generate gambar (return sinkron)"""

        if response_state is None:
            response_state = self._create_response_state()

        image_trace: Optional[Dict[str, Any]] = None
        if isinstance(perf_trace, dict):
            image_trace = perf_trace.setdefault("image_generation", {})
            image_trace["input_image_count"] = len(images) if images else 0

        # nggak nunggu slot konkurensi gambar lokal; request langsung di-submit ke upstream begitu datang.
        normalized_tier = normalize_user_paygate_tier(token.user_paygate_tier)

        if image_trace is not None:
            image_trace["slot_wait_ms"] = 0

        if images and len(images) > 0:
            await self._update_request_log_progress(
                request_log_state,
                token_id=token.id,
                status_text="uploading_images",
                progress=28,
            )
        else:
            await self._update_request_log_progress(
                request_log_state,
                token_id=token.id,
                status_text="submitting_image",
                progress=28,
            )

        try:
            # upload gambar (kalau ada)
            upload_started_at = time.time()
            image_inputs = []
            if images and len(images) > 0:
                if stream:
                    yield self._create_stream_chunk(
                        f"Upload {len(images)} gambar referensi...\n"
                    )

                # dukung input multi-gambar
                for idx, image_bytes in enumerate(images):
                    media_id = await self.flow_client.upload_image(
                        token.at,
                        image_bytes,
                        model_config["aspect_ratio"],
                        project_id=project_id,
                        token_id=token.id,
                        google_cookies=getattr(token, "google_cookies", None),
                    )
                    image_inputs.append(
                        {
                        "name": media_id,
                            "imageInputType": "IMAGE_INPUT_TYPE_REFERENCE",
                        }
                    )
                    if stream:
                        yield self._create_stream_chunk(
                            f"Gambar {idx + 1}/{len(images)} terunggah\n"
                        )
            if image_trace is not None:
                image_trace["upload_images_ms"] = int(
                    (time.time() - upload_started_at) * 1000
                )

            # panggil API generate
            if stream:
                if images and len(images) > 0:
                    yield self._create_stream_chunk(
                        "Upload gambar referensi selesai, sedang memverifikasi reCAPTCHA...\n"
                    )
                else:
                    yield self._create_stream_chunk(
                        "Sedang memverifikasi reCAPTCHA & mengirim tugas gambar...\n"
                    )

            async def _image_progress_callback(status_text: str, progress: int):
                await self._update_request_log_progress(
                    request_log_state,
                    token_id=token.id,
                    status_text=status_text,
                    progress=progress,
                )

            generate_started_at = time.time()
            (
                result,
                generation_session_id,
                upstream_trace,
            ) = await self.flow_client.generate_image(
                at=token.at,
                project_id=project_id,
                prompt=prompt,
                model_name=model_config["model_name"],
                aspect_ratio=model_config["aspect_ratio"],
                image_inputs=image_inputs,
                token_id=token.id,
                token_image_concurrency=token.image_concurrency,
                progress_callback=_image_progress_callback,
                google_cookies=getattr(token, "google_cookies", None),
            )
            if image_trace is not None:
                image_trace["generate_api_ms"] = int(
                    (time.time() - generate_started_at) * 1000
                )
                image_trace["upstream_trace"] = upstream_trace
                attempts = (
                    upstream_trace.get("generation_attempts")
                    if isinstance(upstream_trace, dict)
                    else None
                )
                if isinstance(attempts, list) and attempts:
                    first_attempt = attempts[0] if isinstance(attempts[0], dict) else {}
                    image_trace["launch_queue_wait_ms"] = int(
                        first_attempt.get("launch_queue_ms") or 0
                    )
                    image_trace["launch_stagger_wait_ms"] = int(
                        first_attempt.get("launch_stagger_ms") or 0
                    )
            await self._update_request_log_progress(
                request_log_state,
                token_id=token.id,
                status_text="image_generated",
                progress=72,
            )

            # ekstrak URL dan mediaId
            media = result.get("media", [])
            if not media:
                self._mark_generation_failed(
                    generation_result, "\u751f\u6210\u7ed3\u679c\u4e3a\u7a7a"
                )
                yield self._create_error_response("Hasil generate kosong", status_code=502)
                return

            image_url = media[0]["image"]["generatedImage"]["fifeUrl"]
            media_id = media[0].get("name")  # buat upsample
            response_state["generated_assets"] = {
                "type": "image",
                "origin_image_url": image_url,
            }

            # cek apakah perlu upsample
            upsample_resolution = model_config.get("upsample")
            if upsample_resolution and media_id:
                upsample_started_at = time.time()
                resolution_name = "4K" if "4K" in upsample_resolution else "2K"
                await self._update_request_log_progress(
                    request_log_state,
                    token_id=token.id,
                    status_text=f"upsampling_{resolution_name.lower()}",
                    progress=82,
                )
                if stream:
                    yield self._create_stream_chunk(
                        f"Lagi upscale gambar ke {resolution_name}...\n"
                    )

                # 4K/2K logika retry gambar - pakai max retry dari konfigurasi
                max_retries = config.flow_max_retries
                for retry_attempt in range(max_retries):
                    try:
                        # panggil API upsample
                        encoded_image = await self.flow_client.upsample_image(
                            at=token.at,
                            project_id=project_id,
                            media_id=media_id,
                            target_resolution=upsample_resolution,
                            user_paygate_tier=normalized_tier,
                            session_id=generation_session_id,
                            token_id=token.id,
                            google_cookies=getattr(token, "google_cookies", None),
                        )

                        if encoded_image:
                            debug_logger.log_info(
                                f"[UPSAMPLE] Gambar sudah di-upscale ke {resolution_name}"
                            )

                            if stream:
                                yield self._create_stream_chunk(
                                    f"✅ Gambar sudah di-upscale ke {resolution_name}\n"
                                )

                            # 2K/4K gambar disatuin disimpan sebagai file asli, di log cuma simpan link.
                            response_state["generated_assets"] = {
                                "type": "image",
                                "origin_image_url": image_url,
                                "upscaled_image": {"resolution": resolution_name},
                            }

                            if str(encoded_image).startswith("https://"):
                                response_state["url"] = encoded_image
                                response_state["generated_assets"]["upscaled_image"][
                                    "url"
                                ] = encoded_image
                                response_state["generated_assets"]["upscaled_image"][
                                    "delivery_mode"
                                ] = "frontend_url"
                                self._mark_generation_succeeded(generation_result)
                                if stream:
                                    yield self._create_stream_chunk(
                                        f"![Generated Image]({encoded_image})",
                                        finish_reason="stop",
                                    )
                                else:
                                    yield self._create_completion_response(
                                        encoded_image,
                                        media_type="image",
                                    )
                                if image_trace is not None:
                                    image_trace["upsample_ms"] = int(
                                        (time.time() - upsample_started_at) * 1000
                                    )
                                return

                            try:
                                await self._update_request_log_progress(
                                    request_log_state,
                                    token_id=token.id,
                                    status_text="caching_image",
                                    progress=90,
                                )
                                if stream:
                                    yield self._create_stream_chunk(
                                        f"Cache {resolution_name} gambar...\n"
                                    )
                                cached_filename = (
                                    await self.file_cache.cache_base64_image(
                                        encoded_image, resolution_name
                                    )
                                )
                                local_url = f"{self._get_base_url(response_state)}/tmp/{cached_filename}"
                                response_state["url"] = local_url
                                response_state["generated_assets"]["upscaled_image"][
                                    "local_url"
                                ] = local_url
                                response_state["generated_assets"]["upscaled_image"][
                                    "url"
                                ] = local_url
                                self._mark_generation_succeeded(generation_result)
                                if stream:
                                    yield self._create_stream_chunk(
                                        f"✅ {resolution_name} gambar berhasil di-cache\n"
                                    )
                                    yield self._create_stream_chunk(
                                        f"![Generated Image]({local_url})",
                                        finish_reason="stop",
                                    )
                                else:
                                    yield self._create_completion_response(
                                        local_url, media_type="image"
                                    )
                                if image_trace is not None:
                                    image_trace["upsample_ms"] = int(
                                        (time.time() - upsample_started_at) * 1000
                                    )
                                return
                            except Exception as e:
                                debug_logger.log_error(
                                    f"Failed to cache {resolution_name} image: {str(e)}"
                                )
                                response_state["url"] = image_url
                                response_state["generated_assets"]["upscaled_image"][
                                    "local_url"
                                ] = None
                                response_state["generated_assets"]["upscaled_image"][
                                    "url"
                                ] = image_url
                                response_state["generated_assets"]["upscaled_image"][
                                    "delivery_mode"
                                ] = "inline_base64_fallback"
                                self._mark_generation_succeeded(generation_result)
                                base64_url = f"data:image/jpeg;base64,{encoded_image}"
                                if stream:
                                    cache_error = self._normalize_error_message(
                                        e, max_length=120
                                    )
                                    yield self._create_stream_chunk(
                                        f"⚠️ Gagal cache: {cache_error}, balikin gambar inline...\n"
                                    )
                                    yield self._create_stream_chunk(
                                        f"![Generated Image]({base64_url})",
                                        finish_reason="stop",
                                    )
                                else:
                                    yield self._create_completion_response(
                                        base64_url, media_type="image"
                                    )
                                if image_trace is not None:
                                    image_trace["upsample_ms"] = int(
                                        (time.time() - upsample_started_at) * 1000
                                    )
                                return
                        else:
                            debug_logger.log_warning("[UPSAMPLE] hasil return kosong")
                            if stream:
                                yield self._create_stream_chunk(
                                    f"⚠️ Upscale gagal, balikin gambar asli...\n"
                                )
                            break  # hasil kosong nggak di-retry

                    except Exception as e:
                        error_str = str(e)
                        debug_logger.log_error(
                            f"[UPSAMPLE] Upscale gagal (percobaan {retry_attempt + 1}/{max_retries}): {error_str}"
                        )
                        
                        # cek apakah error bisa di-retry (403, reCAPTCHA, timeout, dll)
                        retry_reason = self.flow_client._get_retry_reason(error_str)
                        if retry_reason and retry_attempt < max_retries - 1:
                            if stream:
                                yield self._create_stream_chunk(
                                    f"⚠️ Upscale kena {retry_reason}, lagi retry ({retry_attempt + 2}/{max_retries})...\n"
                                )
                            # tunggu sebentar terus retry
                            await asyncio.sleep(1)
                            continue
                        else:
                            if stream:
                                yield self._create_stream_chunk(
                                    f"⚠️ Upscale gagal: {error_str}, balikin gambar asli...\n"
                                )
                            break
                if image_trace is not None:
                    image_trace["upsample_ms"] = int(
                        (time.time() - upsample_started_at) * 1000
                    )
                # pas upscale gagal dan fallback ke gambar asli, catat flag gagal biar caller tahu resolusi aktual yang dikirim
                if upsample_resolution and media_id:
                    response_state.setdefault("generated_assets", {})[
                        "upscaled_image"
                    ] = {
                        "resolution": resolution_name,
                        "failed": True,
                        "delivery_mode": "origin_fallback",
                    }

            local_url = image_url
            cache_started_at = time.time()
            if config.cache_enabled:
                await self._update_request_log_progress(
                    request_log_state,
                    token_id=token.id,
                    status_text="caching_image",
                    progress=90,
                )
                if stream:
                    yield self._create_stream_chunk("Menyimpan cache gambar 1K...\n")
                try:
                    cached_filename = await self.file_cache.download_and_cache(
                        image_url, "image"
                    )
                    local_url = (
                        f"{self._get_base_url(response_state)}/tmp/{cached_filename}"
                    )
                    if stream:
                        yield self._create_stream_chunk(
                            "✅ 1K gambar berhasil di-cache, siap return alamat cache...\n"
                        )
                except Exception as e:
                    debug_logger.log_error(f"Failed to cache 1K image: {str(e)}")
                    local_url = image_url
                    if stream:
                        cache_error = self._normalize_error_message(e, max_length=120)
                        yield self._create_stream_chunk(
                            f"⚠️ Gagal cache: {cache_error}\nlagi return link sumber...\n"
                        )
            elif stream:
                yield self._create_stream_chunk("Cache nonaktif, mengembalikan URL resmi...\n")
            if image_trace is not None:
                image_trace["cache_image_ms"] = int(
                    (time.time() - cache_started_at) * 1000
                )

            # return hasil
            # simpan URL buat pencatatan log
            response_state["url"] = local_url
            final_assets = {
                "type": "image",
                "origin_image_url": image_url,
                "final_image_url": local_url,
            }
            # pertahankan flag fallback gagal upscale (kalau ada), biar caller tahu resolusi aktual
            upscaled_marker = (response_state.get("generated_assets") or {}).get(
                "upscaled_image"
            )
            if upscaled_marker:
                final_assets["upscaled_image"] = upscaled_marker
            response_state["generated_assets"] = final_assets
            self._mark_generation_succeeded(generation_result)

            if stream:
                yield self._create_stream_chunk(
                    f"![Generated Image]({local_url})", finish_reason="stop"
                )
            else:
                yield self._create_completion_response(
                    local_url,  # langsung oper URL, biar method yang format di dalam
                    media_type="image",
                )

        finally:
            pass

    async def _handle_video_generation(
        self,
        token,
        project_id: str,
        model_config: dict,
        prompt: str,
        images: Optional[List[bytes]],
        stream: bool,
        perf_trace: Optional[Dict[str, Any]] = None,
        generation_result: Optional[Dict[str, Any]] = None,
        response_state: Optional[Dict[str, Any]] = None,
        request_log_state: Optional[Dict[str, Any]] = None,
        pending_token_state: Optional[Dict[str, bool]] = None,
        video_media_id: Optional[str] = None,
    ) -> AsyncGenerator:
        """Proses generate video (polling asinkron)"""

        if response_state is None:
            response_state = self._create_response_state()

        video_trace: Optional[Dict[str, Any]] = None
        if isinstance(perf_trace, dict):
            video_trace = perf_trace.setdefault("video_generation", {})
            video_trace["input_image_count"] = len(images) if images else 0

        # nggak nunggu slot konkurensi video lokal; request langsung di-submit ke upstream begitu datang.
        normalized_tier = normalize_user_paygate_tier(token.user_paygate_tier)

        if video_trace is not None:
            video_trace["slot_wait_ms"] = 0

        await self._update_request_log_progress(
            request_log_state,
            token_id=token.id,
            status_text="preparing_video",
            progress=24,
        )

        try:
            # ambil tipe model dan konfigurasi
            video_type = model_config.get("video_type")
            supports_images = model_config.get("supports_images", False)
            min_images = model_config.get("min_images", 0)
            max_images = model_config.get("max_images", 0)
            use_v2_model_config = bool(model_config.get("use_v2_model_config", False))

            # sesuaikan model otomatis berdasarkan tier akun key
            user_tier = normalized_tier

            original_model_key = model_config["model_key"]
            model_key, tier_message = self._resolve_video_model_key_for_tier(
                model_config, user_tier
            )
            if tier_message:
                if stream:
                    yield self._create_stream_chunk(f"{tier_message}\n")
                debug_logger.log_info(
                    f"[VIDEO] adjustment model tier akun: {original_model_key} -> {model_key}"
                )
            elif user_tier == "PAYGATE_TIER_TWO" and original_model_key == model_key:
                debug_logger.log_info(
                    f"[VIDEO] akun TIER_TWO, nggak nemu varian ultra yang valid, pertahankan model: {model_key}"
                )

            # update model_key di model_config
            model_config = dict(model_config)  # bikin copy biar nggak ubah konfigurasi asli
            model_config["model_key"] = model_key

            # jumlah gambar
            image_count = len(images) if images else 0

            # ========== validasi dan proses gambar ==========

            # T2V: text-to-video - nggak dukung gambar
            if video_type == "t2v":
                if image_count > 0:
                    if stream:
                        yield self._create_stream_chunk(
                            "⚠️ Model text-to-video nggak dukung upload gambar, gambar diabaikan, cuma pakai prompt teks\n"
                        )
                    debug_logger.log_warning(
                        f"[T2V] model {model_config['model_key']} nggak dukung gambar, sudah diabaikan {image_count} gambar"
                    )
                images = None  # bersihin gambar
                image_count = 0

            # Omni: nggak ada gambar pakai T2V, ada gambar pakai jalur langsung Reference Images upstream sekarang
            elif video_type == "omni":
                if max_images is not None and image_count > max_images:
                    error_msg = f"Model Omni maksimal dukung {max_images} gambar referensi, sekarang dikasih {image_count} gambar"
                    if stream:
                        yield self._create_stream_chunk(f"{error_msg}\n")
                    self._mark_generation_failed(generation_result, error_msg)
                    yield self._create_error_response(error_msg, status_code=400)
                    return

            # I2V: model first-last frame - butuh 1-2 gambar
            elif video_type == "i2v":
                if image_count < min_images or image_count > max_images:
                    error_msg = f"Model first-last frame butuh {min_images}-{max_images} gambar, sekarang dikasih {image_count} gambar"
                    if stream:
                        yield self._create_stream_chunk(f"{error_msg}\n")
                    self._mark_generation_failed(generation_result, error_msg)
                    yield self._create_error_response(error_msg, status_code=400)
                    return

            # R2V: generate multi-gambar - protokol upstream sekarang maksimal 3 gambar referensi
            elif video_type == "r2v":
                if max_images is not None and image_count > max_images:
                    error_msg = f"Model video multi-gambar maksimal dukung {max_images} gambar referensi, sekarang dikasih {image_count} gambar"
                    if stream:
                        yield self._create_stream_chunk(f"{error_msg}\n")
                    self._mark_generation_failed(generation_result, error_msg)
                    yield self._create_error_response(error_msg, status_code=400)
                    return

            # ========== upload gambar ==========
            start_media_id = None
            end_media_id = None
            reference_images = []

            # I2V: proses first-last frame
            if video_type == "i2v" and images:
                if image_count == 1:
                    # cuma 1 gambar: jadi first frame aja
                    if stream:
                        yield self._create_stream_chunk("Mengunggah frame awal gambar...\n")
                    start_media_id = await self.flow_client.upload_image(
                        token.at,
                        images[0],
                        model_config["aspect_ratio"],
                        project_id=project_id,
                        token_id=token.id,
                        google_cookies=getattr(token, "google_cookies", None),
                    )
                    debug_logger.log_info(f"[I2V] Cuma upload first frame: {start_media_id}")

                elif image_count == 2:
                    # 2 gambar: first frame + last frame
                    if stream:
                        yield self._create_stream_chunk("Mengunggah frame awal dan akhir gambar...\n")
                    start_media_id = await self.flow_client.upload_image(
                        token.at,
                        images[0],
                        model_config["aspect_ratio"],
                        project_id=project_id,
                        token_id=token.id,
                        google_cookies=getattr(token, "google_cookies", None),
                    )
                    end_media_id = await self.flow_client.upload_image(
                        token.at,
                        images[1],
                        model_config["aspect_ratio"],
                        project_id=project_id,
                        token_id=token.id,
                        google_cookies=getattr(token, "google_cookies", None),
                    )
                    debug_logger.log_info(
                        f"[I2V] Upload first-last frame: {start_media_id}, {end_media_id}"
                    )

            # R2V: proses multi-gambar
            elif video_type == "r2v" and images:
                if stream:
                    yield self._create_stream_chunk(
                        f"Upload {image_count} gambar referensi...\n"
                    )

                for img in images:
                    media_id = await self.flow_client.upload_image(
                        token.at,
                        img,
                        model_config["aspect_ratio"],
                        project_id=project_id,
                        token_id=token.id,
                        google_cookies=getattr(token, "google_cookies", None),
                    )
                    reference_images.append(
                        {
                        "imageUsageType": "IMAGE_USAGE_TYPE_ASSET",
                            "mediaId": media_id,
                        }
                    )
                debug_logger.log_info(
                    f"[R2V] Sudah upload {len(reference_images)} gambar referensi"
                )

            # Omni R2V: gambar referensi diupload ke project, terus pakai RPC video gambar referensi sekarang
            elif video_type == "omni" and images:
                if stream:
                    yield self._create_stream_chunk(
                        f"Upload {image_count} gambar referensi Omni...\n"
                    )

                for img in images:
                    media_id = await self.flow_client.upload_image(
                        token.at,
                        img,
                        model_config["aspect_ratio"],
                        project_id=project_id,
                        token_id=token.id,
                        google_cookies=getattr(token, "google_cookies", None),
                    )
                    reference_images.append(
                        {
                        "imageUsageType": "IMAGE_USAGE_TYPE_ASSET",
                            "mediaId": media_id,
                        }
                    )
                debug_logger.log_info(
                    f"[VIDEO OMNI-R2V] Sudah upload {len(reference_images)} gambar referensi"
                )

            # ========== panggil API generate ==========
            if stream:
                yield self._create_stream_chunk("Mengirim tugas pembuatan video...\n")
            submit_started_at = time.time()

            # I2V: generate first-last frame
            if video_type == "i2v" and start_media_id:
                if end_media_id:
                    # ada first-last frame
                    result = await self.flow_client.generate_video_start_end(
                        at=token.at,
                        project_id=project_id,
                        prompt=prompt,
                        model_key=model_config["model_key"],
                        aspect_ratio=model_config["aspect_ratio"],
                        start_media_id=start_media_id,
                        end_media_id=end_media_id,
                        use_v2_model_config=use_v2_model_config,
                        user_paygate_tier=normalized_tier,
                        token_id=token.id,
                        token_video_concurrency=token.video_concurrency,
                        google_cookies=getattr(token, "google_cookies", None),
                    )
                else:
                    # cuma first frame - perlu buang _fl dari model_key
                    # kasus 1: _fl_ di tengah (misal veo_3_1_i2v_s_fast_fl_ultra_relaxed -> veo_3_1_i2v_s_fast_ultra_relaxed)
                    # kasus 2: _fl di akhir (misal veo_3_1_i2v_s_fast_ultra_fl -> veo_3_1_i2v_s_fast_ultra)
                    actual_model_key = model_config["model_key"].replace("_fl_", "_")
                    if actual_model_key.endswith("_fl"):
                        actual_model_key = actual_model_key[:-3]
                    debug_logger.log_info(
                        f"[I2V] mode single frame, model_key: {model_config['model_key']} -> {actual_model_key}"
                    )
                    result = await self.flow_client.generate_video_start_image(
                        at=token.at,
                        project_id=project_id,
                        prompt=prompt,
                        model_key=actual_model_key,
                        aspect_ratio=model_config["aspect_ratio"],
                        start_media_id=start_media_id,
                        use_v2_model_config=use_v2_model_config,
                        user_paygate_tier=normalized_tier,
                        token_id=token.id,
                        token_video_concurrency=token.video_concurrency,
                        google_cookies=getattr(token, "google_cookies", None),
                    )

            # R2V: generate multi-gambar
            elif video_type == "r2v" and reference_images:
                result = await self.flow_client.generate_video_reference_images(
                    at=token.at,
                    project_id=project_id,
                    prompt=prompt,
                    model_key=model_config["model_key"],
                    aspect_ratio=model_config["aspect_ratio"],
                    reference_images=reference_images,
                    user_paygate_tier=normalized_tier,
                    token_id=token.id,
                    token_video_concurrency=token.video_concurrency,
                    google_cookies=getattr(token, "google_cookies", None),
                )

            # Omni: ada gambar pakai jalur langsung Reference Images, nggak ada gambar pakai jalur teks murni
            elif video_type == "omni" and reference_images:
                if stream:
                    yield self._create_stream_chunk("Mengirim tugas video referensi Omni...\n")
                result = await self.flow_client.generate_video_reference_images(
                    at=token.at,
                    project_id=project_id,
                    prompt=prompt,
                    model_key=model_config.get("reference_model_key", "abra_r2v_8s"),
                    aspect_ratio=model_config["aspect_ratio"],
                    reference_images=reference_images,
                    user_paygate_tier=normalized_tier,
                    token_id=token.id,
                    token_video_concurrency=token.video_concurrency,
                    google_cookies=getattr(token, "google_cookies", None),
                )

            # Extend: lanjutin video
            elif video_type == "extend":
                if not video_media_id:
                    error_msg = "Lanjutin video butuh mediaGenerationId video sumber, kirim via image_url sebagai extend://VIDEO_MEDIA_ID"
                    if stream:
                        yield self._create_stream_chunk(f"{error_msg}\n")
                    self._mark_generation_failed(generation_result, error_msg)
                    yield self._create_error_response(error_msg, status_code=400)
                    return

                debug_logger.log_info(f"[EXTEND] Lanjutin video: {video_media_id}")
                if stream:
                    yield self._create_stream_chunk(
                        f"Task lanjutin video lagi di-submit, video sumber: {video_media_id[:8]}...\n"
                    )
                result = await self.flow_client.generate_video_extend(
                    at=token.at,
                    project_id=project_id,
                    prompt=prompt,
                    video_media_id=video_media_id,
                    model_key=model_config["model_key"],
                    aspect_ratio=model_config["aspect_ratio"],
                    user_paygate_tier=normalized_tier,
                    token_id=token.id,
                    token_video_concurrency=token.video_concurrency,
                )

            # T2V atau R2V tanpa gambar: generate teks murni
            else:
                result = await self.flow_client.generate_video_text(
                    at=token.at,
                    project_id=project_id,
                    prompt=prompt,
                    model_key=model_config["model_key"],
                    aspect_ratio=model_config["aspect_ratio"],
                    use_v2_model_config=use_v2_model_config,
                    user_paygate_tier=normalized_tier,
                    token_id=token.id,
                    token_video_concurrency=token.video_concurrency,
                    google_cookies=getattr(token, "google_cookies", None),
                )
            if video_trace is not None:
                video_trace["submit_generation_ms"] = int(
                    (time.time() - submit_started_at) * 1000
                )

            direct_video_url = str(result.get("video_url") or "").strip()
            if result.get("direct_media") and direct_video_url:
                await self.token_manager.record_usage(token.id, is_video=True)
                await self.token_manager.record_success(token.id)
                if getattr(self, "load_balancer", None):
                    self.load_balancer.clear_quota_cooldown(token.id, model_key)
                if self.proxy_manager and hasattr(
                    self.proxy_manager,
                    "record_attempt_success",
                ):
                    fingerprint = self.flow_client.get_request_fingerprint() or {}
                    await self.proxy_manager.record_attempt_success(
                        token.id,
                        str(fingerprint.get("proxy_url") or "").strip(),
                    )

                duration = time.time() - submit_started_at
                response_state["url"] = direct_video_url
                response_state["generated_assets"] = {
                    "type": "video",
                    "final_video_url": direct_video_url,
                    "delivery_mode": "frontend_direct_media",
                }
                await self._update_request_log_progress(
                    request_log_state,
                    token_id=token.id,
                    status_text="completed",
                    progress=100,
                )
                prompt_for_log = (
                    prompt if len(prompt) <= 2000 else f"{prompt[:2000]}...(truncated)"
                )
                await self._log_request(
                    token.id,
                    "generate_video",
                    {
                        "model": model_key,
                        "prompt": prompt_for_log,
                        "delivery_mode": "frontend_direct_media",
                    },
                    {
                        "status": "success",
                        "model": model_key,
                        "prompt": prompt_for_log,
                        "url": direct_video_url,
                        "performance": {
                            "status": "success",
                            "total_ms": int(duration * 1000),
                        },
                    },
                    200,
                    duration,
                    log_id=request_log_state.get("id"),
                    status_text="completed",
                    progress=100,
                )
                self._mark_generation_succeeded(generation_result)
                if stream:
                    yield self._create_stream_chunk(
                        f"<video src='{direct_video_url}' controls style='max-width:100%'></video>",
                        finish_reason="stop",
                    )
                else:
                    yield self._create_completion_response(
                        direct_video_url,
                        media_type="video",
                    )
                return

            # ambil task_id dan operations
            operations = result.get("operations", [])
            if not operations:
                self._mark_generation_failed(
                    generation_result,
                    "\u751f\u6210\u4efb\u52a1\u521b\u5efa\u5931\u8d25",
                )
                yield self._create_error_response("Gagal bikin task generate", status_code=502)
                return

            operation = operations[0]
            task_id = operation["operation"]["name"]
            scene_id = operation.get("sceneId")

            # simpan Task ke database
            task = Task(
                task_id=task_id,
                token_id=token.id,
                model=model_config["model_key"],
                prompt=prompt,
                status="processing",
                scene_id=scene_id,
            )
            await self.db.create_task(task)
            await self._update_request_log_progress(
                request_log_state,
                token_id=token.id,
                status_text="video_submitted",
                progress=45,
                response_extra={"task_id": task_id, "scene_id": scene_id},
            )

            # polling hasil
            if stream:
                yield self._create_stream_chunk(f"Video sedang diproses...\n")

            # cek apakah perlu upscale
            upsample_config = model_config.get("upsample")

            # kalau extend, oper media_id video sumber buat digabung nanti
            extend_source_id = video_media_id if video_type == "extend" else None
            async for chunk in self._poll_video_result(
                token,
                project_id,
                operations,
                stream,
                upsample_config,
                generation_result,
                response_state,
                request_log_state,
                extend_source_media_id=extend_source_id,
            ):
                yield chunk

        finally:
            pass

    async def _poll_video_result(
        self,
        token,
        project_id: str,
        operations: List[Dict],
        stream: bool,
        upsample_config: Optional[Dict] = None,
        generation_result: Optional[Dict[str, Any]] = None,
        response_state: Optional[Dict[str, Any]] = None,
        request_log_state: Optional[Dict[str, Any]] = None,
        extend_source_media_id: Optional[str] = None,
    ) -> AsyncGenerator:
        """Polling hasil generate video
        
        Args:
            upsample_config: konfigurasi upscale {"resolution": "VIDEO_RESOLUTION_4K", "model_key": "veo_3_1_upsampler_4k"}
        """

        if response_state is None:
            response_state = self._create_response_state()

        normalized_tier = normalize_user_paygate_tier(token.user_paygate_tier)
        poll_interval = max(0.1, float(config.poll_interval))
        max_attempts = _video_poll_attempt_budget(
            config.video_timeout,
            poll_interval,
            upsample=bool(upsample_config),
        )
        poll_budget_seconds = max_attempts * poll_interval
        poll_deadline = time.monotonic() + poll_budget_seconds

        consecutive_poll_errors = 0
        last_poll_error: Optional[Exception] = None
        max_consecutive_poll_errors = 3

        for attempt in range(max_attempts):
            remaining = poll_deadline - time.monotonic()
            if remaining <= 0:
                break
            await asyncio.sleep(min(poll_interval, remaining))
            remaining = poll_deadline - time.monotonic()
            if remaining <= 0:
                break

            try:
                # Include the status RPC itself in the wall-time budget. The outer
                # deadline prevents slow retries from extending video_timeout.
                result = await asyncio.wait_for(
                    self.flow_client.check_video_status(
                        token.at,
                        operations,
                        token_id=token.id,
                        google_cookies=getattr(token, "google_cookies", None),
                    ),
                    timeout=remaining,
                )
                checked_operations = result.get("operations", [])
                consecutive_poll_errors = 0
                last_poll_error = None

                if not checked_operations:
                    continue

                operation = checked_operations[0]
                status = operation.get("status")

                # update status - lapor tiap 20 detik (poll_interval=3 detik, 20 detik ~7x polling)
                progress_update_interval = 7  # tiap 7x polling = 21 detik
                if stream and attempt % progress_update_interval == 0:  # lapor tiap 20 detik
                    progress = min(int((attempt / max_attempts) * 100), 95)
                    await self._update_request_log_progress(
                        request_log_state,
                        token_id=token.id,
                        status_text="video_polling",
                        progress=max(45, progress),
                        response_extra={"upstream_status": status},
                    )
                    yield self._create_stream_chunk(f"Progres: {progress}%\n")

                # cek status
                if status == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                    try:
                        resolved_video = await self._resolve_video_asset(
                            token, operation
                        )
                    except Exception as redirect_error:
                        media_name = (
                            operation.get("mediaName")
                            or operation.get("name")
                            or operation["operation"].get("name")
                        )
                        error_msg = f"Video berhasil digenerate tapi gagal ambil alamat media: {self._normalize_error_message(redirect_error)}"
                        debug_logger.log_warning(
                            f"[VIDEO POLL] Gagal ambil URL video: media={media_name}, error={redirect_error}"
                        )
                        await self._fail_video_task(checked_operations, error_msg)
                        self._mark_generation_failed(generation_result, error_msg)
                        yield self._create_error_response(error_msg, status_code=502)
                        return

                    video_url = resolved_video["video_url"]
                    video_media_id = resolved_video["video_media_id"]
                    aspect_ratio = resolved_video["aspect_ratio"]
                    media_name = resolved_video["media_name"]
                    metadata = resolved_video["metadata"]
                    video_info = resolved_video["video_info"]

                    if not video_url:
                        media_name_for_fetch = operation.get("mediaName") or operation[
                            "operation"
                        ].get("name", "")
                        if media_name_for_fetch:
                            if stream:
                                yield self._create_stream_chunk(
                                    "Generate video selesai, lagi download file video...\n"
                                )
                            try:
                                media_result = await self.flow_client.get_media(
                                    token.at,
                                    media_name_for_fetch,
                                    token_id=token.id,
                                    google_cookies=getattr(
                                        token, "google_cookies", None
                                    ),
                                    project_id=project_id,
                                )
                                encoded_video = media_result.get("video", {}).get(
                                    "encodedVideo", ""
                                )
                                if encoded_video:
                                    cached_filename = (
                                        await self.file_cache.cache_base64_video(
                                        encoded_video
                                    )
                                    )
                                    video_url = f"{self._get_base_url(response_state)}/tmp/{cached_filename}"
                                    video_info["fifeUrl"] = video_url
                                    debug_logger.log_info(
                                        f"[VIDEO] Video fetched via get_media and cached: {cached_filename}"
                                    )
                                else:
                                    debug_logger.log_error(
                                        "[VIDEO] get_media returned empty encodedVideo"
                                    )
                            except Exception as fetch_err:
                                debug_logger.log_error(
                                    f"[VIDEO] Failed to fetch video via get_media: {fetch_err}"
                                )

                    if not video_url:
                        error_msg = "Video berhasil digenerate tapi nggak dapet alamat media"
                        await self._fail_video_task(checked_operations, error_msg)
                        self._mark_generation_failed(generation_result, error_msg)
                        yield self._create_error_response(error_msg, status_code=502)
                        return

                    video_info["url"] = video_url
                    video_info["mediaName"] = media_name
                    video_info["mediaGenerationId"] = video_media_id
                    metadata.setdefault("video", video_info)
                    operation["operation"]["metadata"] = metadata

                    # ========== proses upscale video ==========
                    if upsample_config and video_media_id:
                        if stream:
                            resolution_name = (
                                "4K"
                                if "4K" in upsample_config["resolution"]
                                else "1080P"
                            )
                            yield self._create_stream_chunk(
                                f"\nGenerate video selesai, mulai {resolution_name} upscale... (bisa butuh 30  menit)\n"
                            )
                        
                        try:
                            # submit task upscale
                            upsample_result = await self.flow_client.upsample_video(
                                at=token.at,
                                project_id=project_id,
                                video_media_id=video_media_id,
                                aspect_ratio=aspect_ratio,
                                resolution=upsample_config["resolution"],
                                model_key=upsample_config["model_key"],
                                user_paygate_tier=normalized_tier,
                                token_id=token.id,
                                token_video_concurrency=token.video_concurrency,
                                google_cookies=getattr(token, "google_cookies", None),
                            )
                            
                            upsample_operations = upsample_result.get("operations", [])
                            if upsample_operations:
                                if stream:
                                    yield self._create_stream_chunk(
                                        "Task upscale sudah di-submit, lanjut polling...\n"
                                    )
                                
                                # polling rekursif hasil upscale (nggak di-upscale lagi)
                                async for chunk in self._poll_video_result(
                                    token,
                                    project_id,
                                    upsample_operations,
                                    stream,
                                    None,
                                    generation_result,
                                    response_state,
                                    request_log_state,
                                ):
                                    yield chunk
                                return
                            else:
                                if stream:
                                    yield self._create_stream_chunk(
                                        "⚠️ Gagal bikin task upscale, balikin video asli\n"
                                    )
                        except Exception as e:
                            debug_logger.log_error(f"Video upsample failed: {str(e)}")
                            if stream:
                                yield self._create_stream_chunk(
                                    f"⚠️ Upscale gagal: {str(e)}, balikin video asli\n"
                            )
                            
                    # Current Flow returns the generated extend media as its own
                    # asset. There is no current frontend RPC that concatenates
                    # two media IDs, so never label this single segment as a
                    # completed 16-second composite.
                    if extend_source_media_id and video_media_id and stream:
                        yield self._create_stream_chunk(
                            "Potongan lanjutan sudah digenerate; frontend Flow sekarang nggak sediain RPC sambung media, return potongannya aja.\n"
                        )

                    # cache video (kalau diaktifkan)
                    local_url = video_url
                    if config.cache_enabled:
                        await self._update_request_log_progress(
                            request_log_state,
                            token_id=token.id,
                            status_text="caching_video",
                            progress=92,
                        )
                        try:
                            if stream:
                                yield self._create_stream_chunk("Menyimpan cache file video...\n")
                            cached_filename = await self.file_cache.download_and_cache(
                                video_url, "video"
                            )
                            local_url = f"{self._get_base_url(response_state)}/tmp/{cached_filename}"
                            if stream:
                                yield self._create_stream_chunk(
                                    "✅ video berhasil di-cache, siap return alamat cache...\n"
                                )
                        except Exception as e:
                            debug_logger.log_error(f"Failed to cache video: {str(e)}")
                            # gagal cache nggak ngaruh ke hasil, pakai URL asli
                            local_url = video_url
                            if stream:
                                cache_error = self._normalize_error_message(
                                    e, max_length=120
                                )
                                yield self._create_stream_chunk(
                                    f"⚠️ Gagal cache: {cache_error}\nlagi return link sumber...\n"
                                )
                    else:
                        if stream:
                            yield self._create_stream_chunk(
                                "cache dimatikan, lagi return link sumber...\n"
                            )

                    # update database
                    task_id = operation["operation"]["name"]
                    await self.db.update_task(
                        task_id,
                        status="completed",
                        progress=100,
                        result_urls=[local_url],
                        completed_at=time.time(),
                    )

                    # simpan URL buat pencatatan log
                    response_state["url"] = local_url
                    response_state["generated_assets"] = {
                        "type": "video",
                        "final_video_url": local_url,
                        "mediaGenerationId": video_media_id,
                        "mediaName": media_name,
                        "aspectRatio": aspect_ratio,
                        "model": resolved_video.get("model"),
                        "duration": resolved_video.get("duration"),
                    }

                    # return hasil
                    self._mark_generation_succeeded(generation_result)

                    if stream:
                        yield self._create_stream_chunk(
                            f"<video src='{local_url}' data-media-id='{video_media_id}' controls style='max-width:100%'></video>",
                            finish_reason="stop",
                        )

                    else:
                        yield self._create_completion_response(
                            local_url,  # langsung oper URL, biar method yang format di dalam
                            media_type="video",
                        )
                    return

                elif status == "MEDIA_GENERATION_STATUS_FAILED":
                    # generate gagal - ekstrak info error
                    error_info = operation.get("operation", {}).get("error", {})
                    error_code = error_info.get("code", "unknown")
                    error_message = error_info.get("message", "Error tidak dikenal")
                    
                    # update status task di database
                    await self._fail_video_task(
                        checked_operations, f"{error_message} (code: {error_code})"
                    )
                    
                    # return pesan error yang ramah, suruh user retry
                    friendly_error = f"Gagal membuat video: {error_message}, silakan coba lagi"
                    self._mark_generation_failed(generation_result, friendly_error)
                    if stream:
                        yield self._create_stream_chunk(f"Error: {friendly_error}\n")
                    yield self._create_error_response(friendly_error, status_code=502)
                    return

                elif status.startswith("MEDIA_GENERATION_STATUS_ERROR"):
                    # ??????
                    error_msg = f"Gagal membuat video: {status}"
                    await self._fail_video_task(checked_operations, error_msg)
                    self._mark_generation_failed(generation_result, error_msg)
                    yield self._create_error_response(error_msg, status_code=502)
                    return
                    
            except Exception as e:
                last_poll_error = e
                consecutive_poll_errors += 1
                debug_logger.log_error(f"Poll error: {str(e)}")
                if consecutive_poll_errors >= max_consecutive_poll_errors:
                    error_msg = f"Gagal query status video: {self._normalize_error_message(e)}"
                    await self._fail_video_task(operations, error_msg)
                    self._mark_generation_failed(generation_result, error_msg)
                    if stream:
                        yield self._create_stream_chunk(f"Error: {error_msg}\n")
                    yield self._create_error_response(error_msg, status_code=502)
                    return
                continue

        # timeout
        if last_poll_error is not None:
            error_msg = f"Query status video gagal terus: {self._normalize_error_message(last_poll_error)}"
        else:
            error_msg = f"Generate video timeout (lebih dari {int(poll_budget_seconds)} detik belum selesai)"
        await self._fail_video_task(operations, error_msg)
        self._mark_generation_failed(generation_result, error_msg)
        yield self._create_error_response(error_msg, status_code=504)

    # ========== format response ==========

    def _create_stream_chunk(
        self, content: str, role: str = None, finish_reason: str = None
    ) -> str:
        """Bikin chunk response streaming"""
        import json
        import time

        chunk = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "flow2api",
            "choices": [{"index": 0, "delta": {}, "finish_reason": finish_reason}],
        }

        if role:
            chunk["choices"][0]["delta"]["role"] = role

        if finish_reason:
            chunk["choices"][0]["delta"]["content"] = content
        else:
            chunk["choices"][0]["delta"]["reasoning_content"] = content

        return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    def _create_completion_response(
        self,
        content: str,
        media_type: str = "image",
        is_availability_check: bool = False,
    ) -> str:
        """Bikin response non-streaming

        Args:
            content: URL media atau pesan teks murni
            media_type: tipe media ("image" atau "video")
            is_availability_check: apakah response cek ketersediaan (pesan teks murni)

        Returns:
            response format JSON
        """
        import json
        import time

        # cek ketersediaan: return pesan teks murni
        if is_availability_check:
            formatted_content = content
        else:
            # generate media: format konten jadi Markdown sesuai tipe media
            if media_type == "video":
                formatted_content = (
                    f"```html\n<video src='{content}' controls></video>\n```"
                )
            else:  # image
                formatted_content = f"![Generated Image]({content})"

        response = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "flow2api",
            "choices": [
                {
                "index": 0,
                    "message": {"role": "assistant", "content": formatted_content},
                    "finish_reason": "stop",
                }
            ],
        }

        return json.dumps(response, ensure_ascii=False)

    def _create_error_response(self, error_message: str, status_code: int = 500) -> str:
        """Bikin response error"""
        import json

        error = {
            "error": {
                "message": error_message,
                "type": "server_error"
                if status_code >= 500
                else "invalid_request_error",
                "code": "generation_failed",
                "status_code": status_code,
            }
        }

        return json.dumps(error, ensure_ascii=False)

    def _get_base_url(self, response_state: Optional[Dict[str, Any]] = None) -> str:
        """Ambil base URL buat akses file cache"""
        # kalau domain akses cache dikonfigurasi, selalu utamakan itu, biar nggak ketimpa Host/IP request.
        if config.cache_base_url:
            return config.cache_base_url.rstrip("/")

        request_base_url = ""
        if isinstance(response_state, dict):
            request_base_url = (
                (response_state.get("base_url") or "").strip().rstrip("/")
            )
        if request_base_url:
            return request_base_url

        # fallback ke alamat service, biar alamat listen 0.0.0.0 / :: nggak langsung dikasih ke client
        server_host = (config.server_host or "").strip()
        if server_host in {"", "0.0.0.0", "::", "[::]"}:
            server_host = "127.0.0.1"

        return f"http://{server_host}:{config.server_port}"

    async def _update_request_log_progress(
        self,
        request_log_state: Optional[Dict[str, Any]],
        *,
        token_id: Optional[int] = None,
        status_text: str,
        progress: int,
        response_extra: Optional[Dict[str, Any]] = None,
    ):
        """?????????????"""
        if not isinstance(request_log_state, dict):
            return
        log_id = request_log_state.get("id")
        if not log_id:
            return

        safe_progress = max(0, min(100, int(progress)))
        now = time.time()
        last_status_text = str(request_log_state.get("last_status_text") or "").strip()
        last_progress = int(request_log_state.get("last_progress") or 0)
        last_updated_at = float(request_log_state.get("last_progress_update_at") or 0)

        request_log_state["progress"] = safe_progress
        request_log_state["last_status_text"] = status_text
        request_log_state["last_progress"] = safe_progress
        payload = {
            "status": "processing",
            "status_text": status_text,
            "progress": safe_progress,
        }
        if isinstance(response_extra, dict):
            payload.update(response_extra)

        should_write = (
            safe_progress in (0, 100)
            or status_text != last_status_text
            or safe_progress >= last_progress + 5
            or (now - last_updated_at) >= 1.0
        )
        if not should_write:
            return

        request_log_state["last_progress_update_at"] = now

        try:
            await self.db.update_request_log(
                log_id,
                token_id=token_id,
                response_body=json.dumps(payload, ensure_ascii=False),
                status_code=102,
                duration=0,
                status_text=status_text,
                progress=safe_progress,
            )
        except Exception as e:
            debug_logger.log_error(f"Failed to update request log progress: {e}")

    async def _log_request(
        self,
        token_id: Optional[int],
        operation: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        status_code: int,
        duration: float,
        log_id: Optional[int] = None,
        status_text: Optional[str] = None,
        progress: Optional[int] = None,
    ):
        """???????????? log_id ????????"""
        try:
            effective_status_text = status_text or (
                "completed"
                if status_code == 200
                else "failed"
                if status_code >= 400
                else "processing"
            )
            effective_progress = progress
            if effective_progress is None:
                effective_progress = (
                    100 if status_code == 200 else 0 if status_code >= 400 else 0
                )
            effective_progress = max(0, min(100, int(effective_progress)))

            request_body = json.dumps(request_data, ensure_ascii=False)
            response_body = json.dumps(response_data, ensure_ascii=False)

            if log_id:
                await self.db.update_request_log(
                    log_id,
                    token_id=token_id,
                    operation=operation,
                    request_body=request_body,
                    response_body=response_body,
                    status_code=status_code,
                    duration=duration,
                    status_text=effective_status_text,
                    progress=effective_progress,
                )
                return log_id

            log = RequestLog(
                token_id=token_id,
                operation=operation,
                request_body=request_body,
                response_body=response_body,
                status_code=status_code,
                duration=duration,
                status_text=effective_status_text,
                progress=effective_progress,
            )
            return await self.db.add_request_log(log)
        except Exception as e:
            debug_logger.log_error(f"Failed to log request: {e}")
            return None
