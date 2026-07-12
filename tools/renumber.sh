#!/usr/bin/env bash
# Full "renumber" run: rebuild every derived artifact from the raw CSVs after a
# code change (see the defense handbook, section 6). Stamp-based resume: each
# completed step drops a flag under .renumber_stamps/, so re-running this script
# after an interruption continues instead of restarting (the individual tools
# also checkpoint internally).
#
# ONE-TIME preparation (NOT done here, so a resume never deletes fresh work):
#   rm models/*.joblib
#   rm reports/tables/{model_metrics,cv_metrics,cv_summary,imbalance_comparison,tuning_results}.csv
#   rm -r reports/tables/_xai_cache reports/tables/_thr_cache
#
# Usage:  bash tools/renumber.sh [python_exe]
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${1:-python}"
STAMPS=.renumber_stamps
mkdir -p "$STAMPS"

step() { # step <name> <command...>
  local name=$1; shift
  if [ -f "$STAMPS/$name" ]; then
    echo "== skip (stamped): $name"
    return 0
  fi
  echo "== [$(date +%H:%M:%S)] $name: $*"
  "$@"
  touch "$STAMPS/$name"
}

step 00_verify_raw   "$PY" setup_raw_data.py
step 01_master       "$PY" -m src.data.build_master_table
step 02_checkpoints  "$PY" -m src.data.make_checkpoints --force
step 03_split        "$PY" -m src.evaluation.make_split --materialise
step 04_eda          "$PY" -m src.eda.eda
step 05_tests        "$PY" -m pytest tests/ -q
step 06_train        "$PY" -m src.modeling.train
step 07_cv           "$PY" -m src.modeling.train --cv
step 08_stat_tests   "$PY" -m src.evaluation.stat_tests
step 09_task4_figs   "$PY" -m tools.make_task4_figures
step 10_imbalance    "$PY" -m tools.make_imbalance_comparison
step 11_eval_extras  "$PY" -m tools.make_eval_analysis
step 12_thr_valid    "$PY" -m tools.make_threshold_validation
step 13_xai          "$PY" -m tools.make_xai_analysis --lime-n 100
step 14_xai_strat    "$PY" -m tools.make_xai_by_strategy
step 15_fairness     "$PY" -m tools.make_fairness_report
step 16_sens_xgb     "$PY" -m tools.sensitivity_active --model xgb --plot
step 17_sens_lgbm    "$PY" -m tools.sensitivity_active --model lgbm --plot
step 18_tuning       "$PY" -m tools.tune_models
step 19_deck         "$PY" tools/build_revealjs_report.py
step 20_docx         "$PY" tools/build_docx.py
step 21_final_report "$PY" -m tools.build_final_report
step 22_final_slides "$PY" -m tools.build_final_slides

echo "== [$(date +%H:%M:%S)] RENUMBER COMPLETE — remove $STAMPS/ before the next full run."
