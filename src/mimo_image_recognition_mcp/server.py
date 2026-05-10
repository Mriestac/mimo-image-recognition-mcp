import base64
import mimetypes
import os
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("mimo-image-recognition")


def load_mimo_settings() -> dict[str, str]:
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
    api_base = api_base.rstrip("/")

    if api_base.endswith("/chat/completions"):
        return api_base

    return f"{api_base}/chat/completions"


def guess_mime_type(image_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(image_path))

    if mime_type is None:
        suffix = image_path.suffix.lower()

        if suffix in [".jpg", ".jpeg"]:
            return "image/jpeg"

        if suffix == ".png":
            return "image/png"

        if suffix == ".webp":
            return "image/webp"

        raise ValueError(
            f"无法识别图片类型：{image_path.suffix}。"
            "请使用 jpg、jpeg、png 或 webp 图片。"
        )

    if not mime_type.startswith("image/"):
        raise ValueError(f"文件不是图片类型：{mime_type}")

    return mime_type


def local_image_to_data_url(image_path: str) -> str:
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


def build_image_url(
    image_path: str | None,
    image_url: str | None,
) -> str:
    if image_path and image_url:
        raise ValueError("image_path 和 image_url 只能传入一个，不能同时传。")

    if not image_path and not image_url:
        raise ValueError("必须传入 image_path 或 image_url。")

    if image_url:
        if not (
            image_url.startswith("http://")
            or image_url.startswith("https://")
            or image_url.startswith("data:image/")
        ):
            raise ValueError(
                "image_url 必须是 http、https 或 data:image/...;base64,... 格式。"
            )

        return image_url

    assert image_path is not None
    return local_image_to_data_url(image_path)


async def call_mimo_image_api(
    *,
    image_url_value: str,
    prompt: str,
    system_prompt: str | None,
    temperature: float,
    max_tokens: int,
) -> str:
    settings = load_mimo_settings()

    endpoint = build_chat_completions_url(settings["api_base"])

    messages: list[dict[str, Any]] = []

    if system_prompt:
        messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url_value,
                    },
                },
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
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

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            endpoint,
            headers=headers,
            json=payload,
        )

    if response.status_code >= 400:
        return (
            "MIMO API 调用失败。\n"
            f"HTTP 状态码：{response.status_code}\n"
            f"请求地址：{endpoint}\n"
            f"模型名称：{settings['model']}\n"
            f"响应内容：{response.text}"
        )

    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return f"MIMO API 返回了非预期格式：\n{data}"


@mcp.tool()
async def understand_image(
    prompt: str,
    image_path: str | None = None,
    image_url: str | None = None,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 1200,
) -> str:
    """
    调用小米 MIMO 多模态模型理解图片。

    Args:
        prompt: Agent 自己决定的图片理解任务。
        image_path: 本地图片路径，例如 E:/test/screenshot.png。
        image_url: 网络图片 URL，或者 data:image/...;base64,... 格式。
        system_prompt: 可选，由 Agent 决定的系统提示词。
        temperature: 输出随机性，越低越稳定。
        max_tokens: 最大输出长度。

    Returns:
        MIMO 模型返回的图片理解结果。
    """
    image_url_value = build_image_url(
        image_path=image_path,
        image_url=image_url,
    )

    return await call_mimo_image_api(
        image_url_value=image_url_value,
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


@mcp.resource("mimo://config")
def get_mimo_config() -> str:
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