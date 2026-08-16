"""アプリ全体で使う定数。

CATEGORIES は要件では「7種・変更不可」だったが、利用者の指示で「ゲーム」を追加して8種にした。
既存キーの順序・名前と「舞台・演劇」の存在は変更しないこと（過去の記録が壊れるため）。
"""

# (key, 表示名) の並び。key はDBに保存する値。順序は表示順。
CATEGORIES = [
    ("book", "本"),
    ("movie", "映画"),
    ("stage", "舞台・演劇"),
    ("music", "音楽"),
    ("youtube", "YouTube"),
    ("drama", "ドラマ・アニメ"),
    ("game", "ゲーム"),
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

# --- 今月の発見（要件23章）---
# 文言はここにだけ置く。コード中に直書きしない（要件23-7）。
# 事実と数字だけを述べ、解釈は足さない。「あなたは〜」で始めない。感嘆符は使わない（要件23-4）。
DISCOVERY_TEMPLATES = {
    "memo_gap": "評価は{rating}だったけれど、いちばん長く書いたのは『{title}』でした",
    "longest_memo": "今週いちばん長く語ったのは『{title}』でした",
    "long_wait": "『{title}』は、気になるに入れてから{days}日後に見ました",
    "reunion": "{creator}を記録するのは、{year}年{month}月以来2回目です",
    "busy_day": "{month}月{day}日は、1日に{count}つ記録しました",
    "first_category": "{category}を記録したのは、これが初めてです",
    "bookends": "今週の1まい目は『{first}』、最後は『{last}』でした",
    "only_one": "今週の1まいは『{title}』でした",
}

# 見出し
DISCOVERY_HEADING = "今週の発見"

# 発見は最大2件まで（要件23-5）
DISCOVERY_LIMIT = 2
# 「長く語った」とみなすメモの文字数
DISCOVERY_MEMO_MIN = 40
# 「気になる」から実際に見るまでの日数がこれ以上なら long_wait が成立
DISCOVERY_WAIT_DAYS = 7
# 1日にこの件数以上あれば busy_day が成立
DISCOVERY_BUSY_MIN = 3


# --- 状態（要件21章：気になるリスト）---
# "done" = 見たもの（シール1枚）。"wish" = まだ見ていないもの。
STATUS_DONE = "done"
STATUS_WISH = "wish"
STATUS_KEYS = [STATUS_DONE, STATUS_WISH]
