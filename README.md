# 机器人工程解读视频 MVP

本地生成中文横版 YouTube 视频：口播稿/分镜 → 硅基流动 CosyVoice2 TTS → 字幕 → 图解卡片 → MP4。

## 使用

```bash
export SILICONFLOW_API_KEY='你的密钥'   # 只在当前终端会话中设置，不写入项目
./render.sh
```

产物在 `outputs/`：视频、SRT 字幕、封面 SVG、标题草案和事实核验说明。

没有 API 密钥时脚本会停止在配音步骤，避免误把占位音频当成成片。密钥由硅基流动控制台创建；不要写入项目文件或提交到版本控制。

## 启用 Qwen-Image 分镜图

默认使用纯色背景，不产生图片生成费用。确认要为 9 个分镜生成并下载 16:9 图片时，在同一终端执行：

```bash
GENERATE_IMAGES=1 ./render.sh
```

脚本使用 `Qwen/Qwen-Image`，并会立即下载接口返回的图片，避免临时 URL 过期。
