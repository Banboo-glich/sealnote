# PythonAnywhere デプロイ手順（はじめての人向け）

このアプリを `https://<ユーザー名>.pythonanywhere.com` で公開するまでの全手順。
上から順に、飛ばさずに進めること。所要時間は 40〜60分ほど。

用語のめやす：

- **Bashコンソール** … PythonAnywhere のサイト上で動く黒い画面。手元のPCではなく、
  向こうのサーバーの中にいる。
- **Webタブ** … 公開設定の画面。ここの **Reload** を押すまで、変更は反映されない。
- `<ユーザー名>` … PythonAnywhere で登録した名前。以下すべて自分のものに置き換える。

---

## 0. 手元のPCでの準備（GitHubに上げる）

> このリポジトリを clone して使う場合、手順0は済んでいる。手順1へ進んでよい。

### ⚠ 先に読む：Gitリポジトリの範囲を確認する

`git init` する前に、そのフォルダが**別のリポジトリの中に入っていないか**を確かめる。

```bash
git rev-parse --show-toplevel
```

ホームフォルダなど、意図しない場所が表示されたら要注意。そのまま `git add .` すると
**書類・ダウンロード・`.ssh` を含むフォルダ全体**が、関係ないリポジトリに
コミットされてしまう。プロジェクトのフォルダの中で `git init` して、
独立したリポジトリにしてから作業すること。

### 0-1. リポジトリを作る

Git Bash か PowerShell で、**sealnote フォルダの中に移動してから**：

```bash
cd <プロジェクトのフォルダ>
git init
git add .
git status          # ← ここで .env と data/ が出ていないことを必ず確認する
git commit -m "シールノート 初回コミット"
```

`git status` の一覧に `.env` や `*.db` が出てきたら、**そのままコミットしない**。
あいことばのハッシュやDBが公開されてしまう。`.gitignore` を確認すること
（現状の `.gitignore` では除外済みなので、通常は出てこない）。

### 0-2. GitHubに新しいリポジトリを作る

github.com → 右上の「+」→ **New repository**

- Repository name: `sealnote`
- **Private** を選ぶ（Publicでも秘密は漏れないが、非公開が無難）
- README等の追加チェックはすべて**外す**（すでに手元にあるため）

作成後に表示される「push an existing repository」のコマンドを実行する：

```bash
git remote add origin https://github.com/<GitHubユーザー名>/sealnote.git
git branch -M main
git push -u origin main
```

### 0-3. Private リポジトリ用のトークンを作る

PythonAnywhere から Private リポジトリを取ってくるにはパスワードではなく
**アクセストークン**が要る。

GitHub → 右上アイコン → Settings → 一番下の **Developer settings** →
**Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**

- Note: `pythonanywhere`
- Expiration: 90日など
- スコープ（チェックボックス）：**`repo` だけ**にチェック

生成された `ghp_...` の文字列を**このページを閉じる前にコピー**する（二度と表示されない）。
メモ帳などに一時的に貼っておく。

> Public リポジトリにした場合、この 0-3 は不要。

---

## 1. PythonAnywhere のアカウントを作る

pythonanywhere.com → **Pricing & signup** → **Create a Beginner account**（無料）

- ⚠ **ここで決めるユーザー名が、そのまま公開URLになる**
  （`<ユーザー名>.pythonanywhere.com`）。あとから変更できない。
- 無料プランでできること：Webアプリ1個、スリープなし、ディスク永続。
  このアプリはこれで十分動く。

登録したらメールの確認リンクを踏んでおく。

---

## 2. コードをサーバーに置く

上部メニュー **Consoles** → **Bash** をクリックして、コンソールを開く。

Public リポジトリの場合（認証不要）：

```bash
git clone https://github.com/<GitHubユーザー名>/sealnote.git
```

Private リポジトリの場合（0-3 のトークンをURLに埋め込む）：

```bash
git clone https://<トークン>@github.com/<GitHubユーザー名>/sealnote.git
```

確認：

```bash
ls ~/sealnote
```

`app  data  migrations  requirements.txt  wsgi.py ...` のように出ればよい。

---

## 3〜5をまとめて実行する（推奨）

手順3・4・5（仮想環境／`.env`／DB作成）は、スクリプト1本で済む：

```bash
bash ~/sealnote/scripts/pythonanywhere_setup.sh
```

途中であいことばを2回聞かれる（画面には表示されない）。それ以外は自動。
終わると、手順6でWebタブに貼る値がそのまま印字される。

何度実行してもよい（すでにあるものは作り直さない）。
うまく動かないときや、中で何をしているか確かめたいときは、以下の3〜5を手でたどる。

---

## 3. 仮想環境を作って、ライブラリを入れる

まず使えるPythonのバージョンを確認する：

