#!/usr/bin/env bash
# 在远程服务端执行敏感度分析，并在结束时写出 run.done / run.exit 作为哨兵。
# 由 run_sensitivity.sh 通过 nohup 调用，环境变量：TASKS / JOBS / OUT。
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT" || exit 1

TASKS="${TASKS:-1 2 3 4}"
JOBS="${JOBS:-4}"
OUT="${OUT:-solution/sensitivity/results}"

export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT"
rm -f "$OUT/run.done" "$OUT/run.exit"

echo "[remote] root=$ROOT tasks='$TASKS' jobs=$JOBS out=$OUT"
python3 -u solution/sensitivity/run_sensitivity.py --tasks $TASKS --jobs "$JOBS" --out "$OUT"
code=$?
echo "$code" > "$OUT/run.exit"
touch "$OUT/run.done"
exit "$code"
