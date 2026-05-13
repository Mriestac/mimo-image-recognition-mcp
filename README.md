# MIMO Image Recognition MCP

一个调用小米 MIMO 多模态模型进行图片理解的 MCP Server。

该 MCP 支持：

- 本地图片路径识别
- 网络图片 URL 识别
- Agent 自定义提示词
- API Key、请求地址、模型名称通过 MCP 启动配置传入
- 支持通过 PyPI / uvx 运行
- 支持本地源码运行

## 功能说明

本项目会向 MCP 客户端暴露一个工具：

### `understand_image`

用于调用 MIMO 多模态模型理解图片。

支持的输入方式：

- `image_path`: 单张本地图片路径
- `image_url`: 单张网络图片 URL
- `image_paths`: 多张本地图片路径
- `image_urls`: 多张网络图片 URL
- `prompt`：由 Agent 自己决定的图片理解任务
- `system_prompt`：可选系统提示词
- `temperature`：输出随机性
- `max_tokens`：最大输出长度

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
        "E:/mimo-image-recognition",
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

请把：

```text
E:/mimo-image-recognition
```

改成你自己本地项目的真实路径。

---



## 本地调试

可以使用 MCP Inspector 调试：

```bash
uv run mcp dev src/mimo_image_recognition_mcp/server.py
```

如果能看到：

```text
understand_image
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


## License

MIT
