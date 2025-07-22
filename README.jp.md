# ComfyUI-SDXL-EmptyLatentImage

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md)
[![日本語](https://img.shields.io/badge/lang-日本語-red.svg)](README.jp.md)

使用統計機能付きの解像度選択を提供する、シンプル化されたComfyUI拡張ノードです。<br>
<img src="misc/ss_resolution_list.jpg" alt="ノード画像" style="width:300px; height:auto;">

## 機能

### 基本機能
- **スマート解像度選択**: JSONファイルから読み込まれた事前定義済み解像度から選択
- **カテゴリ別整理**: カスタム → SDXL → SD15 の優先順位で自動分類
- **解像度表示**: `[カテゴリ] 横幅 x 縦幅 (アスペクト比)` 形式で小数点アスペクト比を表示

### 使用統計・視覚的フィードバック
- **使用状況追跡**: 解像度使用頻度の自動記録
- **視覚的インジケーター**: 解像度ラベル後に動的マークを表示:
  - ★ **お気に入り** 解像度（手動登録）
  - 🔥 **頻繁使用** 解像度（3回以上使用）
  - 🕒 **最近使用** 解像度（直近5つ）

### シンプル設定
- **環境変数**: `SDXL_*` 環境変数で設定を上書き
- **基本JSON設定**: 必要最低限の設定のみの簡単な `config.json`

## 解像度表示順序

解像度は以下の優先順位で表示されます：
1. **カスタム** 解像度（ユーザー定義）
2. **SDXL** 解像度
3. **SD15** 解像度

各カテゴリ内では、アスペクト比順（縦長 → 正方形 → 横長）でソートされます。

## JSON形式

解像度ファイルは以下の構造に従ってください：
```json
[
    {
        "width": 1024, "height": 1024
    },
    {
        "width": 832, "height": 1152
    },
    {
        "width": 1152, "height": 832
    }
]
```

## 事前含まれる解像度セット
- **[sdxl_resolution_set.json](sdxl_resolution_set.json)**: 最適なSDXL学習解像度
- **[sd_resolution_set.json](sd_resolution_set.json)**: 標準SD1.5解像度セット
- **custom_resolution_set.json**: カスタム解像度（独自の解像度を追加するためにこのファイルを作成）

## 設定

### 環境変数
デフォルト設定を上書き：
- `SDXL_MAX_RESOLUTION`: 最大許可解像度（デフォルト: 8192）
- `SDXL_MIN_RESOLUTION`: 最小許可解像度（デフォルト: 64）
- `SDXL_MAX_BATCH_SIZE`: 最大バッチサイズ（デフォルト: 64）
- `SDXL_TRACK_USAGE`: 使用統計の有効/無効（デフォルト: true）

### config.json (オプション)
永続的な設定のため `config.json` を作成または変更：
```json
{
  "max_resolution": 8192,
  "min_resolution": 64,
  "max_batch_size": 64,
  "track_usage": true
}
```

## お気に入り解像度の管理

### お気に入りの追加
解像度をお気に入りとしてマークするには、`usage_stats.json` を手動編集：

```json
{
  "favorites": [
    "[CUSTOM] 1024 x 1024 (1.00)",
    "[SDXL] 832 x 1216 (0.68)"
  ],
  "usage_count": {},
  "recent": []
}
```

### 使用統計
拡張機能は以下を自動追跡します：
- **使用回数**: 各解像度の使用回数
- **最近の履歴**: 直近5つの使用解像度
- **お気に入り**: 手動マークされたお気に入り解像度

使用後の `usage_stats.json` 例：
```json
{
  "favorites": [
    "[CUSTOM] 1024 x 1024 (1.00)"
  ],
  "usage_count": {
    "[SDXL] 1024 x 1024 (1.00)": 5,
    "[SDXL] 832 x 1216 (0.68)": 2
  },
  "recent": [
    "[SDXL] 832 x 1216 (0.68)",
    "[SDXL] 1024 x 1024 (1.00)"
  ]
}
```

## インストール

1. ComfyUIがインストールされている `custom_nodes` フォルダに移動
2. リポジトリをクローン：
```bash
git clone https://github.com/shingo1228/ComfyUI-SDXL-EmptyLatentImage
```
3. (オプション) `custom_resolution_set.json` を作成してカスタム解像度を追加：
```bash
cd ComfyUI-SDXL-EmptyLatentImage
# カスタム解像度ファイルを作成
echo '[{"width": 1024, "height": 1024}, {"width": 512, "height": 768}]' > custom_resolution_set.json
```
4. (オプション) `config.json` で設定をカスタマイズ
5. 拡張機能を読み込むためにComfyUIを再起動

## アーキテクチャ

この拡張機能はシンプル化された単一クラス設計を使用：
- **単一ファイル**: すべての機能が `sdxl_empty_latent.py` に含まれる
- **シンプルキャッシュ**: 基本的なファイル更新時刻チェック
- **最小限設定**: 環境変数 + オプションのJSON設定
- **必要機能のみ**: 解像度選択と使用統計の核となる機能に集中

簡略化されたアーキテクチャにより、ComfyUIワークフローでの解像度管理に必要なすべての機能を提供しながら、コードの理解、変更、保守を容易にしています。