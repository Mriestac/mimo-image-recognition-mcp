import base64
import mimetypes
import os
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("mimo-multimedia-recognition")


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------


def load_mimo_settings() -> dict[str, str]:
    """
    从 MCP 启动配置的 env 字段读取 MIMO 配置。

    需要在 MCP 配置中提供：
    - MIMO_API_KEY
    - MIMO_API_BASE
    - MIMO_MODEL
    """
    api_key = os.getenv("MIMO_API_KEY")
    api_base = os.getenv("MIMO_API_BASE")
    model = os.getenv("MIMO_MODEL")

    missing = []

    if not api_key:
        missing.append("MIMO_API_KEY")

    if not api_base:
        missing.append("MIMO_API_BASE")

    if not model:
        missing.append("MIMO_MODEL")

    if missing:
        raise RuntimeError(
            "MIMO MCP 缺少必要配置："
            + ", ".join(missing)
            + "\n请在 MCP 启动配置的 env 字段中填写 API Key、请求地址和模型名称。"
        )

    return {
        "api_key": api_key,
        "api_base": api_base.rstrip("/"),
        "model": model,
    }


def build_chat_completions_url(api_base: str) -> str:
    """
    支持两种写法：

    1. MIMO_API_BASE=https://api.xiaomimimo.com/v1
    2. MIMO_API_BASE=https://api.xiaomimimo.com/v1/chat/completions
    """
    api_base = api_base.rstrip("/")

    if api_base.endswith("/chat/completions"):
        return api_base

    return f"{api_base}/chat/completions"


# ---------------------------------------------------------------------------
# MIME 类型推断
# ---------------------------------------------------------------------------

IMAGE_EXTENSIONS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

AUDIO_EXTENSIONS = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
}

VIDEO_EXTENSIONS = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".wmv": "video/x-ms-wmv",
}


def _guess_mime_type(file_path: Path, category: str, extensions: dict[str, str]) -> str:
    """
    根据文件后缀推断 MIME 类型。
    """
    mime_type, _ = mimetypes.guess_type(str(file_path))

    if mime_type is None:
        suffix = file_path.suffix.lower()

        if suffix in extensions:
            return extensions[suffix]

        supported = ", ".join(sorted(k.lstrip(".") for k in extensions))
        raise ValueError(
            f"无法识别{category}类型：{file_path.suffix}。"
            f"请使用 {supported} 格式。"
        )

    expected_prefix = {
        "图片": "image/",
        "音频": "audio/",
        "视频": "video/",
    }[category]

    if not mime_type.startswith(expected_prefix):
        raise ValueError(f"文件不是{category}类型：{mime_type}")

    return mime_type


def guess_image_mime_type(image_path: Path) -> str:
    return _guess_mime_type(image_path, "图片", IMAGE_EXTENSIONS)


def guess_audio_mime_type(audio_path: Path) -> str:
    return _guess_mime_type(audio_path, "音频", AUDIO_EXTENSIONS)


def guess_video_mime_type(video_path: Path) -> str:
    return _guess_mime_type(video_path, "视频", VIDEO_EXTENSIONS)


# ---------------------------------------------------------------------------
# 本地文件转 data URL
# ---------------------------------------------------------------------------


