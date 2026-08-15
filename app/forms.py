"""フォーム定義（Flask-WTF）。

全POSTフォームでCSRFトークンを使う（要件12章）。
必須項目はカテゴリとタイトルの2つのみ（要件F-01）。
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    TextAreaField,
    DateField,
    RadioField,
    PasswordField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, Optional, AnyOf

from .constants import (
    CATEGORIES,
    CATEGORY_KEYS,
    TITLE_MAX,
    CREATOR_MAX,
    MEMO_MAX,
)


class LoginForm(FlaskForm):
    """単一パスワードによるゲート（要件8章）。ユーザー名は無い。"""

    password = PasswordField(
        "あいことば", validators=[DataRequired(message="あいことばを入力してください")]
    )
    submit = SubmitField("ひらく")


class ContentForm(FlaskForm):
    """記録の追加・編集フォーム（F-01, F-03）。"""

    category = SelectField(
        "カテゴリ",
        choices=CATEGORIES,
        validators=[
            DataRequired(message="カテゴリを選んでください"),
            AnyOf(CATEGORY_KEYS, message="カテゴリが不正です"),
        ],
    )
    title = StringField(
        "タイトル",
        validators=[
            DataRequired(message="タイトルを入力してください"),
            Length(max=TITLE_MAX, message=f"タイトルは{TITLE_MAX}文字までです"),
        ],
    )
    creator = StringField(
        "作り手",
        validators=[
            Optional(),
            Length(max=CREATOR_MAX, message=f"作り手は{CREATOR_MAX}文字までです"),
        ],
    )
    # 評価は未入力可。"" を「未入力」として扱う。
    rating = RadioField(
        "評価",
        choices=[("", "なし"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")],
        validators=[Optional()],
        default="",
    )
    memo = TextAreaField(
        "ひとことメモ",
        validators=[
            Optional(),
            Length(max=MEMO_MAX, message=f"メモは{MEMO_MAX}文字までです"),
        ],
    )
    logged_date = DateField(
        "記録日",
        validators=[DataRequired(message="日付を入れてください")],
    )
    submit = SubmitField("シールを貼る")

    def rating_value(self):
        """評価を int または None に正規化して返す。"""
        raw = (self.rating.data or "").strip()
        if raw == "":
            return None
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None
        return value if 1 <= value <= 5 else None
