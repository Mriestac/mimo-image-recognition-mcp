# MIMO Multimedia Recognition MCP

一个调用小米 MIMO 多模态模型进行**图片、音频、视频**理解的 MCP Server。

## 工作原理

本 MCP 的作用是在不中断 MIMO 2.5 Pro 主模型对话上下文的前提下，通过 MCP 工具调用 MIMO 2.5 模型单独完成多模态识别任务。

```
用户提问（含图片/音频/视频）
       ↓
MIMO 2.5 Pro（主对话模型，纯文本）
       ↓ 通过 MCP 工具调用
本 MCP Server
       ↓ 调用 OpenAI 兼容 API
MIMO 2.5（多模态模型）
       ↓ 返回识别结果
MIMO 2.5 Pro 继续推理并回答用户
```

它不会让 MIMO 2.5 Pro 模型本身具备多模态理解能力；多模态理解由本 MCP 背后的 MIMO 2.5 模型完成，再把识别结果返回给主对话模型继续推理。

---

## 支持的功能

| 工具 | 功能 | 支持格式 | 输入方式 | 限制 |
|------|------|---------|---------|------|
| `understand_image` | 图片理解、OCR、截图分析 | JPG/JPEG/PNG/WebP/GIF | 本地路径 / 网络URL / Base64 | 单文件 ≤20MB，最多 6 张 |
| `understand_audio` | 音频转录、声音分析 | MP3/WAV/FLAC/M4A/OGG | 本地路径 / 网络URL / Base64 | 本地 ≤50MB，URL ≤100MB |
| `understand_video` | 视频内容分析、动作识别 | MP4/MOV/AVI/WMV | 本地路径 / 网络URL / Base64 | 本地 ≤50MB，URL ≤300MB |

---

## 快速开始（3 分钟完成配置）

### 第一步：获取 API Key

