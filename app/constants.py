"""アプリ全体で使う定数。

CATEGORIES は要件で「7種・変更不可」と定められている。
順序・キー・「舞台・演劇」の存在を変更しないこと。
"""

# (key, 表示名) の並び。key はDBに保存する値。順序は表示順。
CATEGORIES = [
    ("book", "本"),
    ("movie", "映画"),
    ("stage", "舞台・演劇"),
    ("music", "音楽"),
    ("youtube", "YouTube"),
    ("drama", "ドラマ・アニメ"),
    ("other", "そのほか"),
]

# key -> 表示名 の辞書（テンプレートやサービスで参照）
CATEGORY_LABELS = {key: label for key, label in CATEGORIES}

# バリデーション用の有効なキー集合
CATEGORY_KEYS = [key for key, _ in CATEGORIES]

# 入力上限（要件 F-01）
TITLE_MAX = 200
CREATOR_MAX = 120
MEMO_MAX = 500

# 評価の範囲
RATING_MIN = 1
RATING_MAX = 5
