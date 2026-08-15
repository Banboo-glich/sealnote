"""小さな共通ヘルパ。"""


def clean_text(value: str | None) -> str | None:
    """空文字は None に。前後の空白を除去する。

    任意入力の項目を「未入力＝NULL」で統一するために使う。
    """
    if value is None:
        return None
    value = value.strip()
    return value or None
