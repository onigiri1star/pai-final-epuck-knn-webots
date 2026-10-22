# Physical AI応用1 最終課題｜AIによる仮想二輪ロボットの走行制御

## 概要

Webotsシミュレーターの e-puck ロボットを、Pythonの k-NN（k近傍法）による行動分類と、**人が設計した9経由地点のルート**で走行させる課題。実物のロボットは不要。

- ロボット：Webots e-puck（二輪ロボット）
- AI：教師ルールから生成した合成例6,000件を使用した k-NN（k=3）
- AI入力：右前方・左前方の近接センサー値、次の経由地点の方角
- AI出力：前進／左旋回／右旋回
- 目標座標とウェイポイント：**手動設定**。AIによる自動経路計画ではない
- 現在位置・向き：Webots Supervisorのシミュレーション内特権情報。実機にそのまま転用できない
- 障害物：赤・青の直方体をワールド内に固定配置

## フォルダ構成

```text
PAI_Final_Code/
├── worlds/
│   └── ai_navigation.wbt
├── controllers/
│   └── ai_navigation/
│       ├── ai_navigation.py
│       ├── learned_policy.py
│       └── training_data.json
├── scripts/
│   ├── train_model.py
│   └── evaluate_model.py
├── README.md
└── .gitignore
```

## 再現手順（Mac / Webots）

1. ルートフォルダ `PAI_Final_Code` を展開。フォルダ構成は変えない。
2. Webotsで `File → Open World...` から `worlds/ai_navigation.wbt` を開く。
3. Webots `Preferences → General → Python command` に、ターミナルで `command -v python3` と入力して確認したPythonの**実際のパス**を指定。Mac環境の一例：`/opt/homebrew/bin/python3`。
4. Webotsのリセットボタンを押し、シミュレーションを再生。
5. コンソールの `[PAI] Waypoint 9/9 reached` と `[PAI] SUCCESS! Goal reached` を確認。

**互換性メモ：** 提出時の動作画面は macOS 27.0.1 / Webots R2025a Nightly Build 21/10/2026 / Python 3.14.7。このビルドは開発版であり、他のOSやWebotsバージョンで同じ走行結果になる保証はない。外部PROTO・テクスチャの取得時にネットワーク警告が出る場合がある。

## 独自の修正・工夫

1. **センサー補正：** 実行ログで障害物が近くにない場面でも近接センサーが約65〜75を示していたため、近似的なアイドル値75を引き、`(raw - 75) / 325` を0〜1に制限してAIへ渡すよう修正。
2. **経由地点9/9：** 初期の短い往路から、同じ経由地点を往復する長距離走行ルートに変更。障害物の位置は変更していない。
3. **再現性：** 学習データの生成乱数シードを固定。外部Pythonパッケージ不要。
4. **安全補助制御：** 距離センサーが設定閾値を超えた場合に旋回状態を一定時間保持する補助ロジックを追加（既存の方式を維持）。

## 実行結果と限界

利用者のMacで収録された実行画面のコンソールより、**シミュレーション時間63.2秒・経由地点9/9到達・最終距離 0.108m** の成功ログを確認。提出動画自体は66秒程度。これは単一の走行記録であり、成功率の統計ではない。

ただし、今回の走行映像では k-NN が `forward` と判定するログが中心。**AIによる障害物検知・回避の性能や頑健性を実証したものではない**。ウェイポイントは人手で設計されており、ロボットが周辺地図や経路を自動生成したわけではない。位置情報もSupervisorに依存する。

## 学習データの再生成・簡易評価

ターミナルでこのフォルダに移動して：

```bash
python3 scripts/train_model.py
python3 scripts/evaluate_model.py
```

注：`train_model.py` を実行すると `training_data.json` が再生成される。`evaluate_model.py` のスコアは**合成したテスト入力に対する教師ラベルとの一致率**で、Webotsの実走行成功率ではない。

## 提出時の注意

- GitHubは**展開済みのフォルダ構造で public リポジトリ**へ登録。ZIPファイルだけをアップロードするのは避ける。
- 公開前にコード・コミット履歴・動画・レポートから氏名、所属、メールアドレス、ユーザー名等の個人情報や秘密情報を除外。
- 動画はYouTubeへ1〜3分のMP4、最低でも「限定公開」。OmniCampusに動画URL、publicのGitHub URL、PDF説明資料を提出。
- レポートに実装範囲・工夫点と未検証事項を正直に記載。

## 提出物・関連ファイル

- デモ動画（YouTube、66秒・等速・日本語字幕）: （URL は omnicampus の提出フォームに記載）
- 説明資料 PDF: `docs/説明資料_PAI最終課題_88585.pdf`
- デモ動画の字幕: `docs/demo_subtitles_ja.srt`

## 出典・参考

- Webots公式：https://cyberbotics.com/
- Webotsプロジェクトリポジトリ：https://github.com/cyberbotics/webots
- e-puck PROTO：https://github.com/cyberbotics/webots/blob/R2025a/projects/robots/gctronic/e-puck/protos/E-puck.proto
- Tutorial 4：https://github.com/cyberbotics/webots/blob/master/docs/guide/tutorial-4-more-about-controllers.md
