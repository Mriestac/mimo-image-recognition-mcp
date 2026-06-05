# MIMO Multimedia Recognition MCP

一个调用小米 MIMO 多模态模型进行**图片、音频、视频**理解的 MCP Server。

## 重要说明

本 MCP 的作用是在不中断 MIMO 2.5 Pro 主模型对话上下文的前提下，通过 MCP 工具调用 MIMO 2.5 模型单独完成多模态识别任务。

它不会让 MIMO 2.5 Pro 模型本身具备多模态理解能力；多模态理解由本 MCP 背后的 MIMO 2.5 模型完成，再把识别结果返回给主对话模型继续推理。

该 MCP 支持：

- **图片理解**：本地/网络图片识别、OCR、截图分析等
- **音频理解**：本地/网络音频转录、声音分析、音乐识别等
- **视频理解**：本地/网络视频内容分析、动作识别等
- Agent 自定义提示词
- API Key、请求地址、模型名称通过 MCP 启动配置传入
- 支持通过 PyPI / uvx 运行
- 支持本地源码运行

## 功能说明

本项目会向 MCP 客户端暴露三个工具：

### `understand_image`

用于调用 MIMO 多模态模型理解图片。

支持的输入方式：

- `image_path`: 单张本地图片路径
- `image_url`: 单张网络图片 URL 或 data:image Base64
- `image_paths`: 多张本地图片路径
- `image_urls`: 多张网络图片 URL
- `prompt`：由 Agent 自己决定的图片理解任务
- `system_prompt`：可选系统提示词
- `temperature`：输出随机性
- `max_tokens`：最大输出长度

支持格式：JPG、JPEG、PNG、WebP、GIF。单文件最大 20 MB，最多 6 张。

### `understand_audio`

用于调用 MIMO 多模态模型理解音频。

支持的输入方式：

- `audio_path`: 单个本地音频路径
- `audio_url`: 单个网络音频 URL 或 data:audio Base64
- `audio_paths`: 多个本地音频路径
- `audio_urls`: 多个网络音频 URL
- `prompt`：由 Agent 自己决定的音频理解任务
- `system_prompt`：可选系统提示词
- `temperature`：输出随机性
- `max_tokens`：最大输出长度

支持格式：MP3、WAV、FLAC、M4A、OGG。URL 方式最大 100 MB，Base64 方式最大 50 MB。

### `understand_video`

用于调用 MIMO 多模态模型理解视频。

支持的输入方式：

- `video_path`: 单个本地视频路径
- `video_url`: 单个网络视频 URL 或 data:video Base64
- `video_paths`: 多个本地视频路径
- `video_urls`: 多个网络视频 URL
- `fps`：抽帧帧率，范围 [0.1, 10]，默认 2
- `media_resolution`：媒体分辨率，"default" 或 "max"
- `prompt`：由 Agent 自己决定的视频理解任务
- `system_prompt`：可选系统提示词
- `temperature`：输出随机性
- `max_tokens`：最大输出长度

支持格式：MP4、MOV、AVI、WMV。URL 方式最大 300 MB，Base64 方式最大 50 MB。

### 建议写入 `CLAUDE.md`

为了让 Claude 在多模态识别任务中稳定调用本 MCP，建议在项目的 `CLAUDE.md` 中加入类似说明：

```markdown
进行图片识别、音频理解、视频分析任务时，只使用 mimo_image_recognition_mcp。
```

---

## 安装方式一：通过 PyPI / uvx 使用

如果你只是想使用这个 MCP，推荐使用这种方式。

MCP 配置示例：

```json
{
  "mcpServers": {
    "mimo-image-recognition": {
      "command": "uvx",
      "args": [
        "--refresh",
        "mimo-image-recognition-mcp"
      ],
      "env": {
        "MIMO_API_KEY": "用户自己的 API Key",
        "MIMO_API_BASE": "https://token-plan-cn.xiaomimimo.com/v1",
        "MIMO_MODEL": "mimo-v2.5"
      }
    }
  }
}
```

配置项说明：

| 配置项 | 说明 |
|---|---|
| `MIMO_API_KEY` | 你的 MIMO API Key |
| `MIMO_API_BASE` | MIMO API 请求地址，通常为 `https://api.xiaomimimo.com/v1`或`https://token-plan-cn.xiaomimimo.com/v1` |
| `MIMO_MODEL` | 要调用的 MIMO 模型名称，例如 `mimo-v2.5` |

### 网络代理提醒

使用本 MCP 调用 MIMO 接口时，建议不要开启代理。代理可能导致请求超时、连接失败，或影响媒体文件 URL 的访问稳定性。


---

## 安装方式二：本地源码运行

如果你想修改源码或参与开发，可以使用本地源码方式。

### 1. 克隆项目

```bash
git clone https://github.com/Mriestac/mimo-image-recognition-mcp.git
cd mimo-image-recognition-mcp
```


### 2. 安装依赖

```bash
uv sync
```

### 3. MCP 配置示例

```json
{
  "mcpServers": {
    "mimo-image-recognition": {
      "command": "uv",
      "args": [
        "--directory",
        "<你的项目路径>",
        "run",
        "mimo-image-recognition-mcp"
      ],
      "env": {
        "MIMO_API_KEY": "你的 MIMO API Key",
        "MIMO_API_BASE": "https://token-plan-cn.xiaomimimo.com/v1",
        "MIMO_MODEL": "mimo-v2.5"
      }
    }
  }
}
```

请把 `<你的项目路径>` 改成你自己本地项目的真实路径。

---



## 本地调试

可以使用 MCP Inspector 调试：

```bash
uv run mcp dev src/mimo_image_recognition_mcp/server.py
```

如果能看到：

```text
understand_image
understand_audio
understand_video
```

说明 MCP Server 启动成功。

如果你想在 MCP Inspector 中实际调用 MIMO 接口，可以在当前终端临时设置：

### Windows PowerShell

```powershell
$env:MIMO_API_KEY="你的 MIMO API Key"
$env:MIMO_API_BASE="https://api.xiaomimimo.com/v1"
$env:MIMO_MODEL="mimo-v2.5"

uv run mcp dev src/mimo_image_recognition_mcp/server.py
```

---

## API 文档参考

- [OpenAI API 兼容](https://platform.xiaomimimo.com/docs/zh-CN/api/chat/openai-api)
- [图片理解](https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/multimodal-understanding/image-understanding)
- [音频理解](https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/multimodal-understanding/audio-understanding)
- [视频理解](https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/multimodal-understanding/video-understanding)

## License

MIT
