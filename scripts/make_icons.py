"""アプリアイコン一式を1枚の元画像から書き出す（要件10章）。

使い方:
    pip install pillow
    python scripts/make_icons.py path/to/images.png

出力先: app/static/icons/
    icon-192.png / icon-512.png / icon-maskable.png /
    apple-touch-icon.png / favicon.ico

加工:
    - 正方形でなければ中央基準でトリミング
    - 透過は背景 #FBF8F7 で塗りつぶす（iOSが透過を黒表示するため）
    - maskable は安全領域を考慮し、余白を確保して中央に配置
"""
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow が必要です: pip install pillow")

PAPER = (0xFB, 0xF8, 0xF7)  # #FBF8F7
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "static", "icons")


def flatten(img: "Image.Image") -> "Image.Image":
    """透過を #FBF8F7 で埋めてRGBにする。"""
    img = img.convert("RGBA")
    bg = Image.new("RGBA", img.size, PAPER + (255,))
    bg.alpha_composite(img)
    return bg.convert("RGB")


def center_square(img: "Image.Image") -> "Image.Image":
    """中央基準で正方形にトリミング。"""
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def save_square(img: "Image.Image", size: int, name: str) -> None:
    out = img.resize((size, size), Image.LANCZOS)
    path = os.path.join(OUT_DIR, name)
    out.save(path)
    print("wrote", os.path.relpath(path))


def save_maskable(img: "Image.Image", size: int = 512, safe_ratio: float = 0.8) -> None:
    """安全領域を考慮し、中央に余白を確保して配置。"""
    inner = int(size * safe_ratio)
    canvas = Image.new("RGB", (size, size), PAPER)
    resized = img.resize((inner, inner), Image.LANCZOS)
    offset = (size - inner) // 2
    canvas.paste(resized, (offset, offset))
    path = os.path.join(OUT_DIR, "icon-maskable.png")
    canvas.save(path)
    print("wrote", os.path.relpath(path))


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("元画像のパスを指定してください（例: images.png）")

    src = sys.argv[1]
    os.makedirs(OUT_DIR, exist_ok=True)

    img = center_square(flatten(Image.open(src)))

    save_square(img, 192, "icon-192.png")
    save_square(img, 512, "icon-512.png")
    save_square(img, 180, "apple-touch-icon.png")
    save_maskable(img, 512)

    # favicon.ico（32x32）
    ico_path = os.path.join(OUT_DIR, "favicon.ico")
    img.resize((32, 32), Image.LANCZOS).save(ico_path, sizes=[(32, 32)])
    print("wrote", os.path.relpath(ico_path))

    print("\n完了。実機で小さく表示したときの判別を確認してください。")


if __name__ == "__main__":
    main()