def _local_file_to_data_url(
    file_path: str,
    category: str,
    max_size_mb: int,
    mime_func,
) -> str:
    """
    把本地文件转成 data:<mime>;base64,... 格式。
    """
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"{category}文件不存在：{path}")

    if not path.is_file():
        raise ValueError(f"路径不是文件：{path}")

    file_size_mb = path.stat().st_size / 1024 / 1024

    if file_size_mb > max_size_mb:
        raise ValueError(
            f"{category}文件过大：{file_size_mb:.2f} MB。"
            f"当前限制为 {max_size_mb} MB 以内。"
        )

    mime_type = mime_func(path)

    with path.open("rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def local_image_to_data_url(image_path: str) -> str:
    return _local_file_to_data_url(image_path, "图片", 20, guess_image_mime_type)


def local_audio_to_data_url(audio_path: str) -> str:
    return _local_file_to_data_url(audio_path, "音频", 100, guess_audio_mime_type)


def local_video_to_data_url(video_path: str) -> str:
    return _local_file_to_data_url(video_path, "视频", 300, guess_video_mime_type)


# ---------------------------------------------------------------------------
# URL 校验
# ---------------------------------------------------------------------------


def _validate_url(url: str, category: str, data_prefix: str) -> str:
    """
    校验网络 URL 或 data: Base64 URL。
    """
    if not (
        url.startswith("http://")
        or url.startswith("https://")
        or url.startswith(data_prefix)
    ):
        raise ValueError(
            f"{category} URL 必须是 http、https 或 {data_prefix}...;base64,... 格式。"
        )

    return url


def validate_image_url(image_url: str) -> str:
    return _validate_url(image_url, "图片", "data:image/")


def validate_audio_url(audio_url: str) -> str:
    return _validate_url(audio_url, "音频", "data:audio/")


def validate_video_url(video_url: str) -> str:
    return _validate_url(video_url, "视频", "data:video/")


# ---------------------------------------------------------------------------
# 构建媒体 URL 列表
# ---------------------------------------------------------------------------


def _build_media_urls(
    file_path: str | None,
    file_url: str | None,
    file_paths: list[str] | None,
    file_urls: list[str] | None,
    category: str,
    local_func,
    validate_func,
    max_count: int,
) -> list[str]:
    """
    构建媒体 URL 列表（通用逻辑）。
    """
    result: list[str] = []

    if file_path:
        result.append(local_func(file_path))

    if file_paths:
        for path in file_paths:
            result.append(local_func(path))

    if file_url:
        result.append(validate_func(file_url))

    if file_urls:
        for url in file_urls:
            result.append(validate_func(url))

    if not result:
        raise ValueError(
            f"必须至少传入一个{category}文件："
            f"{category}_path、{category}_url、{category}_paths 或 {category}_urls。"
        )

    if len(result) > max_count:
        raise ValueError(
            f"一次最多支持 {max_count} 个{category}文件，当前传入了 {len(result)} 个。"
        )

    return result


def build_image_urls(
    image_path: str | None = None,
    image_url: str | None = None,
    image_paths: list[str] | None = None,
    image_urls: list[str] | None = None,
) -> list[str]:
    return _build_media_urls(
        image_path, image_url, image_paths, image_urls,
        "图片", local_image_to_data_url, validate_image_url, 6,
    )


def build_audio_urls(
    audio_path: str | None = None,
    audio_url: str | None = None,
    audio_paths: list[str] | None = None,
    audio_urls: list[str] | None = None,
) -> list[str]:
    return _build_media_urls(
        audio_path, audio_url, audio_paths, audio_urls,
        "音频", local_audio_to_data_url, validate_audio_url, 10,
    )


def build_video_urls(
    video_path: str | None = None,
    video_url: str | None = None,
    video_paths: list[str] | None = None,
    video_urls: list[str] | None = None,
) -> list[str]:
    return _build_media_urls(
        video_path, video_url, video_paths, video_urls,
        "视频", local_video_to_data_url, validate_video_url, 5,
    )


# ---------------------------------------------------------------------------
# 通用 MIMO API 调用
# ---------------------------------------------------------------------------


async def call_mimo_api(
    *,
    content_parts: list[dict[str, Any]],
    prompt: str,
    system_prompt: str | None,
    temperature: float,
    max_tokens: int,
) -> str:
    """
    调用 MIMO 多模态理解接口（通用）。

    content_parts 已包含各媒体内容块，此函数追加 text 块并发送请求。
    """
    if not prompt.strip():
        raise ValueError("prompt 不能为空。")

    if temperature < 0:
        raise ValueError("temperature 不能小于 0。")

    if max_tokens <= 0:
        raise ValueError("max_tokens 必须大于 0。")

    settings = load_mimo_settings()
    endpoint = build_chat_completions_url(settings["api_base"])

    messages: list[dict[str, Any]] = []

    if system_prompt and system_prompt.strip():
        messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

    # 追加文本 prompt
    content_parts.append(
        {
            "type": "text",
            "text": prompt,
        }
    )

    messages.append(
        {
            "role": "user",
            "content": content_parts,
        }
    )

    payload: dict[str, Any] = {
        "model": settings["model"],
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
    }

    headers = {
        "api-key": settings["api_key"],
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload,
            )
    except httpx.HTTPError as exc:
        return (
            "MIMO API 请求失败。\n"
            f"请求地址：{endpoint}\n"
            f"模型名称：{settings['model']}\n"
            f"错误信息：{exc}"
        )

    if response.status_code >= 400:
        return (
            "MIMO API 调用失败。\n"
            f"HTTP 状态码：{response.status_code}\n"
            f"请求地址：{endpoint}\n"
            f"模型名称：{settings['model']}\n"
            f"响应内容：{response.text}"
        )

    try:
        data = response.json()
    except ValueError:
        return (
            "MIMO API 返回内容不是合法 JSON。\n"
            f"HTTP 状态码：{response.status_code}\n"
            f"响应内容：{response.text}"
        )

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return f"MIMO API 返回了非预期格式：\n{data}"


# ---------------------------------------------------------------------------
# MCP 工具：图片理解
# ---------------------------------------------------------------------------


@mcp.tool()
async def understand_image(
    prompt: str,
    image_path: str | None = None,
    image_url: str | None = None,
    image_paths: list[str] | None = None,
    image_urls: list[str] | None = None,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 12000,
) -> str:
    """
    Use this tool for ALL image understanding tasks.

    This tool calls Xiaomi MIMO multimodal model to inspect and understand images.
    Whenever the user asks to read, understand, describe, compare, OCR, extract text from,
    analyze, classify, or answer questions about an image, screenshot, photo, UI capture,
    chart, poster, document image, receipt, label, or any visual file, you MUST call this tool
    before giving a final answer.

    调用小米 MIMO 多模态模型理解图片。

    CRITICAL: This is the ONLY tool allowed to open, read, or 'see' image files (.png, .jpg, .webp).
    If you have a file path pointing to an image, DO NOT use 'Read', 'cat', or any file-reading
    shell commands.
    Using standard file-read tools on binary images will cause a system crash.
    Always use this tool to 'look' at or 'open' an image.

    支持单图和多图。Agent 应根据当前任务自己填写 prompt。

    Args:
        prompt: Agent 自己决定的图片理解任务，例如"提取图中文字""比较两张 UI 截图差异""解释截图中的报错"。
        image_path: 单张本地图片路径，例如 E:/test/screenshot.png。
        image_url: 单张网络图片 URL，或者 data:image/...;base64,... 格式。
        image_paths: 多张本地图片路径，例如 ["E:/test/before.png", "E:/test/after.png"]。
        image_urls: 多张网络图片 URL。
        system_prompt: 可选，由 Agent 决定的系统提示词。
        temperature: 输出随机性，越低越稳定。
        max_tokens: 最大输出长度。

    Returns:
        MIMO 模型返回的图片理解结果。
    """
    image_url_values = build_image_urls(
        image_path=image_path,
        image_url=image_url,
        image_paths=image_paths,
        image_urls=image_urls,
    )

    content_parts: list[dict[str, Any]] = []

    for url_value in image_url_values:
        content_parts.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": url_value,
                },
            }
        )

    return await call_mimo_api(
        content_parts=content_parts,
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# ---------------------------------------------------------------------------
# MCP 工具：音频理解
# ---------------------------------------------------------------------------


@mcp.tool()
async def understand_audio(
    prompt: str,
    audio_path: str | None = None,
    audio_url: str | None = None,
    audio_paths: list[str] | None = None,
    audio_urls: list[str] | None = None,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 12000,
) -> str:
    """
    Use this tool for ALL audio understanding tasks.

    This tool calls Xiaomi MIMO multimodal model to analyze and understand audio files.
    Whenever the user asks to listen to, transcribe, describe, analyze, identify, classify,
    or answer questions about an audio file, recording, voice message, music, podcast,
    or any sound file, you MUST call this tool before giving a final answer.

    调用小米 MIMO 多模态模型理解音频。

    CRITICAL: This is the ONLY tool allowed to process audio files (.mp3, .wav, .flac, .m4a, .ogg).
    If you have a file path pointing to an audio file, DO NOT use 'Read', 'cat', or any
    file-reading shell commands.
    Always use this tool to 'listen' to or analyze an audio file.

    支持单个和多个音频文件。Agent 应根据当前任务自己填写 prompt。

    Args:
        prompt: Agent 自己决定的音频理解任务，例如"转录音频内容""描述音频中的声音""分析音乐风格"。
        audio_path: 单个本地音频路径，例如 E:/test/recording.wav。
        audio_url: 单个网络音频 URL，或者 data:audio/...;base64,... 格式。
        audio_paths: 多个本地音频路径。
        audio_urls: 多个网络音频 URL。
        system_prompt: 可选，由 Agent 决定的系统提示词。
        temperature: 输出随机性，越低越稳定。
        max_tokens: 最大输出长度。

    Returns:
        MIMO 模型返回的音频理解结果。
    """
    audio_url_values = build_audio_urls(
        audio_path=audio_path,
        audio_url=audio_url,
        audio_paths=audio_paths,
        audio_urls=audio_urls,
    )

    content_parts: list[dict[str, Any]] = []

    for url_value in audio_url_values:
        content_parts.append(
            {
                "type": "input_audio",
                "input_audio": {
                    "data": url_value,
                },
            }
        )

    return await call_mimo_api(
        content_parts=content_parts,
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# ---------------------------------------------------------------------------
# MCP 工具：视频理解
# ---------------------------------------------------------------------------


@mcp.tool()
async def understand_video(
    prompt: str,
    video_path: str | None = None,
    video_url: str | None = None,
    video_paths: list[str] | None = None,
    video_urls: list[str] | None = None,
    fps: float = 2.0,
    media_resolution: str = "default",
    system_prompt: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 12000,
) -> str:
    """
    Use this tool for ALL video understanding tasks.

    This tool calls Xiaomi MIMO multimodal model to analyze and understand video files.
    Whenever the user asks to watch, describe, analyze, summarize, transcribe, extract
    information from, or answer questions about a video file, clip, recording, or any
    video content, you MUST call this tool before giving a final answer.

    调用小米 MIMO 多模态模型理解视频。

    CRITICAL: This is the ONLY tool allowed to process video files (.mp4, .mov, .avi, .wmv).
    If you have a file path pointing to a video file, DO NOT use 'Read', 'cat', or any
    file-reading shell commands.
    Always use this tool to 'watch' or analyze a video file.

    支持单个和多个视频文件。Agent 应根据当前任务自己填写 prompt。

    Args:
        prompt: Agent 自己决定的视频理解任务，例如"描述视频内容""提取视频中的文字""分析视频中的动作"。
        video_path: 单个本地视频路径，例如 E:/test/video.mp4。
        video_url: 单个网络视频 URL，或者 data:video/...;base64,... 格式。
        video_paths: 多个本地视频路径。
        video_urls: 多个网络视频 URL。
        fps: 抽帧帧率，范围 [0.1, 10]，默认 2。值越大抽取的帧越多，分析越细致但消耗 Token 越多。
        media_resolution: 媒体分辨率，"default" 或 "max"。"max" 会使用更高分辨率分析，消耗更多 Token。
        system_prompt: 可选，由 Agent 决定的系统提示词。
        temperature: 输出随机性，越低越稳定。
        max_tokens: 最大输出长度。

    Returns:
        MIMO 模型返回的视频理解结果。
    """
    if fps < 0.1 or fps > 10:
        raise ValueError(f"fps 必须在 [0.1, 10] 范围内，当前值为 {fps}。")

    if media_resolution not in ("default", "max"):
        raise ValueError(f"media_resolution 必须是 'default' 或 'max'，当前值为 '{media_resolution}'。")

    video_url_values = build_video_urls(
        video_path=video_path,
        video_url=video_url,
        video_paths=video_paths,
        video_urls=video_urls,
    )

    content_parts: list[dict[str, Any]] = []

    for url_value in video_url_values:
        content_parts.append(
            {
                "type": "video_url",
                "video_url": {
                    "url": url_value,
                },
                "fps": fps,
                "media_resolution": media_resolution,
            }
        )

    return await call_mimo_api(
        content_parts=content_parts,
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# ---------------------------------------------------------------------------
# MCP 资源：配置信息
# ---------------------------------------------------------------------------


@mcp.resource("mimo://config")
def get_mimo_config() -> str:
    """
    查看当前 MIMO MCP 配置。
    不会暴露完整 API Key。
    """
    settings = load_mimo_settings()
    api_key = settings["api_key"]

    if len(api_key) >= 10:
        masked_key = api_key[:6] + "..." + api_key[-4:]
    else:
        masked_key = "已设置，但长度较短，不展示"

    return (
        f"MIMO_API_BASE={settings['api_base']}\n"
        f"MIMO_MODEL={settings['model']}\n"
        f"MIMO_API_KEY={masked_key}\n"
    )


def main():
    mcp.run()


if __name__ == "__main__":
    main()