```bash
ls /usr/bin/python3.*
```

`python3.12` があればそれを使う（無ければ 3.11、3.13 など、表示された中の新しいものを）。

```bash
mkvirtualenv --python=/usr/bin/python3.12 sealnote
pip install -r ~/sealnote/requirements.txt
```

- 数分かかる。プロンプトの先頭が `(sealnote)` に変わっていれば仮想環境の中にいる。
- あとで使う**仮想環境のパスは `/home/<ユーザー名>/.virtualenvs/sealnote`**。メモしておく。
- コンソールを開き直したときは `workon sealnote` で再び入れる。

---

## 4. 秘密の設定ファイル（.env）を置く

このアプリは `SECRET_KEY` と `APP_PASSWORD_HASH` が無いと**わざと起動に失敗する**。
これらは Git に入れないので、サーバー側で手作業で作る。

**DBやパスワードは、リポジトリの外（`~/data/`）に置く。**
リポジトリの中に置くと `git pull` や操作ミスで記録が消えかねない。

```bash
mkdir -p ~/data
```

### 4-1. SECRET_KEY を作る

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

出てきた64文字をコピー。

### 4-2. あいことばのハッシュを作る

```bash
python -c "from werkzeug.security import generate_password_hash as g; from getpass import getpass; print(g(getpass('あいことば: ')))"
```

入力した文字は画面に出ない（コンソールの履歴にあいことばが残らないように、
あえて `getpass` を使っている）。出てきた `scrypt:...` または `pbkdf2:...` の
長い文字列をコピー。

### 4-3. .env を書く

```bash
nano ~/data/.env
```

エディタが開くので、以下を貼り付けて自分の値に置き換える：

```
SECRET_KEY='ここに 4-1 の値'
APP_PASSWORD_HASH='ここに 4-2 の値'
DATABASE_URL='sqlite:////home/<ユーザー名>/data/sealnote.db'
FLASK_ENV='production'
```

**2つの注意点：**

1. **値はシングルクォート `'` で囲む。**
   ハッシュには `$` が含まれることがあり、囲まないと設定ファイルの読み取り時に
   変数展開と誤解されて壊れる。
2. **`sqlite:` のあとのスラッシュは4本。**
   `sqlite:///` （3本＝相対パス）＋ `/home/...` （絶対パスの先頭）で合計4本になる。
   3本だと別の場所にDBが作られて、記録が入らない・見えないという事故になる。

保存は `Ctrl+O` → `Enter`、終了は `Ctrl+X`。

確認：

```bash
cat ~/data/.env
```

---

## 5. データベースを作る

```bash
workon sealnote
cd ~/sealnote
flask -e ~/data/.env --app wsgi db upgrade
```

`-e ~/data/.env` は「この設定ファイルを読んでから実行して」という指定。
`.env` がリポジトリの外にあるので、この指定が要る（付け忘れると
「必須の環境変数が未設定です」で止まる）。

確認：

```bash
ls -l ~/data/sealnote.db
```

ファイルが出来ていればOK。

---

## 6. Webアプリを設定する

上部メニュー **Web** タブ → **Add a new web app**

1. ドメイン確認の画面 → **Next**
2. フレームワーク選択 → **Manual configuration** を選ぶ
   （⚠ **「Flask」を選ばないこと。** 選ぶと真っさらな別アプリが作られてしまう）
3. Pythonバージョン → 手順3で使ったものと**同じ**を選ぶ
4. **Next** で作成完了

作成後、Webタブの設定項目を上から埋めていく。

### 6-1. Virtualenv

「Virtualenv:」欄に入力：

```
/home/<ユーザー名>/.virtualenvs/sealnote
```

### 6-2. WSGI configuration file

「WSGI configuration file:」の青いリンク
（`/var/www/<ユーザー名>_pythonanywhere_com_wsgi.py`）をクリック。

エディタが開くので、**中身をすべて消して**以下に置き換える
（`<ユーザー名>` を自分のものに）：

```python
import os
import sys

from dotenv import load_dotenv

PROJECT = "/home/<ユーザー名>/sealnote"

# ① 先に環境変数を読み込む。
#    設定クラスは import された瞬間に os.environ を読むので、この順番が重要。
#    ②を先に書くと「必須の環境変数が未設定です」で起動に失敗する。
load_dotenv("/home/<ユーザー名>/data/.env")
os.environ.setdefault("FLASK_ENV", "production")

# ② そのあとでアプリを読み込む
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

from wsgi import app as application  # noqa: E402
```

右上の **Save**。

### 6-3. Static files（省略しない）

Webタブの **Static files** セクション → **Enter URL / Enter path** に：

| URL | Directory |
|---|---|
| `/static/` | `/home/<ユーザー名>/sealnote/app/static` |

