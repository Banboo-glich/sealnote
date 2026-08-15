# シールノート

日々ふれたコンテンツ（本・映画・舞台・音楽など）を1件ずつ「シール」として記録し、
週ごとに振り返るWebアプリ。利用者1人・単一パスワードで守るPWA。

- 技術構成：Python 3.12 / Flask 3.x（アプリケーションファクトリ方式）/ Jinja2 /
  Flask-SQLAlchemy / Flask-Migrate / Flask-WTF / Flask-Limiter / SQLite
- 対象：スマホ優先（横幅375px基準）、Safari(iOS)・Chrome

> 要件の詳細は `要件定義書_シールノート_v2.md` を参照。本READMEは環境構築・運用手順。

---

## ローカル開発

### 1. 仮想環境と依存

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   /  macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 環境変数

`.env.example` をコピーして `.env` を作り、値を埋める。

```bash
cp .env.example .env
```

- `SECRET_KEY`：`python -c "import secrets; print(secrets.token_hex(32))"`
- `APP_PASSWORD_HASH`：
  `python -c "from werkzeug.security import generate_password_hash as g; print(g('好きなあいことば'))"`
- `DATABASE_URL`：ローカルは未設定でよい（`data/sealnote.db` に自動作成）。
- `FLASK_ENV`：ローカルは `development`。

> `SECRET_KEY` または `APP_PASSWORD_HASH` が未設定だと**起動に失敗する**（意図的な安全策）。

### 3. DBの初期化（初回のみ）

```bash
# 環境変数を読み込んでから
flask --app wsgi db upgrade
```

`migrations/` が未生成の場合は最初に一度だけ：

```bash
flask --app wsgi db init
flask --app wsgi db migrate -m "initial"
flask --app wsgi db upgrade
```

### 4. 起動

```bash
flask --app wsgi run
# http://127.0.0.1:5000
```

### 5. テスト

```bash
pytest
```

認証・レート制限・集計・manifestを検証する（要件16章）。UIとPWAの実機挙動は目視で確認する。

---

## 3日間トライアル（要件17章）

デプロイ不要。同一Wi-Fi または `ngrok` で公開する。

- 開始前に最初の1件を一緒に入力しておく（空の画面は最大の離脱要因）
- 開始前にまとめ画面を見せる
- 「1日1件でよい」と伝える。期間中の声かけはしない

---

## デプロイ（PythonAnywhere 無料プラン / Beginner）

> **はじめてデプロイする場合は [`DEPLOY.md`](DEPLOY.md) を見る。**
> 画面操作・つまずきどころを含めた手順書。以下はその要約。

Render を使わない理由：無料PostgreSQLが30日で失効、無料Webが15分でスリープし復帰に
30〜60秒かかるため。「寝る前に1件」の使い方と相性が悪い。PythonAnywhereはスリープせず
ディスクが永続するので **SQLiteのまま運用できる**。

1. Beginner アカウントを作成
2. Bashコンソールで `git clone <このリポジトリ>`
3. `mkvirtualenv --python=/usr/bin/python3.12 sealnote` を作り
   `pip install -r requirements.txt`
4. `~/data` を作成し、`.env` を**リポジトリ外**（例：`~/data/.env`）に配置
   - `DATABASE_URL=sqlite:////home/<ユーザー名>/data/sealnote.db`（スラッシュ4本）
5. Webタブで「手動設定（Manual configuration）」のWebアプリを作成し、仮想環境パスを指定
6. WSGI設定ファイルで `.env` を読み込み、`wsgi.py` の `app` をインポート（下記例）
7. Webタブの **Static files** で URL `/static/` → パス `<プロジェクト>/app/static` を割り当てる
   （**省略しない**。静的配信をWSGIワーカーに任せると無料枠の1ワーカーが詰まる）
8. Webタブの **Force HTTPS** を有効化（PWAにも必須）
9. `flask -e ~/data/.env --app wsgi db upgrade`
   （`.env` がリポジトリ外にあるため `-e` が必要）
10. Reload

### WSGI設定ファイルの例（PythonAnywhere）

```python
import os
from dotenv import load_dotenv

project = "/home/<ユーザー名>/sealnote"
load_dotenv("/home/<ユーザー名>/data/.env")   # .env はリポジトリ外
os.environ.setdefault("FLASK_ENV", "production")

import sys
if project not in sys.path:
    sys.path.insert(0, project)

from wsgi import app as application
```

### 更新手順

自動デプロイは不可。`git pull` →（必要なら `flask db upgrade`）→ Reload。

### 運用上の必須作業

- **3か月ごとにWebタブの延長ボタン（Run until 3 months from today）を押す。**
  押さないとアプリが停止する（データは消えない）。月1回ログインする習慣にしておけば確実。
- **月1回、Filesタブから `sealnote.db` をダウンロードして保管する。**
  無料プランに自動バックアップはない。

### DB配置の注意

- **DBファイルはリポジトリの外に置く**（`~/data/`）。リポジトリ内だと `git pull` や
  誤操作で記録が失われる。`.gitignore` で `*.db` と `data/` を除外済み。

---

## PWA（ホーム画面に追加）

**iOSは自動でインストールを促さない。** 利用者に口頭で伝える：

> Safariでサイトを開く → 共有ボタン → 「ホーム画面に追加」

CSSを変更したら `app/static/sw.js` の `VERSION` を上げる（旧キャッシュを自動削除）。

---

## アイコンについて

`app/static/icons/` に以下を配置する（要件10章）。**利用者指定画像 `images.png` から書き出す。**

| ファイル | サイズ | 用途 |
|---|---|---|
| `icon-192.png` | 192×192 | Android・manifest |
| `icon-512.png` | 512×512 | manifest |
| `icon-maskable.png` | 512×512 | Android（安全領域を考慮し余白を確保） |
| `apple-touch-icon.png` | 180×180 | iOS（必須） |
| `favicon.ico` | 32×32 | タブ・お気に入り |

- 透過部分は背景 `#FBF8F7` で埋める（iOSは透過を黒く表示するため）
- 正方形でなければ中央基準でトリミング

書き出しヘルパ：`python scripts/make_icons.py <元画像>`（Pillow が必要）。

---

## プライバシー（利用者への事前説明・要件20章）

サーバー管理者は技術的にDBの内容（ひとことメモ含む）を閲覧できる。
**「サーバーは自分が管理しているので、見ようと思えば見られる」ことを事前に伝えること。**
