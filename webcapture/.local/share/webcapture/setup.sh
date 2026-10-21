#!/usr/bin/env bash
# 建 venv + 装 playwright/pillow + 检查系统浏览器
# 每台机器部署后跑一次即可；重复跑是安全的
set -euo pipefail

BASE="$(dirname "$(readlink -f "$0")")"
VENV="$HOME/.local/share/webcapture-venv"
TMPD="$HOME/.cache/webcapture-tmp"
mkdir -p "$TMPD"

echo "==> venv: $VENV"
[ -x "$VENV/bin/python3" ] || python3 -m venv "$VENV"

echo "==> 安装 playwright + pillow"
# /tmp 在有些机器上是小容量 tmpfs，必须把临时目录挪到磁盘
TMPDIR="$TMPD" "$VENV/bin/pip" install -q --upgrade pip
TMPDIR="$TMPD" "$VENV/bin/pip" install -q playwright pillow

"$VENV/bin/python3" -c "import playwright, PIL; print('    deps ok, pillow', PIL.__version__)"

echo "==> 检查系统浏览器（不下载 Playwright 自带 Chromium）"
found=""
for b in chromium chromium-browser google-chrome-stable google-chrome brave; do
  if command -v "$b" >/dev/null 2>&1; then
    echo "    $b -> $(command -v "$b")"
    found=1
  fi
done
if [ -z "$found" ]; then
  echo "    未找到 chromium/chrome。Arch 上装一个： sudo pacman -S chromium" >&2
  exit 2
fi

mkdir -p "$HOME/webcapture"
if [ ! -f "$HOME/webcapture/notify.conf" ] && [ -f "$BASE/notify.conf.example" ]; then
  cp "$BASE/notify.conf.example" "$HOME/webcapture/notify.conf"
  chmod 600 "$HOME/webcapture/notify.conf"
  echo "==> 已生成 ~/webcapture/notify.conf（填 webhook 才会发报警）"
fi

echo "==> 完成。试跑一轮： $BASE/shot.sh"
