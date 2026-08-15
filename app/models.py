"""データモデル。

要件7章の通り、テーブルは `contents` 1つのみ。
"""
from datetime import datetime, date

from . import db
from .constants import CATEGORY_LABELS, RATING_MAX, STATUS_DONE, STATUS_WISH


class Content(db.Model):
    """記録1件＝シール1枚。気になる項目（未視聴）も同じテーブルで持つ。

    status で区別する（要件21-3）。新規テーブルを作らないのは、
    変換のときに行をコピーせず、同じ行の状態を変えるだけで済ませるため。
    """

    __tablename__ = "contents"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    creator = db.Column(db.String(120), nullable=True)
    rating = db.Column(db.SmallInteger, nullable=True)  # 1〜5、未入力可
    memo = db.Column(db.Text, nullable=True)  # 最大500文字
    # 気になる項目はまだ見ていないため記録日を持たない（要件21-3）
    logged_date = db.Column(db.Date, nullable=True, index=True)

    # "done"（見た）または "wish"（気になる）
    status = db.Column(
        db.String(10),
        nullable=False,
        default=STATUS_DONE,
        server_default=STATUS_DONE,
        index=True,
    )
    # 気になるリストに入れた日時。直接記録した場合は NULL のまま。
    # done になっても消さない（リスト経由で見たものだと分かるようにするため）。
    wished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    @property
    def is_wish(self) -> bool:
        return self.status == STATUS_WISH

    @property
    def from_wish(self) -> bool:
        """気になるリスト経由で見たものか（要件21-9の集計に使う）。"""
        return self.status == STATUS_DONE and self.wished_at is not None

    @property
    def memo_length(self) -> int:
        """お気に入り判定で使う、メモの文字数。"""
        return len(self.memo) if self.memo else 0

    @property
    def share_text(self) -> str:
        """LINEなどに送る共有用テキスト。

        アプリはあいことばで守られているため、URLを送っても相手は開けない。
        そこでカードの中身そのものを文章にして送る。
        絵文字は使わない（要件9章）。
        """
        lines = [f"【{CATEGORY_LABELS.get(self.category, 'そのほか')}】{self.title}"]
        if self.creator:
            lines.append(self.creator)
        if self.rating:
            lines.append("★" * self.rating + "☆" * (RATING_MAX - self.rating))
        if self.memo:
            lines.append("")
            lines.append(self.memo)
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"<Content {self.id} {self.category} {self.title!r}>"
