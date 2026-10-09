# Fieldcheck

[English](README.md) | [日本語](README.ja.md)

**バージョン付きAIワークフローの実行記録が、守るべき条件を満たしているか**を検査する、独立した小さなPython製CLIです。Switchyardの架空データを使った実行記録を、Node.js、起動中のサーバー、AIモデル、APIキー、外部のPythonパッケージなしで検証できます。

決められたテストデータの動作を検査するもので、**実際のAIモデルの品質評価ではありません**。同梱する実行記録はすべてオリジナルの架空データです。

## 実行方法

このディレクトリで、Python 3.11以降を使用してください。

```sh
python3 -m fieldcheck fixtures/baseline.jsonl --output report.json
python3 -m unittest discover -s tests -v
python3 -m compileall -q fieldcheck tests fixtures
```

ベースラインには、実際に出力した9件の実行記録と、それぞれの期待結果を同梱しています。想定された障害ケースも含め、9件すべてが期待結果と一致するはずです。一方、次の4件は検出を確かめるために意図的に壊しています。

```sh
python3 -m fieldcheck fixtures/negative-controls.jsonl
# 終了コード1：素材の改変、古い承認、存在しない素材への参照、期待結果の不一致
```

終了コードは、**0** が全件合格、**1** が条件または期待結果の不一致、**2** が不正な入力、ケースID・JSONキーの重複、サイズ・深さ制限超過、レポート書き込みエラーです。入力は全体16 MiB、1行1 MiB、JSONの深さ64階層までに制限しています。入力ファイルをレポートで上書きすることはできません。入力の内容からコマンドやモデル処理を実行することもありません。

## 検査する内容

架空データ用v1契約の厳密な形式、素材そのもののSHA-256ハッシュ、素材一覧のダイジェスト、プロバイダー切り替えの上限と拒否時の停止、レビュー指摘が参照する素材ID、承認と現在の入力の一致、監査記録の連番と納品前の承認、納品ファイル一覧のハッシュ、障害状態の整合性、期待結果を確認します。結果には、各検査の名前と実行記録に含まれるローカル処理時間を出力します。

`report.json` は構造化された検査結果です。ダッシュボードや本番の評価サービスではありません。時間の中央値は、入力されたローカル実行記録をまとめたものです。同じ実行の途中経過が複数のケースに含まれるため、独立した実験の集計ではありません。AIプロバイダーの速度、品質、費用の実績として使わないでください。

## Switchyardから新しい記録を出力する

```sh
cd ../switchyard
npm run demo -- ../fieldcheck/fixtures/baseline.jsonl
cd ../fieldcheck
python3 fixtures/make_negative_controls.py
python3 -m fieldcheck fixtures/baseline.jsonl
```

同梱済みのテストデータであれば、Switchyardが手元になくてもFieldcheck単独で実行できます。[データの由来](fixtures/PROVENANCE.md)に生成方法を、[データ契約](docs/contract.md)にハッシュの計算方法と制限を記載しています。これらの詳細資料は英語です。

## 確認済みの結果

現在のローカル検証では、Python 3.14.8でテスト37件が成功し、ベースライン9件すべてを受け入れ、意図的に壊した4件すべてを検出しました。RuffによるLint・フォーマット確認と、厳格なmypy型チェックも通っています。[CIワークフロー](https://github.com/domizo/fieldcheck/actions/workflows/ci.yml)はUbuntu上のPython 3.11・3.14を検査します。[検証記録](docs/verification.md)には、37件のCI成功と、契約検証に追加した回帰テストを記載しています。[依存関係・開発用チェック](DEPENDENCIES.md)と[日本語の技術解説](docs/walkthrough.ja.md)も参照してください。

## 未実装の範囲と制約

実モデルの採点、統計的な品質推定、人による評価ラベル付け、AIプロバイダー呼び出し、汎用のJSON Schema解釈、署名付き監査記録の検証、ダウンロードした納品ファイルの直接読み取り、クラウドへのレポート保存は実装していません。

Fieldcheckが検査するのは、出力された**納品ファイル一覧とハッシュ**です。実際の納品ファイルの内容は、Switchyardの結合テストとダウンロードAPIが検証します。

形式が正しい応答であっても、内容が事実として正しいことを証明するものではありません。[MITライセンス](LICENSE)を適用しています。依存パッケージには、それぞれのライセンスが適用されます。
