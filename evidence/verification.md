# sovity EDC CE 検証記録

検証日: 2026-11-11（Asia/Tokyo）。状態: 進行中。

## 環境と版

- 筆者環境（ユーザー申告）: Surface Laptop / Snapdragon ARM64 / WSL。
- 実測: WSL2 Ubuntu-24.04、Ubuntu 24.04.3 LTS、`uname -m` = `aarch64`。
- Docker Client/Server 28.4.0、linux/arm64、Compose v2.39.2。
- CE/UI: 16.8.1。公式リリースのLatest表示と2026-10-07公開を確認。
- 上流ソース: `bd1c8f5cef503d2fb36f5f42f940a5056ed7e911`。
- CE index digest: `sha256:c8033df70a847ed4635c3a145e68642e2e8ce35f984d7c211b49472e04ff5a52`。
- UI index digest: `sha256:03aec9d12c05c8ac69ed7cd92e9964393103f46eb1bdfd9a09f99ec8f68e0602`。
- 両イメージのGHCRマニフェストにlinux/amd64とlinux/arm64あり。
- CE arm64 digest: `sha256:1d3a51d92d7dc3d197aba88fad90d39197baf81c6951d6613a91e2318961dcba`。
- UI arm64 digest: `sha256:74534c65466a9376ae8d9477c32cd6983b8e5a5187e7b418f1e8afc32fda3da8`。
- PostgreSQL: 17-alpine（起動ログ上17.11）。

## 切り分け

1. 制限付きWindowsシェルの`wsl --list --verbose`は`Wsl/E_ACCESSDENIED`。
2. 権限制約外の同コマンドは成功しUbuntu-24.04 Running/WSL2。WSL故障ではない。
3. 既存設定でのDocker manifest inspect/pullはGHCRからdenied。
4. Python urllibによる匿名トークンでマニフェスト取得成功。
5. Python TemporaryDirectoryをDockerの`--config`に渡したpullは両方成功。既存の認証設定は変更せず、秘密情報も出力していない。

## 実行・観測

| 項目 | 状態 | 観測 |
|---|---|---|
| Compose構文 | 成功 | `docker compose ... config --quiet` exit 0 |
| 起動 | 成功 | `docker compose ... up -d` exit 0、9コンテナ |
| Provider起動 | 成功 | `Runtime ... ready` |
| 公開 | 成功 | New Data Offer → Available、REST-API Endpoint、GET、URL `http://data-server:8080/sample.json`、Title `Temperature sample`、ID `temperature-sample`、Description `One JSON record for the sovity CE hands-on.`、Publish unrestricted → Publish。`Data offer created successfully.` |
| 発見 | 成功 | Consumer → Catalog Browser → preconfigured provider (`http://provider/api/v1/dsp`)。Temperature sampleを1件表示 |
| 契約 | 成功 | ユーザー同意後Confirm。契約ID `01a1caf8-6047-7919-b0ad-1726326f0342`。Unrestricted、CONSUMING、provider |
| 初回転送 | 失敗・修正済み | 受信側がContent-Lengthのみ対応していたため400、UIはTERMINATED。chunked対応を追加 |
| 転送完了 | 成功 | 契約画面 → Transfer → REST-API Endpoint / POST / `http://data-server:8080/receive` / None → Initiate Transfer。転送ID `01a1cafa-17ff-7a89-9bb8-3615a7e74684` がCOMPLETED |
| データ本体 | 成功 | `http://localhost:18080/`で72 bytes、Matches Provider sample: True、JSON本体を表示。SHA-256 `826443ea85951e69e05805554db90e3eb356b3f794bd0e2e9d3048241ef97836` |
| 新規clone | 未実施 | 公開先`takuma-8trees/sovity-edc-ce-hands-on`をユーザーが作成。登録準備中 |

## 設定の根拠

- https://github.com/sovity/edc-ce/releases/tag/v16.8.1
- https://github.com/sovity/edc-ce/blob/v16.8.1/docs/deployment-guide/goals/local-demo-ce/docker-compose.yaml
- https://github.com/sovity/edc-ce/blob/v16.8.1/docs/deployment-guide/goals/local-demo-ce/caddyfiles/Caddyfile.cp-with-integrated-dp

公式Composeを基に、ホスト公開をloopback限定、DB/debugポート公開を除去、ログをINFOにし、標準Pythonのサンプル送受信サーバーを追加。
認証は`sovity-mock-iam`、管理APIは`management-iam-api-key`。DAPS/Portalなし。実運用の認証検証ではない。
上流LICENSE/NOTICEは主にElastic License 2.0、一部Apache 2.0と明記。記事でもこの区別を維持する。

## 画面とイメージ

- [転送完了](transfer-completed.jpg): 修正後のCOMPLETEDと、修正前のTERMINATEDの両方が表示されている。
- [受信データ](received-data.jpg): UI操作で転送したJSON本体と一致判定。
- Caddy 2.8: `sha256:226d1f059b75399fe19182893c7184591c07b97afc8dfcf44eeb80c9a77a530f`。
- PostgreSQL 17-alpine: `sha256:e5d2edd28b1f8d40a0a6c0c9cdc545b19b56a0d5d88f94bc11a97d970d4700d0`。
- Python 3.13-alpine: `sha256:1e1f6334529d1fb26a2ef619d7cffb30a7c7d7cc1cc7338ebee283a58d1aeaca`。
- 5種すべてのローカルイメージのArchitectureがarm64であることも確認。
