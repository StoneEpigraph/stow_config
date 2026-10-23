#!/usr/bin/env bash
# 对固定 4 个网址整页截图 + 时间水印，失败时推送到钉钉/企业微信
# 由 systemd user timer (webcapture.timer) 每 15 分钟调用一次
#
# 首次部署：先跑一次 setup.sh 建 venv
set -uo pipefail

SELF=$(readlink -f "$0")
BASE=$(dirname "$SELF")
OUT="$HOME/webcapture"                    # 日志 / 状态 / 基线
IMG_OUT="$HOME/public/webcapture"         # 成品截图（经 Samba 对内网共享）
VENV_PY="$HOME/.local/share/webcapture-venv/bin/python3"

export TMPDIR="${TMPDIR:-$HOME/.cache/webcapture-tmp}"
export LANG="${LANG:-zh_CN.UTF-8}"
mkdir -p "$TMPDIR" "$OUT" "$IMG_OUT"

# 找一个真正装了 playwright + pillow 的解释器
pick_py() {
  local c
  for c in "$VENV_PY" \
           "$HOME/.workbuddy/binaries/python/envs/default/bin/python3" \
           "/usr/bin/python3"; do
    [ -x "$c" ] || continue
    if "$c" -c 'import playwright, PIL' >/dev/null 2>&1; then
      printf '%s' "$c"
      return 0
    fi
  done
  return 1
}

if ! PY=$(pick_py); then
  echo "[$(date '+%F %T')] 缺少 playwright/pillow，请先运行 $BASE/setup.sh" | tee -a "$OUT/run.out"
  exit 3
fi

# 同一时间只跑一个实例，避免上一次还没结束就叠加
exec 9>"$OUT/.lock"
flock -n 9 || { echo "[$(date '+%F %T')] 已有实例在跑，跳过本轮" >> "$OUT/run.out"; exit 0; }

# 等网络就绪（最多 60 秒）。user 实例里 After=network-online.target 是空实现，
# 开机/重启后立即补跑的那一轮常常还没连上网，容易一起超时误报。
wait_network() {
  local i
  for i in $(seq 1 20); do
    if command -v nmcli >/dev/null 2>&1; then
      [ "$(nmcli -t -f STATE general 2>/dev/null)" = "connected" ] && return 0
    elif command -v curl >/dev/null 2>&1; then
      curl -s -o /dev/null --max-time 3 http://www.gstatic.com/generate_204 2>/dev/null && return 0
    else
      ip route 2>/dev/null | grep -q '^default' && return 0
    fi
    sleep 3
  done
  return 0   # 等不到也继续，交给 capture.py 自己的重试
}
wait_network

echo "[$(date '+%F %T')] ---- run start ($PY) ----" >> "$OUT/run.out"
"$PY" -u "$BASE/capture.py" >> "$OUT/run.out" 2>&1
rc=$?

# 保留策略：RETENTION_DAYS>0 时清理过期截图（默认关闭，可用环境变量覆盖）
RETENTION_DAYS="${RETENTION_DAYS:-0}"
if [ "$RETENTION_DAYS" -gt 0 ]; then
  find "$OUT" "$IMG_OUT" -type f -name '*.png' -mtime +"$RETENTION_DAYS" -delete 2>/dev/null
fi

exit $rc
