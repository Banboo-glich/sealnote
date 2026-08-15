"""WSGI エントリポイント。

PythonAnywhere の WSGI 設定ファイルから、この `app` をインポートする。
ローカルでは `flask --app wsgi run` でも起動できる。
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # ローカル開発用。本番（PythonAnywhere）ではWSGIサーバーが app を読む。
    app.run(host="127.0.0.1", port=5000)
