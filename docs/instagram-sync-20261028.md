# Instagram自動更新：修正・検証・復旧手順（2026-10-28）

## 現在の到達点

| 項目 | 結果 |
|---|---|
| コード修正 | mainへ反映済み：`2581462b43c59732a248d2746d4046451286b382` |
| 取得失敗時の保護・再試行・安全な診断 | ローカル／Actionsの34テストに合格 |
| 実際の認証 | **未復旧。既存トークンの期限切れをMetaの応答で確認** |
| 既存投稿・画像 | 6投稿・6画像を保持。取得失敗で変更していない |
| 現行公式HPへの反映経路 | 既存ワークフローで再公開し、公開JSON・取得状態・全6画像を生成元と照合済み |
| ブラウザ | PCでトップ／イベントページの4投稿、画像、順序、リンクを確認 |
| スマホ | モバイル幅・実機は未検証。このブラウザ環境で利用できる操作には画面幅の切替がなく、代替の検証用ページ作成もURL制限で実行できなかった。スマホ確認済みとは扱わない |

公開経路が正常でも、新しいInstagram投稿の取得が復旧したことにはならない。再認証とSecret更新後の実取得成功が残る。

## 確定した原因

[修正後の実行](https://github.com/MDL20241119/GarrawayFapp.github.io/actions/runs/40605465388)で、通常投稿の`media`と、独立した`me`確認の両方が認証エラーを返した。

| 安全に抽出した項目 | mediaの応答 |
|---|---|
| HTTP | 400 |
| error.type | OAuthException |
| code / error_subcode | 190 / 0 |
| is_transient | 応答にないためnull |
| fbtrace_id | A64hW9c_lKx2hfJrCehLrea |
| messageの要旨 | セッションは2026-10-27 00:56:55 PDTに期限切れ |
| 日本時間 | **2026-10-27 16:56:55 JST** |

トークン、認証ヘッダー、認証情報付きURL、レスポンス全文は記録していない。

直前の[正常実行](https://github.com/MDL20241119/GarrawayFapp.github.io/actions/runs/40455962887)のログでは、2026-10-27 14:33:25 JSTに通常投稿の取得・画像処理が終了し、既存のサイト検証と保存に成功している。この日時はログから確認したもので、`updated_at`だけから推定したものではない。

成功時のコードと最初の失敗時のコードは同じ。差分`242afc9..8310ebb`は保存JSON・画像だけで、取得ワークフローや検証スクリプトに変更はなかった。コード変更が今回の認証失敗を発生させた証拠はない。

## 認証・API仕様の照合と未確認事項

- 現行設定はInstagram Login系の`graph.instagram.com`。無バージョンの既存URL構成と取得フィールド`id,caption,media_type,media_url,thumbnail_url,permalink,timestamp`を維持した。今回の応答はフィールドエラーではなくトークン失効を明示している。
- 発行元Metaアプリ、トークン種別・長短、実際に付与された権限、Secretsに入っているユーザーIDの値と公式アカウントの対応は、失効のため実APIで再確認できなかった。値を取り出したり公開したりしていない。
- 復旧後は`me`の`user_id`／`id`と設定ID、`username`と`garrawayf_lounge`を照合し、別アカウントの内容を公開しない。Instagram Loginで必要な基本権限は`instagram_business_basic`。
- APIバージョンは無指定のまま。成功応答にバージョンヘッダーがある場合だけ記録する。今回の失敗応答から実効バージョンは確認できていない。根拠なく最新バージョンへ移行していない。
- 共同投稿APIは直前の正常実行でも400を返していた。Metaは共同投稿取得を文書化しているが、Facebook Login／Unified Login等の方式による対応差があり、今回のInstagram Login設定で利用できるとは確認していない。期限切れ前の400本文は旧コードが捨てており、未対応／権限不足のどちらかを確定できない。任意の取得として扱い、通常投稿を巻き込まない。
- タグ付け投稿、Storiesの取得経路は追加していない。

Meta公式資料：

- [Business Login for Instagram](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login/business-login)
- [Refresh Access Token](https://developers.facebook.com/documentation/instagram-platform/reference/refresh_access_token)
- [IG User](https://developers.facebook.com/documentation/instagram-platform/instagram-graph-api/reference/ig-user)
- [IG Media](https://developers.facebook.com/documentation/instagram-platform/reference/instagram-media)
- [Collaboration](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-facebook-login/collaboration)

公式資料の検索結果で関連仕様を確認した。本文の直接取得は429等で制限され、すべての仕様を全文確認できたという意味ではない。

## 変更ファイルと保護の仕組み

| ファイル | 変更 |
|---|---|
| `.github/workflows/instagram-feed.yml` | Python処理を分離。34テストと既存データ検証を先に実行。15分のジョブ上限。失敗時も検証済みの既存投稿を保ち、安全な状態記録だけ保存する。取得の非ゼロ終了はそのまま残る |
| `scripts/update_instagram.py` | 安全なAPIエラー抽出、タイムアウト、最大3回の一時障害再試行、一時領域・画像処理・参照整合性検証・置換失敗時の復元 |
| `scripts/test_instagram_feed.py` | 正常系・異常系・秘密情報の非公開・途中失敗の保護を検証する34テスト |
| `data/instagram-sync-status.json` | Actionsが生成する取得状態。失敗コミット：`c0f5ea75b41a5c64e7baa764f065b486a1e28a2b` |
| `docs/instagram-sync-20261028.md` | この報告・復旧手順 |

`scripts/validate_site.py`の既存条件は変更していない。現行公式HP側のワークフロー・`app/social-data.ts`・デザイン・イベントアプリ・API設定にも変更はない。未公開の依存整理PR等も取り込んでいない。作業開始時の両チェックアウトはクリーンであり、別PCや別セッションの未共有作業ツリーは検査できない。

一時障害（タイムアウト・通信・429・一時エラー・5xx）は最大3回、通常2秒→4秒のバックオフ。数値の`Retry-After`がある場合は最大60秒で尊重する。認証・権限等の恒久エラーは再試行しない。APIの読み取りは30秒、画像は45秒、取得サイズも制限する。

APIレスポンスの形・投稿数・投稿属性・アカウント・画像デコード・ハッシュ・参照を検証し、すべての対象画像を一時領域で最適化する。新しいJSONが参照する画像一式を確認してから古い画像を削除する。置換途中の例外では元のバイト列へ戻す。リモート公開の単位は一式を含むGitコミットであり、取得途中のファイルはコミットしない。

従来どおり最新6投稿、最大1080px、JPEG品質82、画像内容のSHA256先頭12桁によるキャッシュ更新を維持した。文章のみの変更も内容更新として検出する。

`updated_at`は掲載内容の更新日時。`checked_at`は試行日時。`last_fetch_succeeded_at`は新処理が一式の取得・保存を完了した日時。今回は初回から失敗したため最後の値はnullであり、過去の`updated_at`を流用して成功日時を作っていない。過去の正常取得は前述の実行ログで別途確認できる。

## テスト結果

ローカルとActionsで34件合格。正常取得、変更なし、文章変更、同一投稿の画像変更、認証、権限、タイムアウト、通信、レート制限、Retry-After上限、5xx、一時的400、回復、空／不足／不正JSON、不正投稿、画像未取得・破損・過大、共同投稿未対応・一時障害、別アカウント、認証情報反射、置換途中の失敗を検証した。異常時は元JSON・画像のバイト列、過去の成功日時、秘密情報の非出力も確認した。

```bash
python -m unittest discover -s scripts -p 'test_instagram*.py' -v
python scripts/validate_site.py
```

ワークフローYAML・Python構文・`git diff --check`も合格。`continue-on-error`は使っていない。実APIの失効エラーは再試行せず、ジョブは正しくfailureになり、後続の既存サイト検証と失敗状態の保存だけが成功した。

## 現行公式HPへの反映確認

[既存の公式公開処理・attempt 2](https://github.com/GarrawayF/garrawayf.github.io/actions/runs/40600383420/attempts/2)を再実行。2026-10-28 08:58:29 JSTにsuccess。公式ソースは`b7a1975382fd79fd7cbe91a78cbbf63a5d92e29d`、取り込み元は`c0f5ea75b41a5c64e7baa764f065b486a1e28a2b`とログで確認した。

既存39 Pythonテスト、Kyushu 5テスト、既存Node回帰、イベント申込のモック検証、production audit、lint、ビルド、公開後検証を含む全ステップが成功。実申請・承認・メール送信はしていない。

- [公式HP](https://garrawayf.github.io/)
- [イベントページ](https://garrawayf.github.io/events/)
- [公開Instagram JSON](https://garrawayf.github.io/data/instagram.json)
- [公開取得状態](https://garrawayf.github.io/data/instagram-sync-status.json)

公開JSONは生成元と一致。公開状態も生成元と一致し、failureを正しく示す。全6画像についてHTTP 200、生成元とのバイト一致、SHA256と`image_version`の一致、投稿順を確認した。

| 投稿ID | 画像ハッシュ |
|---|---|
| 18140689906713968 | 2c01ca8f347a |
| 17977820004129423 | cacc00c08bc7 |
| 18009633227991403 | 77ec04d9d793 |
| 18077418500458072 | dd2a57806c13 |
| 17977460820154190 | 86c8545acc9e |
| 18130122905306444 | 6db905b6fab1 |

PCブラウザ（幅1363px）でトップページ・イベントページの4件表示、各画像のnaturalWidth、日付順、投稿へのリンクを確認。イベントページのドキュメント幅1348pxで横はみ出しなし。トップは既存の遅延読込後に4画像の読み込みを確認した。スマホ幅・実機は未確認。Facebook埋め込みはこの検証ブラウザで接続拒否だったが、本修正の対象外であり変更していない。

### 実行頻度の実績

設定は生成元が毎時7・37分、公式HPが17・47分。ただし直近20回ずつの定期実行では、生成元の間隔は約2.1～7.4時間（中央値約4.25時間）、公式は約1.9～6.8時間（中央値約3.87時間）だった。対象期間は2026-10-24～27 UTC。30分以内の取得・公開を保証しない。新しいwebhook・通知連携・公開経路は追加していない。

## 残る本人操作と再発防止

1. **元のMetaアプリで公式アカウントを再認証し、有効なトークンを発行する。** 現行ホストに対応するInstagram Loginの方式・公式アカウント・`instagram_business_basic`を確認する。発行元や方式を確認せずFacebook Loginのトークンへ差し替えない。
2. **生成元リポジトリ**`MDL20241119/GarrawayFapp.github.io`のSettings → Secrets and variables → Actions → `INSTAGRAM_ACCESS_TOKEN`を更新する。`INSTAGRAM_USER_ID`は同じ公式アカウントの対応IDと照合し、不一致の場合だけ修正する。認証情報はGitHubの設定画面へ直接入力し、チャットへ貼らない。
3. Actionsの「Update Instagram Feed」をmainで手動実行する。取得・保存とサイト検証の両方が成功し、`state=success`と`last_fetch_succeeded_at`が更新されたことを確認する。その後、既存の「Deploy Garraway F website」を実行するか定期実行を待ち、公開JSON／画像／表示とスマホを再確認する。

Metaの長期Instagram Userトークン更新は、発行後24時間以上かつ未失効であることが条件。失効済みの今回のトークンをrefresh APIで延命できると扱わない。

**継続運用の残件：有効期限前の更新と、更新トークンをSecretへ安全に保存する運用が必要。** 現行のActions用`GITHUB_TOKEN`の`contents:write`だけではRepository Secretへ書き戻せず、この接続にもSecrets更新用ツールはない。自動ローテーションを実装・実証したとは報告しない。再発防止の当面の担当作業は、発行日時・有効期限を管理者の非公開管理先へ記録し、長期トークンの45日目など期限に余裕を持つ時点で公式手順による更新とSecret保存を行うこと。恒久自動化には発行方式の確認と、既存の安全な資格情報保存先／書き戻し権限の設計が別途必要になる。

## 再発時の確認とロールバック

1. 取得状態JSONの`state`、`checked_at`、`last_fetch_succeeded_at`、`error.category`、HTTP、code／subcode、秘匿化messageを見る。`updated_at`だけで取得成功を判断しない。
2. 190／authenticationなら再認証・Secret、permissionなら付与権限、requestならID・フィールド・API方式を確認。一時障害は最大3回の結果と次の定期実行を確認する。生のレスポンスやトークン付きURLを貼らない。
3. 生成元コミット → 公式公開ログの取り込みSHA → 公開JSONのID・内容日時 → 画像バイト／ハッシュ → PC・スマホの順で、止まった段階を切り分ける。公開成功だけでAPI取得成功と扱わない。
4. コードの回帰が判明した場合は、最新mainから作業ブランチを作り、修正コミット`2581462b43c59732a248d2746d4046451286b382`を`git revert`する。既存運用で検証・反映し、他作業を巻き込むmainの強制リセットは行わない。データは独立して保持する。
5. データ自体の復旧が必要な場合だけ、確認済みスナップショット`8310ebb92767883ba5149fd0901da55a1b49253d`の`data/instagram.json`と`images/instagram/`を**セットで**別コミットへ復元し、`scripts/validate_site.py`合格後に既存公式公開処理を実行する。ロールバックしても失効した認証は復旧しない。
