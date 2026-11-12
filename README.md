# sovity EDC CE hands-on

sovity EDC CE 16.8.1で、ProviderからConsumerへJSONを1件交換するローカルデモです。公開・カタログ取得・契約・転送はsovity UIで操作し、受信内容は同梱サーバーの画面で確認します。

**旧版 `hands-on-16.8.1-v1` の検証状況:** Surface Laptop（Snapdragon ARM64）のWSL2 Ubuntu 24.04.3 LTSで、GitHub新規clone・空のDBから、公開→発見→契約→転送完了→受信内容一致まで確認済みです。Data Server分離後の確認は [分離後の検証記録](evidence/data-server-split.md) を参照してください。

## 1. 環境の起動

Docker EngineとDocker Compose v2が使える環境が必要です。読者の環境をSurfaceやWSLに限定しません。今回の実測は`aarch64`、Docker 28.4.0、Compose v2.39.2です。CE/UI両イメージにlinux/amd64とlinux/arm64がありますが、amd64での実行は未検証です。

```bash
git clone https://github.com/takuma-8trees/sovity-edc-ce-hands-on.git
cd sovity-edc-ce-hands-on
git checkout main
docker compose up -d
```

初回はイメージ取得とDB初期化を待ちます。起動直後に画面が空なら少し待って再読み込みしてください。

| 画面 | URL |
|---|---|
| Provider UI | http://localhost:11000 |
| Consumer UI | http://localhost:22000 |
| Provider提供データ確認 | http://localhost:18081/ |
| Consumer受信データ確認 | http://localhost:18080/ |

ポート11000、22000、18080、18081を空けてください。ホストへの公開は127.0.0.1に限定しています。リモートホストで動かす場合のブラウザー接続は今回の検証範囲外です。

ブラウザーを2つのウィンドウに分け、左をProvider、右をConsumerに固定すると立場を意識しやすくなります。左にはProvider UIと提供データ確認画面、右にはConsumer UIと受信データ確認画面を別タブで開いてください。

旧版から更新する場合は `docker compose up -d --remove-orphans` で旧`data-server`コンテナを除去できます。volumeは保持されます。既存のData Offerや契約のURLは自動更新されません。新しいIDで提供情報を登録し、新たに契約・転送してください。

### GHCRの取得がdeniedになる場合

今回の環境では既存Docker設定でGHCRのpullが拒否され、空の一時認証設定では成功しました。同じ場合は既存設定を変更せず、以下をBashで実行してから起動してください。

```bash
docker_config_tmp=$(mktemp -d)
docker --config "$docker_config_tmp" pull ghcr.io/sovity/edc-ce:16.8.1
docker --config "$docker_config_tmp" pull ghcr.io/sovity/edc-ce-ui:16.8.1
rmdir "$docker_config_tmp"
docker compose up -d
```

## 2. Providerとしてデータを提供する

左側の画面でProviderとして操作します。http://localhost:18081/ で提供するJSONとSHA-256を確認してからProvider UIへ移ります。

Provider UIの **New Data Offer** を開きます。

| 項目 | 入力・選択 |
|---|---|
| Offer Type | Available (with data source) |
| Type | REST-API Endpoint |
| Method | GET |
| URL | `http://provider-data-server:8080/sample.json` |
| Authentication | None |
| Title | `Temperature sample` |
| Data offer ID | `temperature-sample` |
| Description | `One JSON record for the sovity CE hands-on.` |
| Publishing Mode | Publish unrestricted |

ParameterizationとAdvanced Fieldsはオフのまま、**Publish** を押します。`Data offer created successfully.` が表示されます。

初回の入力直後、未登録のIDに`Asset ID is already taken`と表示される挙動を観測しました。少し待ち、**Data Offers**にまだ存在しないことを確認してから再度**Publish**すると成功しました。既存IDを重複作成しないでください。

ここで入力するURLはコンテナからアクセスするためのものです。`localhost:18081`ではなく、Composeのサービス名`provider-data-server`を使います。

## 3. Consumerとしてデータを利用する

ここからは右側の画面へ移り、Consumerとして操作します。

### データの発見・契約

1. Consumer UIの **Catalog Browser** を開く。
2. **Preconfigured Counterparties** の `provider http://provider/api/v1/dsp` を選ぶ。手入力する場合はConnector Endpointを`http://provider/api/v1/dsp`、Participant IDを`provider`として **Fetch Catalog**。
3. **Temperature sample** を開き、**Negotiate** を押す。
4. **Contract Offers** の `Unrestricted` を確認し、**Negotiate**。
5. **Data Offer Terms & Conditions** を確認して同意チェックを入れ、**Confirm**。
6. **Contract Agreement** の画面に契約ID、Counter Party ID `provider`、Contract Policy `Unrestricted` が表示されることを確認。

