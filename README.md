# PAI Final Project — E-puck navigation with a k-NN learned steering policy (Webots)

Physical AI 応用1講座 最終課題の提出用リポジトリです。
Webots R2025a 上の小型二輪ロボット **E-puck** を Python で制御し、
教師あり学習（k近傍法, k-NN）が「前進／左旋回／右旋回」を判断して、
手動設定した経由地点を順番にたどり、ゴール（緑の球）へ到達します。

- 実機・追加ライブラリ不要（Python 標準ライブラリのみ）
- 走行結果（Webots 上で確認済み）: 経由地点 9/9 通過、**シミュレーション時間 63.2 s でゴール到達**（最終位置とゴールの距離 0.108 m）
- デモ動画: （YouTube URL をここに記載）

## 構成

```
worlds/ai_navigation.wbt              # ワールド（フロア 2.4 m 四方・障害物 2 個・ゴール・壁 4 面・E-puck）
controllers/ai_navigation/
  ai_navigation.py                    # Webots コントローラ（Supervisor）: 特徴量生成 → k-NN 推論 → モータ制御
  learned_policy.py                   # 純 Python の k-NN 分類器（k=3, 重み付き距離）
  training_data.json                  # 合成教師データ 6,000 例（train_model.py で再生成可能）
scripts/train_model.py                # 教師ルールから合成データを生成（seed 固定で再現可能）
scripts/evaluate_model.py             # オフライン精度検証（Webots 不要）
docs/demo_subtitles_ja.srt            # デモ動画の日本語字幕
```

## 動かし方

1. Webots R2025a をインストールし、`worlds/ai_navigation.wbt` を開く
2. Webots の Preferences → General → Python command に `python3` の絶対パスを設定（例: `/opt/homebrew/bin/python3`）
3. ▶（Run）を押す。コンソールに `[PAI] ...` のログが流れ、`[PAI] SUCCESS! Goal reached at t=63.2s` が出れば到達

教師データの再生成とオフライン検証:

```bash
python3 scripts/train_model.py
python3 scripts/evaluate_model.py
```

## AI の使い方

| 項目 | 内容 |
|---|---|
| 手法 | k近傍法（k=3）による教師あり分類。NumPy / scikit-learn 不使用 |
| 入力特徴量 | 右前方IR代表値（ps0–2 の最大, 正規化 0–1）／左前方IR代表値（ps5–7）／目標方位との差（−1〜1） |
| 出力 | `forward` / `turn_left` / `turn_right` |
| 教師データ | ルールベースの教師方策から合成した 6,000 例（`seed=20261020`） |
| オフライン精度 | クラス均等 300 例で 94.3%（forward 100/100, turn_left 89/100, turn_right 94/100） |

## 正直に書いておくこと（限界）

- 経由地点（9 点）とゴール座標は人が設定したもので、AI による経路計画ではありません。AI は各時刻の「前進／左右旋回」の局所判断を担当します。
- 位置・向きは Webots の Supervisor から取得しています（シミュレーション専用の特権的な自己位置。実機の自己位置推定ではありません）。
- 今回の走行ではIRセンサー値が常に待機値付近（65–75）で、近接障害物の回避分岐（閾値 100）は発動していません。障害物回避性能は未検証です。
- 教師データは合成データで、実走行ログからの学習ではありません。

## 参考

- Webots 公式ドキュメント Tutorial 4: https://github.com/cyberbotics/webots/blob/master/docs/guide/tutorial-4-more-about-controllers.md
- E-puck PROTO (R2025a): https://github.com/cyberbotics/webots/blob/R2025a/projects/robots/gctronic/e-puck/protos/E-puck.proto
