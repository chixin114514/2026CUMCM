#!/usr/bin/env bash
# A题敏感度分析：本地生成 → 同步到远程服务端运行 → 回传结果。
#
# 远程默认使用项目历史工作流中的高性能 CPU 节点：
#   root@192.168.188.3:7999  (Ubuntu 22.04 / WSL2, 12 vCPU, 24G)
#
# 用法：
#   ./run_sensitivity.sh                 # 同步→远程后台运行全部4题→回传
#   TASKS="1 2" ./run_sensitivity.sh     # 只跑问题一、二
#   JOBS=8 ./run_sensitivity.sh          # 远程并行 8 个进程
#   ./run_sensitivity.sh sync-up         # 只上传
#   ./run_sensitivity.sh run             # 只远程后台运行并等待
#   ./run_sensitivity.sh sync-down       # 只回传
#   LOCAL=1 ./run_sensitivity.sh run     # 在本机运行（不连远程）
#
# 每次扰动结果自动命名并保存在：
#   solution/sensitivity/results/taskN-<参数>-<取值>.csv
#   汇总：solution/sensitivity/results/sensitivity_summary.csv
# 远程日志：solution/sensitivity/logs/taskN-... .log 及 remote_run_*.log

set -uo pipefail

REMOTE_HOST="${REMOTE_HOST:-root@192.168.188.3}"
REMOTE_PORT="${REMOTE_PORT:-7999}"
REMOTE_DIR="${REMOTE_DIR:-/root/2026CUMCM_sensitivity}"
TASKS="${TASKS:-1 2 3 4}"
JOBS="${JOBS:-4}"
LOCAL="${LOCAL:-0}"
PYTHON="${PYTHON:-python3}"
POLL_INTERVAL="${POLL_INTERVAL:-15}"

LOCAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE_RESULTS="solution/sensitivity/results"
LOCAL_RESULTS="$LOCAL_ROOT/solution/sensitivity/results"
LOG_DIR="$LOCAL_ROOT/solution/sensitivity/logs"

SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=10 -p "$REMOTE_PORT")
RSYNC_SSH="ssh -o BatchMode=yes -p $REMOTE_PORT"

FILES=(
  solution/sensitivity/run_sensitivity.py
  solution/sensitivity/remote_run.sh
  solution/task1/script/solve_task1.py
  solution/task2/script/solve_task2.py
  solution/task3/script/solve_task3.py
  solution/task4/script/solve_task4.py
  problem/附件/附件1.xlsx
  problem/附件/附件2.xlsx
  problem/附件/附件3/result1.xlsx
  problem/附件/附件3/result2.xlsx
  problem/附件/附件3/result3.xlsx
  problem/附件/附件3/result4.xlsx
)

log() { printf '\033[1;34m[sensitivity]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[sensitivity] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

remote_cmd() { ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "$@"; }

sync_up() {
  log "创建远程目录 $REMOTE_DIR"
  remote_cmd "mkdir -p '$REMOTE_DIR' '$REMOTE_DIR/$REMOTE_RESULTS'" || die "无法创建远程目录，检查 SSH 连接"
  log "上传求解器与附件到 $REMOTE_HOST:$REMOTE_DIR"
  ( cd "$LOCAL_ROOT" && rsync -avR -e "$RSYNC_SSH" "${FILES[@]}" "$REMOTE_HOST:$REMOTE_DIR/" ) || die "rsync 上传失败"
}

run_remote() {
  mkdir -p "$LOG_DIR" "$LOCAL_RESULTS"
  remote_cmd "mkdir -p '$REMOTE_DIR/$REMOTE_RESULTS'" || die "无法创建远程结果目录"
  local stamp remote_log
  stamp="$(date +%Y%m%d_%H%M%S)"
  remote_log="$REMOTE_DIR/$REMOTE_RESULTS/remote_run_$stamp.log"

  log "远程后台启动: TASKS='$TASKS' JOBS=$JOBS"
  remote_cmd "rm -f '$REMOTE_DIR/$REMOTE_RESULTS/run.done' '$REMOTE_DIR/$REMOTE_RESULTS/run.exit'; \
    nohup env TASKS='$TASKS' JOBS='$JOBS' OUT='$REMOTE_RESULTS' bash '$REMOTE_DIR/solution/sensitivity/remote_run.sh' > '$remote_log' 2>&1 & \
    echo \$! > '$REMOTE_DIR/$REMOTE_RESULTS/run.pid'; echo STARTED pid=\$(cat '$REMOTE_DIR/$REMOTE_RESULTS/run.pid')" || die "远程启动失败"

  log "等待远程计算完成（日志: $REMOTE_HOST:${remote_log}）"
  while true; do
    local state
    state="$(remote_cmd "if test -f '$REMOTE_DIR/$REMOTE_RESULTS/run.done'; then echo DONE; else echo RUNNING; fi" 2>/dev/null)"
    if [[ "$state" == "DONE" ]]; then
      break
    fi
    sleep "$POLL_INTERVAL"
  done

  local remote_tail exit_code
  remote_tail="$(remote_cmd "tail -n 15 '$remote_log'" 2>/dev/null || true)"
  printf '%s\n' "$remote_tail"
  exit_code="$(remote_cmd "cat '$REMOTE_DIR/$REMOTE_RESULTS/run.exit' 2>/dev/null || echo 1")"
  [[ "$exit_code" == "0" ]] || die "远程计算退出码 $exit_code（见 ${remote_log}）"
}

run_local() {
  mkdir -p "$LOG_DIR" "$LOCAL_RESULTS"
  local stamp
  stamp="$(date +%Y%m%d_%H%M%S)"
  log "本地运行: TASKS='$TASKS' JOBS=$JOBS"
  ( cd "$LOCAL_ROOT" && OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -u solution/sensitivity/run_sensitivity.py --tasks $TASKS --jobs "$JOBS" --out "$REMOTE_RESULTS" ) 2>&1 | tee "$LOG_DIR/run_$stamp.log"
  return "${PIPESTATUS[0]}"
}

sync_down() {
  mkdir -p "$LOCAL_RESULTS"
  if [[ "$LOCAL" == "1" ]]; then
    log "本地运行，结果已在 $LOCAL_RESULTS"
    return 0
  fi
  log "回传结果到 $LOCAL_RESULTS"
  rsync -avz -e "$RSYNC_SSH" "$REMOTE_HOST:$REMOTE_DIR/$REMOTE_RESULTS/" "$LOCAL_RESULTS/" || die "rsync 回传失败"
}

usage() {
  sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

case "${1:-all}" in
  sync-up) sync_up ;;
  run)
    [[ "$LOCAL" == "1" ]] && run_local || run_remote ;;
  sync-down) sync_down ;;
  all)
    if [[ "$LOCAL" == "1" ]]; then
      run_local || die "本地运行失败"
    else
      sync_up || die "上传失败"
      run_remote || die "远程运行失败"
      sync_down || die "回传失败"
    fi
    log "完成。查看 $LOCAL_RESULTS/sensitivity_summary.csv"
    ;;
  -h|--help|help) usage ;;
  *) die "未知子命令 '$1'（可用: all|sync-up|run|sync-down）" ;;
esac
