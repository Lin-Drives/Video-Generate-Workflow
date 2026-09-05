#!/bin/zsh
set -euo pipefail
ROOT="${0:A:h}"
OUT="$ROOT/outputs"
BUILD="$ROOT/work/build"
OUTPUT_BASENAME="${OUTPUT_BASENAME:-机器人怎么看见世界}"
IMAGE_PROVIDER="${IMAGE_PROVIDER:-gpt}"
mkdir -p "$OUT" "$BUILD"
if [[ "${REUSE_AUDIO:-}" != "1" || ( "${GENERATE_IMAGES:-}" == "1" && "$IMAGE_PROVIDER" == "qwen" ) ]]; then
  : "${SILICONFLOW_API_KEY:?未检测到 SILICONFLOW_API_KEY。请仅在当前终端执行：export SILICONFLOW_API_KEY='你的密钥'}"
fi
if [[ "${GENERATE_IMAGES:-}" == "1" && "$IMAGE_PROVIDER" == "qwen" ]]; then
  echo "开始生成：已启用 Qwen-Image 分镜图"
elif [[ "${GENERATE_IMAGES:-}" == "1" ]]; then
  echo "开始生成：GPT 为主配置，请先生成并审核 GPT 分镜图后使用 USE_EXISTING_IMAGES=1"
elif [[ "${USE_EXISTING_IMAGES:-}" == "1" ]]; then
  echo "开始生成：复用 GPT 主分镜图"
else
  echo "开始生成：纯色背景模式"
fi
if [[ -n "${IMAGE_SCENES:-}" ]]; then
  echo "仅重新生成分镜图：${IMAGE_SCENES}"
fi
python3 "$ROOT/work/generate.py" "$ROOT" "$BUILD"
echo "正在合并片段，并导出兼容 IINA 的外挂字幕…"
cp "$BUILD/subtitles.srt" "$OUT/${OUTPUT_BASENAME}.srt"
ffmpeg -y -v error -f concat -safe 0 -i "$BUILD/concat.txt" \
  -map 0:v -map 0:a -c:v copy -c:a aac "$OUT/${OUTPUT_BASENAME}.mp4"
echo "正在验收输出文件…"
ffprobe -v error -show_entries format=duration:stream=codec_name,codec_type,width,height \
  -of default=noprint_wrappers=1 "$OUT/${OUTPUT_BASENAME}.mp4" | tee "$OUT/验收信息.txt"
echo "Created: $OUT/${OUTPUT_BASENAME}.mp4"
