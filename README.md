# Garraway F Living Lab

Garraway F公式サイトのGitHub Pages対応ソースです。

## Branches

- `main`: GitHub Pagesで公開する静的ファイル
- `sites-source`: React / Next.jsの編集用ソース
- `legacy-pages-20260830`: 移行前の旧GitHub Pages版

## Local development

```bash
npm ci
npm run dev
```

## Static build

```bash
npm run build
```

生成物は`out/`に出力されます。SNS表示は既存の`data/instagram.json`と
`data/facebook-events.json`を利用します。

ChatGPT Sites版は別の公開環境として継続し、このリポジトリの更新では削除されません。
