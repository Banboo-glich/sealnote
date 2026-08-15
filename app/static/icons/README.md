# アイコン（未配置）

要件10章のアイコン一式をここに置く。**利用者指定画像 `images.png` の受領後**に生成する。

生成方法（Pillow が必要）:

```bash
pip install pillow
python scripts/make_icons.py <元画像のパス>
```

生成されるファイル:

| ファイル | サイズ | 用途 |
|---|---|---|
| `icon-192.png` | 192×192 | Android・manifest |
| `icon-512.png` | 512×512 | manifest |
| `icon-maskable.png` | 512×512 | Android（安全領域を考慮した余白つき） |
| `apple-touch-icon.png` | 180×180 | iOS（必須） |
| `favicon.ico` | 32×32 | タブ・お気に入り |

未配置でもアプリは動作するが、iOSのホーム画面追加ではアイコンが正しく出ない。
公開前に必ず配置すること。
