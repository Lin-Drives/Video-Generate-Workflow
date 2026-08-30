#!/bin/zsh
set -euo pipefail
ROOT="${0:A:h}"
OUT="$ROOT/outputs"
BUILD="$ROOT/work/build"
mkdir -p "$OUT" "$BUILD"
: "${SILICONFLOW_API_KEY:?未检测到 SILICONFLOW_API_KEY。请仅在当前终端执行：export SILICONFLOW_API_KEY='你的密钥'}"
if [[ "${GENERATE_IMAGES:-}" == "1" ]]; then
  echo "开始生成：已启用 Qwen-Image 分镜图"
else
  echo "开始生成：纯色背景模式"
fi
python3 "$ROOT/work/generate.py" "$ROOT" "$BUILD"
echo "正在合并片段、写入字幕…"
ffmpeg -y -v error -f concat -safe 0 -i "$BUILD/concat.txt" -i "$BUILD/subtitles.srt" \
  -map 0:v -map 0:a -map 1:0 -c:v copy -c:a aac -c:s mov_text \
  -metadata:s:s:0 language=chi "$OUT/机器人冲刺的那几秒.mp4"
echo "正在验收输出文件…"
ffprobe -v error -show_entries format=duration:stream=codec_name,codec_type,width,height \
  -of default=noprint_wrappers=1 "$OUT/机器人冲刺的那几秒.mp4" | tee "$OUT/验收信息.txt"
echo "Created: $OUT/机器人冲刺的那几秒.mp4"