1. 访问 [Xiaomi MiMo 开放平台](https://platform.xiaomimimo.com/)
2. 注册并登录
3. 进入控制台，创建 API Key

### 第二步：选择安装方式

#### 方式一：通过 PyPI / uvx 使用（推荐）

无需克隆代码，直接配置即可。

**前提条件**：已安装 [uv](https://docs.astral.sh/uv/)（Python 包管理工具）。

```bash
# Windows
pip install uv

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 方式二：本地源码运行

适合需要修改源码或参与开发的用户。

```bash
git clone https://github.com/Mriestac/mimo-image-recognition-mcp.git
cd mimo-image-recognition-mcp
uv sync
```

### 第三步：配置 MCP

根据你使用的 AI 工具，选择对应的配置方式。

#### Claude Code 配置

在终端运行以下命令，或手动编辑 `~/.claude/settings.json`：

```bash
claude mcp add mimo-multimedia-recognition \
  -- uvx --refresh mimo-image-recognition-mcp
```

然后在弹出的配置中添加环境变量，或手动编辑配置文件：

```json
{
  "mcpServers": {
    "mimo-multimedia-recognition": {
      "command": "uvx",
      "args": ["--refresh", "mimo-image-recognition-mcp"],
      "env": {
        "MIMO_API_KEY": "你的 MIMO API Key",
        "MIMO_API_BASE": "https://token-plan-cn.xiaomimimo.com/v1",
        "MIMO_MODEL": "mimo-v2.5"
      }
    }
  }
}
```

> **本地源码运行**时，将 `command` 和 `args` 改为：
> ```json
> {
>   "command": "uv",
>   "args": ["--directory", "你的项目路径", "run", "mimo-image-recognition-mcp"]
> }
> ```

#### Claude Desktop 配置

编辑 `~/.claude/claude_desktop_config.json`（macOS）或 `%APPDATA%\Claude\claude_desktop_config.json`（Windows）：

```json
{
  "mcpServers": {
    "mimo-multimedia-recognition": {
      "command": "uvx",
      "args": ["--refresh", "mimo-image-recognition-mcp"],
      "env": {
        "MIMO_API_KEY": "你的 MIMO API Key",
        "MIMO_API_BASE": "https://token-plan-cn.xiaomimimo.com/v1",
        "MIMO_MODEL": "mimo-v2.5"
      }
    }
  }
}
```

#### Cursor / VS Code 配置

在项目根目录创建 `.cursor/mcp.json` 或 `.vscode/mcp.json`：

```json
{
  "mcpServers": {
    "mimo-multimedia-recognition": {
      "command": "uvx",
      "args": ["--refresh", "mimo-image-recognition-mcp"],
      "env": {
        "MIMO_API_KEY": "你的 MIMO API Key",
        "MIMO_API_BASE": "https://token-plan-cn.xiaomimimo.com/v1",
        "MIMO_MODEL": "mimo-v2.5"
      }
    }
  }
}
```

#### Cherry Studio 配置

在 Cherry Studio 的 MCP 设置中添加：

- **名称**：`mimo-multimedia-recognition`
- **命令**：`uvx`
- **参数**：`--refresh` `mimo-image-recognition-mcp`
- **环境变量**：
  - `MIMO_API_KEY` = `你的 MIMO API Key`
  - `MIMO_API_BASE` = `https://token-plan-cn.xiaomimimo.com/v1`
  - `MIMO_MODEL` = `mimo-v2.5`

### 第四步：验证配置

配置完成后，重启 AI 工具。在对话中尝试：

> "帮我看看这张图片里有什么"（附带一张图片）

如果 AI 调用了 `understand_image` 工具并返回了图片描述，说明配置成功。

---

## 配置项说明

| 配置项 | 必填 | 说明 |
|---|---|---|
| `MIMO_API_KEY` | ✅ | 你的 MIMO API Key，在 [控制台](https://platform.xiaomimimo.com/console) 创建 |
| `MIMO_API_BASE` | ✅ | MIMO API 请求地址（见下方说明） |
| `MIMO_MODEL` | ✅ | 要调用的模型名称，推荐 `mimo-v2.5` |

### API 请求地址选择

| 地址 | 说明 |
|---|---|
| `https://api.xiaomimimo.com/v1` | 官方默认地址 |
| `https://token-plan-cn.xiaomimimo.com/v1` | Token Plan 国内地址 |
| `https://token-plan-sgp.xiaomimimo.com/v1` | Token Plan 新加坡地址 |

> 请根据你的账号类型和网络环境选择合适的地址。如果一个地址不通，尝试其他地址。

### 可用模型

| 模型 | 说明 |
|---|---|
| `mimo-v2.5` | 推荐，支持图片/音频/视频理解 |
| `mimo-v2-omni` | 支持图片/音频/视频理解 |

---

## 详细使用指南

### 一、图片理解 (`understand_image`)

#### 场景 1：识别网络图片

直接让 AI 分析一张网络图片：

> "帮我看看这张图片里有什么：https://example.com/photo.jpg"

AI 会自动调用 `understand_image` 工具，内部执行：

```json
{
  "prompt": "描述这张图片的内容",
  "image_url": "https://example.com/photo.jpg"
}
```

#### 场景 2：识别本地图片

让 AI 分析本地文件：

> "帮我看看 E:/screenshots/error.png 这张截图里的报错信息"

AI 会自动调用：

```json
{
  "prompt": "提取截图中的报错信息",
  "image_path": "E:/screenshots/error.png"
}
```

#### 场景 3：比较多张图片

> "对比这两张 UI 截图的差异：E:/before.png 和 E:/after.png"

AI 会自动调用：

```json
{
  "prompt": "比较这两张 UI 截图的差异",
  "image_paths": ["E:/before.png", "E:/after.png"]
}
```

#### 场景 4：OCR 文字提取

> "帮我提取这张发票图片里的所有文字：https://example.com/invoice.jpg"

---

### 二、音频理解 (`understand_audio`)

#### 场景 1：转录音频内容

> "帮我转录这段音频的内容：https://example.com/recording.wav"

AI 会自动调用 `understand_audio` 工具，内部执行：

```json
{
  "prompt": "转录这段音频的内容",
  "audio_url": "https://example.com/recording.wav"
}
```

#### 场景 2：分析本地音频

> "帮我听听 E:/recordings/meeting.mp3 里说了什么"

AI 会自动调用：

```json
{
  "prompt": "描述这段音频的内容",
  "audio_path": "E:/recordings/meeting.mp3"
}
```

#### 场景 3：识别音乐

> "这段音频是什么风格的音乐？https://example.com/music.flac"

---

### 三、视频理解 (`understand_video`)

#### 场景 1：描述视频内容

> "帮我描述一下这个视频的内容：https://example.com/clip.mp4"

AI 会自动调用 `understand_video` 工具，内部执行：

```json
{
  "prompt": "描述这段视频的内容",
  "video_url": "https://example.com/clip.mp4",
  "fps": 2,
  "media_resolution": "default"
}
```

#### 场景 2：分析本地视频

> "帮我分析 E:/videos/demo.mp4 里演示的操作步骤"

AI 会自动调用：

```json
{
  "prompt": "分析视频中演示的操作步骤",
  "video_path": "E:/videos/demo.mp4"
}
```

#### 场景 3：高精度视频分析

对于需要更细致分析的场景，可以使用更高帧率和分辨率：

> "仔细分析这个视频中人物的每个动作，视频在 E:/sports/training.mp4"

AI 会使用 `fps=5, media_resolution="max"` 进行更精细的分析。

---

## 工具参数详解

### `understand_image`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `prompt` | string | ✅ | - | 图片理解任务描述 |
| `image_path` | string | - | - | 单张本地图片路径 |
| `image_url` | string | - | - | 单张网络图片 URL 或 data:image Base64 |
| `image_paths` | list[string] | - | - | 多张本地图片路径 |
| `image_urls` | list[string] | - | - | 多张网络图片 URL |
| `system_prompt` | string | - | - | 可选系统提示词 |
| `temperature` | float | - | 0.2 | 输出随机性，越低越稳定 |
| `max_tokens` | int | - | 12000 | 最大输出长度 |

### `understand_audio`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `prompt` | string | ✅ | - | 音频理解任务描述 |
| `audio_path` | string | - | - | 单个本地音频路径 |
| `audio_url` | string | - | - | 单个网络音频 URL 或 data:audio Base64 |
| `audio_paths` | list[string] | - | - | 多个本地音频路径 |
| `audio_urls` | list[string] | - | - | 多个网络音频 URL |
| `system_prompt` | string | - | - | 可选系统提示词 |
| `temperature` | float | - | 0.2 | 输出随机性，越低越稳定 |
| `max_tokens` | int | - | 12000 | 最大输出长度 |

### `understand_video`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `prompt` | string | ✅ | - | 视频理解任务描述 |
| `video_path` | string | - | - | 单个本地视频路径 |
| `video_url` | string | - | - | 单个网络视频 URL 或 data:video Base64 |
| `video_paths` | list[string] | - | - | 多个本地视频路径 |
| `video_urls` | list[string] | - | - | 多个网络视频 URL |
| `fps` | float | - | 2.0 | 抽帧帧率，范围 [0.1, 10] |
| `media_resolution` | string | - | "default" | 媒体分辨率，"default" 或 "max" |
| `system_prompt` | string | - | - | 可选系统提示词 |
| `temperature` | float | - | 0.2 | 输出随机性，越低越稳定 |
| `max_tokens` | int | - | 12000 | 最大输出长度 |

---

## 建议写入 `CLAUDE.md`

为了让 Claude 在多模态识别任务中稳定调用本 MCP，建议在项目的 `CLAUDE.md` 中加入：

```markdown
## 图片 & 音频 & 视频识别

进行图片识别、音频理解、视频分析任务时，只使用 mimo_image_recognition_mcp。
不要使用 Read 工具读取图片/音频/视频文件。
```

---

## 本地调试

### 使用 MCP Inspector

```bash
# 设置环境变量
export MIMO_API_KEY="你的 API Key"
export MIMO_API_BASE="https://api.xiaomimimo.com/v1"
export MIMO_MODEL="mimo-v2.5"

# 启动 Inspector
uv run mcp dev src/mimo_image_recognition_mcp/server.py
```

**Windows PowerShell**：

```powershell
$env:MIMO_API_KEY="你的 API Key"
$env:MIMO_API_BASE="https://api.xiaomimimo.com/v1"
$env:MIMO_MODEL="mimo-v2.5"

uv run mcp dev src/mimo_image_recognition_mcp/server.py
```

启动后如果能看到以下工具列表，说明 MCP Server 启动成功：

```text
understand_image
understand_audio
understand_video
```

### 使用 Python 直接测试

```python
import asyncio
import os

os.environ["MIMO_API_KEY"] = "你的 API Key"
os.environ["MIMO_API_BASE"] = "https://api.xiaomimimo.com/v1"
os.environ["MIMO_MODEL"] = "mimo-v2.5"

from mimo_image_recognition_mcp.server import understand_image, understand_audio, understand_video

async def main():
    # 测试图片理解
    result = await understand_image(
        prompt="描述这张图片的内容",
        image_url="https://example-files.cnbj1.mi-fds.com/example-files/image/image_example.png",
    )
    print("图片理解:", result)

    # 测试音频理解
    result = await understand_audio(
        prompt="转录这段音频的内容",
        audio_url="https://example-files.cnbj1.mi-fds.com/example-files/audio/audio_example.wav",
    )
    print("音频理解:", result)

    # 测试视频理解
    result = await understand_video(
        prompt="描述这段视频的内容",
        video_url="https://example-files.cnbj1.mi-fds.com/example-files/video/video_example.mp4",
    )
    print("视频理解:", result)

asyncio.run(main())
```

---

## 常见问题

### Q: 代理导致请求失败？

使用本 MCP 调用 MIMO 接口时，建议**不要开启代理**。代理可能导致请求超时、连接失败，或影响媒体文件 URL 的访问稳定性。

### Q: 本地文件路径怎么写？

- Windows：`E:/folder/file.png` 或 `E:\\folder\\file.png`
- macOS/Linux：`/home/user/file.png`

支持 `~` 展开，如 `~/Documents/audio.wav`。

### Q: 支持哪些模型？

目前支持 `mimo-v2.5` 和 `mimo-v2-omni`。推荐使用 `mimo-v2.5`。

### Q: 音频/视频有大小限制吗？

| 类型 | 本地文件 | URL 方式 |
|------|---------|---------|
| 图片 | ≤ 20 MB | 无限制 |
| 音频 | ≤ 50 MB | ≤ 100 MB |
| 视频 | ≤ 50 MB | ≤ 300 MB |

> 本地文件限制为原始文件大小。由于 Base64 编码会膨胀约 33%，本地文件限制比 URL 方式更严格以避免内存溢出。

### Q: 视频的 fps 和 media_resolution 怎么选？

- `fps=2`（默认）：适合一般场景，Token 消耗较少
- `fps=5`：适合需要捕捉快速动作的场景
- `fps=10`：最高精度，Token 消耗最大
- `media_resolution="default"`：默认分辨率，推荐
- `media_resolution="max"`：最高分辨率，适合需要看清细节的场景

---

## API 文档参考

- [OpenAI API 兼容](https://platform.xiaomimimo.com/docs/zh-CN/api/chat/openai-api)
- [图片理解](https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/multimodal-understanding/image-understanding)
- [音频理解](https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/multimodal-understanding/audio-understanding)
- [视频理解](https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/multimodal-understanding/video-understanding)

## 更新日志

### v0.2.0 (2025-06-05)

- ✨ 新增 `understand_audio` 工具：支持音频理解（MP3/WAV/FLAC/M4A/OGG）
- ✨ 新增 `understand_video` 工具：支持视频理解（MP4/MOV/AVI/WMV），可调节 fps 和分辨率
- 🔧 重构代码架构：提取通用的 MIME 推断、文件转换、URL 校验函数
- 🐛 修复 API 参数：`max_tokens` → `max_completion_tokens`
- 📝 完善文档：添加详细的调用步骤和使用示例

### v0.1.4

- 初始版本，支持图片理解

## License

MIT
