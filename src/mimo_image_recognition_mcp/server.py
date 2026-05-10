import base64
import mimetypes
import os
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("mimo-image-recognition")


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


def guess_mime_type(image_path: Path) -> str:
    """
    根据文件后缀推断图片 MIME 类型。
    """
    mime_type, _ = mimetypes.guess_type(str(image_path))

    if mime_type is None:
        suffix = image_path.suffix.lower()

        if suffix in [".jpg", ".jpeg"]:
            return "image/jpeg"

        if suffix == ".png":
            return "image/png"

        if suffix == ".webp":
            return "image/webp"

        if suffix == ".gif":
            return "image/gif"

        raise ValueError(
            f"无法识别图片类型：{image_path.suffix}。"
            "请使用 jpg、jpeg、png、webp 或 gif 图片。"
        )

    if not mime_type.startswith("image/"):
        raise ValueError(f"文件不是图片类型：{mime_type}")

    return mime_type


def local_image_to_data_url(image_path: str) -> str:
    """
    把本地图片转成 data:image/...;base64,... 格式。
    """
    path = Path(image_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"图片不存在：{path}")

    if not path.is_file():
        raise ValueError(f"路径不是文件：{path}")

    max_size_mb = 20
    file_size_mb = path.stat().st_size / 1024 / 1024

    if file_size_mb > max_size_mb:
        raise ValueError(
            f"图片过大：{file_size_mb:.2f} MB。"
            f"当前工具限制为 {max_size_mb} MB 以内。"
        )

    mime_type = guess_mime_type(path)

    with path.open("rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def validate_image_url(image_url: str) -> str:
    """
    校验网络图片 URL 或 data:image Base64 URL。
    """
    if not (
        image_url.startswith("http://")
        or image_url.startswith("https://")
        or image_url.startswith("data:image/")
    ):
        raise ValueError(
            "image_url 必须是 http、https 或 data:image/...;base64,... 格式。"
        )

    return image_url


def build_image_urls(
    image_path: str | None = None,
    image_url: str | None = None,
    image_paths: list[str] | None = None,
    image_urls: list[str] | None = None,
) -> list[str]:
    """
    构建图片 URL 列表。

    支持：
    1. image_path: 单张本地图片
    2. image_url: 单张网络图片
    3. image_paths: 多张本地图片
    4. image_urls: 多张网络图片
    """
    result: list[str] = []

    if image_path:
        result.append(local_image_to_data_url(image_path))

    if image_paths:
        for path in image_paths:
            result.append(local_image_to_data_url(path))

    if image_url:
        result.append(validate_image_url(image_url))

    if image_urls:
        for url in image_urls:
            result.append(validate_image_url(url))

    if not result:
        raise ValueError(
            "必须至少传入一张图片："
            "image_path、image_url、image_paths 或 image_urls。"
        )

    max_images = 6

    if len(result) > max_images:
        raise ValueError(
            f"一次最多支持 {max_images} 张图片，当前传入了 {len(result)} 张。"
        )

    return result


async def call_mimo_image_api(
    *,
    image_url_values: list[str],
    prompt: str,
    system_prompt: str | None,
    temperature: float,
    max_tokens: int,
) -> str:
    """
    调用 MIMO 图片理解接口。

    API Key、请求地址、模型名来自 MCP 启动配置。
    prompt 和 system_prompt 由 Agent 调用工具时决定。
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

    content: list[dict[str, Any]] = []

    for image_url_value in image_url_values:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": image_url_value,
                },
            }
        )

    content.append(
        {
            "type": "text",
            "text": prompt,
        }
    )

    messages.append(
        {
            "role": "user",
            "content": content,
        }
    )

    payload: dict[str, Any] = {
        "model": settings["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "api-key": settings["api_key"],
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
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
    调用小米 MIMO 多模态模型理解图片。

    支持单图和多图。Agent 应根据当前任务自己填写 prompt。

    Args:
        prompt: Agent 自己决定的图片理解任务，例如“提取图中文字”“比较两张 UI 截图差异”“解释截图中的报错”。
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

    return await call_mimo_image_api(
        image_url_values=image_url_values,
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


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
