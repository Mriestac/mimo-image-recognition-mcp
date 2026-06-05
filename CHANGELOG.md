# Changelog

本文档记录 MIMO Multimedia Recognition MCP 的所有重要变更。

## [0.2.0] - 2025-06-05

### ✨ 新增功能

- **音频理解** (`understand_audio`)：支持 MP3、WAV、FLAC、M4A、OGG 格式的音频分析
  - 支持本地文件路径、网络 URL、Base64 编码三种输入方式
  - URL 方式最大 100 MB，Base64 方式最大 50 MB
  - 支持同时传入多个音频文件

- **视频理解** (`understand_video`)：支持 MP4、MOV、AVI、WMV 格式的视频分析
  - 支持本地文件路径、网络 URL、Base64 编码三种输入方式
  - URL 方式最大 300 MB，Base64 方式最大 50 MB
  - 可调节抽帧帧率 (`fps`: 0.1-10) 和媒体分辨率 (`media_resolution`: default/max)
  - 支持同时传入多个视频文件

### 🔧 重构

- 提取通用的 MIME 类型推断函数 `_guess_mime_type()`
- 提取通用的本地文件转 Base64 函数 `_local_file_to_data_url()`
- 提取通用的 URL 校验函数 `_validate_url()`
- 提取通用的媒体 URL 列表构建函数 `_build_media_urls()`
- 提取通用的 API 调用函数 `call_mimo_api()`

### 🐛 修复

- 修复 API 参数名：`max_tokens` → `max_completion_tokens`（符合 MIMO API 规范）

### 📝 文档

- 重写 README，添加详细的安装配置步骤
- 添加 Claude Code、Claude Desktop、Cursor、VS Code、Cherry Studio 的配置示例
- 添加图片/音频/视频理解的详细使用指南和场景示例
- 添加工具参数详解表格
- 添加常见问题解答
- 添加 CHANGELOG.md

## [0.1.4] - Unreleased

### ✨ 初始版本

- 支持图片理解 (`understand_image`)
  - 支持 JPG、JPEG、PNG、WebP、GIF 格式
  - 支持本地文件路径、网络 URL、Base64 编码
  - 单文件最大 20 MB，最多 6 张
  - 支持自定义 system_prompt、temperature、max_tokens
- 支持 MCP 资源 (`mimo://config`) 查看当前配置
