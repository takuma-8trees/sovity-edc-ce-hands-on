# Data Server分離の検証記録

実施日: 2026-11-12（日本時間）

## 変更

- 提供元を `provider-data-server`（ホスト18081）、受信先を `consumer-data-server`（ホスト18080）に分離。
- 提供側はサンプルを読み取り専用でマウント。受信側はサンプルを参照せず、専用volumeに直近の受信データを保存。
- 両画面でJSON、バイト数、実際のバイト列から算出したSHA-256を表示。
- CE/UI/Caddy/DBのイメージと設定は変更なし。

## 実行環境と結果

WSL Ubuntu / x86_64、Docker Engine 29.5.3、Docker Compose v5.1.4。
既存環境と分けたComposeプロジェクト `sovity-split-check` で実行。

```bash
docker compose -p sovity-split-check config --quiet
docker compose -p sovity-split-check up -d provider-data-server consumer-data-server
COMPOSE_PROJECT_NAME=sovity-split-check bash run/check-data-servers.sh
```

結果: PASS。

- 提供元のGETがサンプルを返す。
- 提供元へのPOSTは405、受信先の `/sample.json` は404。
- 空のPOSTは400。
- 異なるデータをPOSTすると受信画面はそのハッシュを表示し、提供元のデータは変わらない。
- Content-Length形式とchunked形式の両方でPOST成功。
- 受信バイト列が提供サンプルと一致し、両画面のSHA-256も一致。

サンプルは72バイト、SHA-256は以下。

```text
826443ea85951e69e05805554db90e3eb356b3f794bd0e2e9d3048241ef97836
```

このテストはHTTPで直接送信しており、EDC経由の契約・転送フロー全体は今回再検証していない。
旧版のEDC経由検証とスクリーンショットは `verification.md` および `hands-on-16.8.1-v1` の記録。
分離後のEDC経由受け入れ確認とスクリーンショット撮影では、空の環境からREADMEの手順を実施する。
