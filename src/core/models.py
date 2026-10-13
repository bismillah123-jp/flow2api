"""Data models for Flow2API"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Union, Any, Literal
from datetime import datetime


class Token(BaseModel):
    """Token model for Flow2API"""

    id: Optional[int] = None

    # Info autentikasi (inti)
    st: str  # Identifier kompatibilitas login state; Flow versi baru pakai Google/Flow Cookies lengkap
    at: Optional[str] = None  # Identifier kompatibilitas setelah validasi login state
    at_expires: Optional[datetime] = None  # Waktu validasi login state berikutnya

    # Info dasar
    email: str
    name: Optional[str] = ""
    remark: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    use_count: int = 0

    # Field khusus VideoFX
    credits: int = 0  # Sisa credits
    user_paygate_tier: Optional[str] = None  # PAYGATE_TIER_ONE

    # Manajemen project
    current_project_id: Optional[str] = None  # UUID project yang dipakai saat ini
    current_project_name: Optional[str] = None  # Nama project

    # Switch fitur
    image_enabled: bool = True
    video_enabled: bool = True

    # Batas concurrency
    image_concurrency: int = -1  # -1 berarti tanpa batas
    video_concurrency: int = -1  # -1 berarti tanpa batas

    # Proxy captcha (level token, bisa override proxy captcha browser global)
    captcha_proxy_url: Optional[str] = None
    extension_route_key: Optional[str] = None

    # Refresh Google/Flow Cookie; pertahankan nama field lama agar kompatibel dengan data yang ada
    protocol_mode: str = "session"  # session/protocol
    google_cookies: str = ""
    login_account: str = ""
    login_password: str = ""
    proxy_url: str = ""
    auto_refresh_enabled: bool = True
    refresh_interval_minutes: int = 120
    last_st_refresh_at: Optional[datetime] = None
    last_st_refresh_result: str = ""

    # Terkait ban 429
    ban_reason: Optional[str] = None  # Alasan ban: "429_rate_limit" atau None
    banned_at: Optional[datetime] = None  # Waktu di-ban


class Project(BaseModel):
    """Project model for VideoFX"""

    id: Optional[int] = None
    project_id: str  # UUID project VideoFX
    token_id: int  # ID Token yang terasosiasi
    project_name: str  # Nama project
    tool_name: str = "PINHOLE"  # Nama tool, fixed PINHOLE
    is_active: bool = True
    created_at: Optional[datetime] = None


class TokenStats(BaseModel):
    """Token statistics"""

    token_id: int
    image_count: int = 0
    video_count: int = 0
    success_count: int = 0
    error_count: int = 0  # Historical total errors (never reset)
    last_success_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    # Statistik hari ini
    today_image_count: int = 0
    today_video_count: int = 0
    today_error_count: int = 0
    today_date: Optional[str] = None
    # Counter error beruntun (untuk penilaian auto-disable)
    consecutive_error_count: int = 0


class Task(BaseModel):
    """Generation task"""

    id: Optional[int] = None
    task_id: str  # operation name yang dikembalikan Flow API
    token_id: int
    model: str
    prompt: str
    status: str  # processing, completed, failed
    progress: int = 0  # 0-100
    result_urls: Optional[List[str]] = None
    error_message: Optional[str] = None
    scene_id: Optional[str] = None  # sceneId dari Flow API
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class RequestLog(BaseModel):
    """API request log"""

    id: Optional[int] = None
    token_id: Optional[int] = None
    operation: str
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    status_code: int
    duration: float
    status_text: Optional[str] = None
    progress: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AdminConfig(BaseModel):
    """Admin configuration"""

    id: int = 1
    username: str
    password: str
    api_key: str
    error_ban_threshold: int = 3  # Auto-disable token after N consecutive errors


class ProxyConfig(BaseModel):
    """Proxy configuration"""

    id: int = 1
    enabled: bool = False  # Switch proxy request
    proxy_url: Optional[str] = None  # Alamat proxy request
    media_proxy_enabled: bool = False  # Switch proxy upload/download gambar
    media_proxy_url: Optional[str] = None  # Alamat proxy upload/download gambar


class GenerationConfig(BaseModel):
    """Generation timeout configuration"""

    id: int = 1
    image_timeout: int = 300  # seconds
    video_timeout: int = 1500  # seconds
    max_retries: int = 3  # Jumlah retry request maksimum


class CallLogicConfig(BaseModel):
    """Token selection call logic configuration"""

    id: int = 1
    call_mode: str = "default"
    polling_mode_enabled: bool = False
    updated_at: Optional[datetime] = None


class CacheConfig(BaseModel):
    """Cache configuration"""

    id: int = 1
    cache_enabled: bool = False
    cache_timeout: int = 7200  # seconds (2 hours), 0 means never expire
    cache_base_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DebugConfig(BaseModel):
    """Debug configuration"""

    id: int = 1
    enabled: bool = False
    log_requests: bool = True
    log_responses: bool = True
    mask_token: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CaptchaConfig(BaseModel):
    """Captcha configuration"""

    id: int = 1
    captcha_method: str = (
        "yescaptcha"  # yescaptcha/captcharun/twocaptcha/capsolver/ezcaptcha/browser/personal/remote_browser
    )
    yescaptcha_api_key: str = ""
    yescaptcha_base_url: str = "https://api.yescaptcha.com"
    yescaptcha_task_type: str = "RecaptchaV3TaskProxylessM1S9"
    capmonster_api_key: str = ""
    capmonster_base_url: str = "https://api.capmonster.cloud"
    ezcaptcha_api_key: str = ""
    ezcaptcha_base_url: str = "https://api.ez-captcha.com"
    capsolver_api_key: str = ""
    capsolver_base_url: str = "https://api.capsolver.com"
    captcharun_api_key: str = ""
    captcharun_base_url: str = "https://api.captcha-run.com"
    twocaptcha_api_key: str = ""
    twocaptcha_base_url: str = "https://api.2captcha.com"
    remote_browser_base_url: str = ""
    remote_browser_api_key: str = ""
    remote_browser_timeout: int = 60
    website_key: str = "6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV"
    page_action: str = "IMAGE_GENERATION"
    browser_proxy_enabled: bool = False  # Apakah captcha browser pakai proxy
    browser_proxy_url: Optional[str] = None  # URL proxy captcha browser
    browser_count: int = 1  # Jumlah instance captcha browser
    personal_project_pool_size: int = (
        4  # Jumlah project pool yang dirawat default per Token (hanya memengaruhi rotasi project)
    )
    personal_max_resident_tabs: int = 5  # Batas atas tab captcha bersama per instance browser built-in
    browser_personal_fresh_restart_every_n_solves: int = (
        10  # Setelah berapa kali solve sukses browser dibersihkan dan direstart, 0 = nonaktif
    )
    personal_idle_tab_ttl_seconds: int = 600  # Timeout idle tab browser built-in (detik)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PluginConfig(BaseModel):
    """Plugin connection configuration"""

    id: int = 1
    connection_token: str = ""  # Token koneksi plugin
    auto_enable_on_update: bool = True  # Otomatis aktifkan saat update token (default aktif)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TokenRefreshConfig(BaseModel):
    """Protocol ST refresh configuration"""

    id: int = 1
    enabled: bool = True
    refresh_interval_minutes: int = 120
    updated_at: Optional[datetime] = None


# OpenAI Compatible Request Models
class ChatMessage(BaseModel):
    """Chat message"""

    role: str
    content: Union[str, List[dict]]  # string or multimodal array


class ImageConfig(BaseModel):
    """Gemini imageConfig parameters"""

    aspectRatio: Optional[str] = None  # "16:9", "9:16", "1:1", "4:3", "3:4"
    imageSize: Optional[str] = None  # "2k", "4k"

    # Kompatibel dengan field size/quality atau snake_case yang mungkin di-pass-through upstream seperti OpenAI/NewAPI
    model_config = ConfigDict(extra="allow")


class GenerationConfigParam(BaseModel):
    """Gemini generationConfig parameters (for model name resolution)"""

    responseModalities: Optional[List[str]] = None  # ["IMAGE", "TEXT"]
    imageConfig: Optional[ImageConfig] = None

    model_config = ConfigDict(extra="allow")


class GeminiInlineData(BaseModel):
    """Gemini inline binary data."""

    mimeType: str
    data: str


class GeminiFileData(BaseModel):
    """Gemini file reference."""

    fileUri: str
    mimeType: Optional[str] = None


class GeminiPart(BaseModel):
    """Gemini content part."""

    text: Optional[str] = None
    inlineData: Optional[GeminiInlineData] = None
    fileData: Optional[GeminiFileData] = None

    model_config = ConfigDict(extra="allow")


class GeminiContent(BaseModel):
    """Gemini content block."""

    role: Optional[Literal["user", "model"]] = None
    parts: List[GeminiPart]


class GeminiGenerateContentRequest(BaseModel):
    """Gemini official generateContent request."""

    contents: List[GeminiContent]
    generationConfig: Optional[GenerationConfigParam] = None
    systemInstruction: Optional[GeminiContent] = None

    model_config = ConfigDict(extra="allow")


class ChatCompletionRequest(BaseModel):
    """Chat completion request (OpenAI compatible + Gemini extension)"""

    model: str
    messages: Optional[List[ChatMessage]] = None
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    # Flow2API specific parameters
    image: Optional[str] = None  # Base64 encoded image (deprecated, use messages)
    video: Optional[str] = None  # Base64 encoded video (deprecated)
    # Gemini extension parameters (from extra_body or top-level)
    generationConfig: Optional[GenerationConfigParam] = None
    contents: Optional[List[Any]] = None  # Gemini native contents

    model_config = ConfigDict(
        extra="allow"
    )  # Allow extra fields like extra_body passthrough
