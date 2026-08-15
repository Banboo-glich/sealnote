#!/bin/bash
# PythonAnywhere 初期セットアップ（DEPLOY.md の手順3〜5を自動化する）。
#
# 使い方（PythonAnywhere の Bash コンソールで）:
#     git clone <リポジトリURL>
#     bash ~/sealnote/scripts/pythonanywhere_setup.sh
#
# やること:
#   1. 仮想環境を作り、requirements.txt を入れる
#   2. ~/data/.env を作る（SECRET_KEY 自動生成・あいことばは対話入力）
#   3. データベースを作る（flask db upgrade）
#   4. Webタブに貼る値を印字する
#
# 何度実行しても壊れない（既にあるものは作り直さない）。
set -euo pipefail

PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$HOME/.virtualenvs/sealnote"
ENVFILE="$HOME/data/.env"
ME="$(whoami)"

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

# --- 1. Python と仮想環境 -----------------------------------------------
say "1/4 仮想環境"

PY=""
for v in 3.12 3.11 3.13 3.10; do
    if [ -x "/usr/bin/python$v" ]; then
        PY="/usr/bin/python$v"
        break
    fi
done
if [ -z "$PY" ]; then
    echo "エラー: /usr/bin/python3.10〜3.13 が見つかりません。" >&2
    echo "  ls /usr/bin/python3.* の結果を添えて相談してください。" >&2
    exit 1
fi
PYVER="$("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
echo "使うPython: $PY (バージョン $PYVER)"

if [ -d "$VENV" ]; then
    echo "仮想環境はすでにあります: $VENV"
else
    "$PY" -m venv "$VENV"
    echo "作成しました: $VENV"
fi

say "2/4 ライブラリのインストール（数分かかります）"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r "$PROJECT/requirements.txt"
echo "完了。"

# --- 2. .env -------------------------------------------------------------
say "3/4 設定ファイル（.env）"

mkdir -p "$HOME/data"

if [ -f "$ENVFILE" ]; then
    echo "$ENVFILE はすでにあります。作り直しません。"
    echo "（あいことばを変えたい場合は、この行の下の案内を参照）"
else
    PYTMP="$(mktemp)"
    trap 'rm -f "$PYTMP"' EXIT
    cat > "$PYTMP" <<'PYCODE'
import os
import secrets
import sys
from getpass import getpass

from werkzeug.security import generate_password_hash

path, home = sys.argv[1], sys.argv[2]

print("アプリを開くときの「あいことば」を決めてください。")
print("（入力しても画面には表示されません）")
while True:
    pw = getpass("あいことば: ")
    if not pw:
        print("  空です。もう一度入力してください。")
        continue
    if pw != getpass("もう一度   : "):
        print("  一致しません。もう一度入力してください。")
        continue
    break

# 値はシングルクォートで囲む。ハッシュに含まれる $ が変数展開されるのを防ぐ。
# DATABASE_URL のスラッシュは4本（sqlite:/// + /home/...）。
lines = [
    "SECRET_KEY='%s'" % secrets.token_hex(32),
    "APP_PASSWORD_HASH='%s'" % generate_password_hash(pw),
    "DATABASE_URL='sqlite:////%s/data/sealnote.db'" % home.strip("/"),
    "FLASK_ENV='production'",
]
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
os.chmod(path, 0o600)
print("書き込みました: %s" % path)
PYCODE
    "$VENV/bin/python" "$PYTMP" "$ENVFILE" "$HOME"
    rm -f "$PYTMP"
    trap - EXIT
fi

# --- 3. データベース -----------------------------------------------------
say "4/4 データベース"

cd "$PROJECT"
"$VENV/bin/flask" -e "$ENVFILE" --app wsgi db upgrade
ls -l "$HOME/data/sealnote.db"

# --- 4. Webタブに貼る値 --------------------------------------------------
WSGI_OUT="$HOME/data/wsgi_to_paste.py"
cat > "$WSGI_OUT" <<PYWSGI
import os
import sys

from dotenv import load_dotenv

PROJECT = "$PROJECT"

# ① 先に環境変数を読み込む。
#    設定クラスは import された瞬間に os.environ を読むので、この順番が重要。
#    ②を先に書くと「必須の環境変数が未設定です」で起動に失敗する。
load_dotenv("$ENVFILE")
os.environ.setdefault("FLASK_ENV", "production")

# ② そのあとでアプリを読み込む
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

from wsgi import app as application  # noqa: E402
PYWSGI

cat <<BANNER

========================================================================
 コンソール側の作業は完了しました。
 残りは Webタブ（ブラウザ）での設定です。
========================================================================

【1】 Web タブ → Add a new web app
      → Next
      → "Manual configuration" を選ぶ  ※「Flask」ではない
      → Python $PYVER を選ぶ           ※上で使ったものと同じ
      → Next

【2】 Virtualenv 欄に貼る:

      $VENV

【3】 "WSGI configuration file:" のリンクを開き、中身を全部消して
      下記ファイルの内容に置き換えて Save:

      $WSGI_OUT

      ↓ 中身をここにも出しておきます（コピーして貼ってもよい）
------------------------------------------------------------------------
$(cat "$WSGI_OUT")
------------------------------------------------------------------------

【4】 Static files セクションに1行追加:

      URL:       /static/
      Directory: $PROJECT/app/static

【5】 Security セクション → Force HTTPS を Enabled に
      ※必須。OFF だとログインしても弾かれ続けます

【6】 上部の緑の Reload ボタンを押す

      → https://$ME.pythonanywhere.com

========================================================================
 あいことばを変えたくなったら:
   rm $ENVFILE && bash $0
 （DBは消えません。記録は残ります）
========================================================================
BANNER