これを設定しないと、CSS・アイコン・Service Worker の配信まで
アプリ本体（無料プランでは1ワーカーしかない）が処理することになり、
表示が重くなる。

### 6-4. Force HTTPS を ON にする

Webタブの **Security** セクション → **Force HTTPS** を **Enabled** に。

⚠ **これは必須。** 本番設定では Cookie に「HTTPSでしか送らない」印が付くため、
`http://` でアクセスすると**あいことばを入れてもログイン画面に戻され続ける**。
「ホーム画面に追加」（PWA）にもHTTPSが要る。

### 6-5. Reload

Webタブ上部の緑の **Reload** ボタンを押す。

---

## 7. 動作確認

`https://<ユーザー名>.pythonanywhere.com` をスマホのSafari（またはChrome）で開いて、
順に確かめる：

- [ ] ログイン画面が出て、デザイン（薄いピンクの見出し・明朝体）が効いている
      → 効いていなければ Static files の設定漏れ
- [ ] 目のアイコンを押すと、あいことばが表示される
- [ ] あいことばでログインできる → 戻されるなら Force HTTPS を確認
- [ ] 「シールを貼る」で1件保存できる
- [ ] 「今週のまとめ」が開く
- [ ] タブのアイコンがムーミンになっている
- [ ] Safari → 共有ボタン → **ホーム画面に追加** ができ、
      ホーム画面のアイコンが正しく出る

---

## 8. うまくいかないときの調べ方

**まずログを見る。** Webタブ → **Log files** セクション：

- **Error log** … Pythonの例外はここ。まずこれを見る（一番下が最新）
- **Server log** … 起動・再起動の記録
- **Access log** … アクセスの記録

| 症状 | 原因と対処 |
|---|---|
| `必須の環境変数が未設定です` | WSGIファイルで `load_dotenv` が `from wsgi import` より**後**にある。または `.env` のパスが違う |
| `unable to open database file` | `DATABASE_URL` のスラッシュが3本。または `~/data` が無い |
| ログインしても戻される | Force HTTPS が OFF、または `http://` で開いている |
| `ModuleNotFoundError: No module named 'flask'` | Webタブの Virtualenv 欄が空、またはパス違い |
| コンソールで `No module named 'flask_limiter'` / `No such command 'db'` | 素の `flask` を打っている（システム側が動いている）。`~/.virtualenvs/sealnote/bin/flask` とフルパスで実行する |
| `no such column: contents.status` | `db upgrade` を実行していない |
| 画面が真っ白／CSSが効かない | Static files の設定漏れ。設定済みなら古いキャッシュ（下記） |
| 直したのに変わらない | **Reload を押していない**。押しても直らなければ `app/static/sw.js` の `VERSION` を上げて再Reload |

Service Worker が古いCSSを掴んでいる場合、スマホ側で
「設定 → Safari → 履歴とWebサイトデータを消去」か、
ホーム画面のアプリを一度削除して追加し直すと確実。

---

## 9. 更新のしかた（コードを直したあと）

自動デプロイは無い。手元でコミット＆プッシュしたあと、Bashコンソールで：

```bash
bash ~/sealnote/scripts/pythonanywhere_update.sh
```

DBのバックアップ → `git pull` → 依存の更新 → マイグレーション、をまとめて行う。

最後に **Webタブ → Reload**。これを忘れると反映されない。

### 手で行う場合

```bash
cd ~/sealnote
git pull
~/.virtualenvs/sealnote/bin/pip install -r requirements.txt
~/.virtualenvs/sealnote/bin/flask -e ~/data/.env --app wsgi db upgrade
```

⚠ **`flask` や `pip` を素で打たないこと。**
PythonAnywhere にはシステム標準の Flask が入っているため、素で打つとそちらが動き、

```
ModuleNotFoundError: No module named 'flask_limiter'
Error: No such command 'db'.
```

になる。`workon sealnote` で仮想環境に入っていれば素のコマンドでもよいが、
フルパスで書くほうが確実。

---

## 10. 無料プランの運用（忘れると止まる）

- **3か月ごとに、Webタブの「Run until 3 months from today」ボタンを押す。**
  押さないとWebアプリが停止する（データは消えない。押せば復活する）。
  期限が近づくとPythonAnywhereからメールが来る。
  月1回ログインする習慣にしておけば確実。
- **月1回、DBをバックアップする。** 無料プランに自動バックアップは無い。
  Files タブ → `data/` → `sealnote.db` の**ダウンロードアイコン**をクリックして、
  手元のPCに保存する。

> 無料プランはサーバーからの外部通信が制限されているが、
> このアプリが使う Google Fonts は**閲覧者のブラウザ**が直接読みに行くので影響しない。
