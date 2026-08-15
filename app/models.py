"""データモデル。

要件7章の通り、テーブルは `contents` 1つのみ。
"""
from datetime import datetime, date

from . import db
from .constants import CATEGORY_LABELS, RATING_MAX


class Content(db.Model):
    """記録1件＝シール1枚。"""

    __tablename__ = "contents"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    creator = db.Column(db.String(120), nullable=True)
    rating = db.Column(db.SmallInteger, nullable=True)  # 1〜5、未入力可
    memo = db.Column(db.Text, nullable=True)  # 最大500文字
    logged_date = db.Column(db.Date, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

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