### HTTP転送

契約画面の **Transfer** を選びます。

| 項目 | 入力・選択 |
|---|---|
| Data Sink Type | REST-API Endpoint |
| Method | POST |
| URL | `http://consumer-data-server:8080/receive` |
| Authentication | None |

**Initiate Transfer** を押し、**Transfer History** の最新の行が `COMPLETED` になるのを待ちます。`Successfully initiated transfer.` は開始の通知なので、それだけで完了と判断しないでください。

### 受信した中身を確認

http://localhost:18080/ を開きます。先に開いていた場合は再読み込みします。

```text
Received bytes: 72
SHA-256: 826443ea85951e69e05805554db90e3eb356b3f794bd0e2e9d3048241ef97836
```

```json
{"id":"sample-001","message":"Hello from Provider","temperatureC":23.5}
```

左に http://localhost:18081/ の提供データ確認画面、右に受信データ確認画面を並べます。JSONの中身、Source bytesとReceived bytes、SHA-256が一致することを確認してください。ハッシュ値は各サーバーが保持するバイト列（末尾改行を含む）からそれぞれ計算します。Consumerは元のサンプルファイルを参照しません。必要なら http://localhost:18080/received から受信内容だけを表示できます。

この画面はsovity UIではなく、今回同梱した受信確認用サーバーです。今回のHTTP PUSH手順では、sovity UIで転送状態、こちらで本体を確認しました。

## 構成と範囲

- Provider/ConsumerそれぞれにCE（Control PlaneとData Plane一体）、UI、PostgreSQL、Caddyを配置。
- Caddyが同一オリジンでUIとAPIを振り分ける。DSPパスは`/api/v1/dsp`。
- `provider-data-server` は読み取り専用サンプルのGETと、提供JSON・バイト数・SHA-256の表示を担当。Providerネットワークに接続。
- `consumer-data-server` はPOST受信と、受信JSON・バイト数・SHA-256の表示を担当。ProviderのData Planeから到達できるよう両ネットワークに接続。元のサンプルはマウントせず、直近の受信内容のみ既存の`received-data` volumeに保存。
- Dataspace認証は`sovity-mock-iam`、管理API認証は`management-iam-api-key`。キーとDBパスワードは公開デモ用の固定値。DAPS、Dataspace Portal、実運用の認証・認可は対象外。
- サーバーはEDCのchunked転送に対応。独自イメージのビルドは不要。

## 4. 環境の閉塞

```bash
docker compose ps
docker compose logs --tail 50 provider-connector consumer-connector provider-data-server consumer-data-server
docker compose down
```

`down`ではDBと受信データのvolumeを残します。同じ構成で再起動した場合、既存のデータ提供・契約を利用できます。既に`temperature-sample`を作成済みなら、同じIDで再作成せず **Data Offers** や **Contracts** から進んでください。

今回のデモのデータをすべて破棄して最初から試す場合だけ、次を実行します。

```bash
docker compose down -v
```

イメージ削除は、他の用途で使っていないことを確認して個別に行ってください。`docker system prune`等の一括削除は不要です。

## 版・ライセンス・証拠

CE/UIは16.8.1、PostgreSQLは17-alpine、Caddyは2.8、Pythonは3.13-alpineを参照し、Composeではすべて検証時のdigestも固定しています。実測結果は[evidence/verification.md](evidence/verification.md)。

構成は[sovity公式v16.8.1 local-demo-ce](https://github.com/sovity/edc-ce/tree/v16.8.1/docs/deployment-guide/goals/local-demo-ce)から変更しました。主な変更はホスト公開範囲、debug/DBポートの除去、ログレベル、データサーバー追加です。

上流のコード・成果物は主にElastic License 2.0で、一部がApache 2.0です。上流のLICENSE、NOTICE、Elastic License本文を[licenses](licenses/)に保存しています。「CEだからすべてApache 2.0」とは扱わないでください。

## Data Serverのスモークテスト

両サーバーの起動後、Bashで実行します。直近の受信データはテスト用サンプルで上書きされます。

```bash
docker compose up -d provider-data-server consumer-data-server
bash run/check-data-servers.sh
```

Content-Length/chunked形式のPOST、提供側の読み取り専用、受信側でサンプルを公開しないこと、受信バイト列と両画面のSHA-256を確認します。異なるデータを送ったときにConsumer側だけハッシュが変わることも確認します。

このテストはEDCを通らない直接のHTTP POSTです。EDC経由の受け入れ確認は、別の空のComposeプロジェクトで公開・契約・転送を実施してください。旧スクリーンショットと `evidence/verification.md` はv1の記録です。
