#!/bin/bash
# PythonAnywhere の更新用（DEPLOY.md 手順9）。
#
# 使い方:
#     bash ~/sealnote/scripts/pythonanywhere_update.sh
#     → そのあと Webタブの Reload を押す
#
# やること:
#   1. DBのバックアップを取る（マイグレーションで壊れたときの保険）
#   2. git pull
#   3. 依存の更新
#   4. マイグレーション
#
# 仮想環境をフルパスで呼ぶ。素の `flask` はシステム側のものが動いてしまい、
# ModuleNotFoundError: No module named 'flask_limiter' になる。
set -euo pipefail

PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$HOME/.virtualenvs/sealnote"
ENVFILE="$HOME/data/.env"
DB="$HOME/data/sealnote.db"

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

if [ ! -x "$VENV/bin/flask" ]; then
    echo "エラー: 仮想環境が見つかりません（$VENV）" >&2
    echo "  先に pythonanywhere_setup.sh を実行してください。" >&2
    exit 1
fi

# --- 1. バックアップ -----------------------------------------------------
say "1/4 バックアップ"
if [ -f "$DB" ]; then
    STAMP="$(date +%Y%m%d_%H%M%S)"
    cp "$DB" "$HOME/data/backup_$STAMP.db"
    echo "保存しました: ~/data/backup_$STAMP.db"
    # 古いバックアップは5つまでに保つ（無料プランの容量対策）
    ls -1t "$HOME"/data/backup_*.db 2>/dev/null | tail -n +6 | while read -r old; do
        rm -f "$old"
        echo "古いバックアップを削除: $(basename "$old")"
    done
else
    echo "DBがまだありません。スキップします。"
fi

# --- 2. コードの更新 -----------------------------------------------------
say "2/4 コードの取得"
cd "$PROJECT"
git pull

# --- 3. 依存 -------------------------------------------------------------
say "3/4 ライブラリの更新"
"$VENV/bin/pip" install --quiet -r requirements.txt
echo "完了。"

# --- 4. マイグレーション -------------------------------------------------
say "4/4 データベースの更新"
"$VENV/bin/flask" -e "$ENVFILE" --app wsgi db upgrade

cat <<'BANNER'

========================================================================
 最後に Webタブの緑の Reload ボタンを押してください。
 押すまで、直したものは反映されません。
========================================================================
BANNER
