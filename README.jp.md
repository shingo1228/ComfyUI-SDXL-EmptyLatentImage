# ComfyUI-SDXL-EmptyLatentImage

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md)
[![日本語](https://img.shields.io/badge/lang-日本語-red.svg)](README.jp.md)

使用統計、設定管理機能を備えた解像度選択と空のLatent Image生成を提供する [ComfyUI](https://github.com/comfyanonymous/ComfyUI) 用拡張ノードです。<br>
<img src="misc/ss_resolution_list.jpg" alt="Node image" style="width:50%; height:auto;">

## 機能

### コア機能
- **スマート解像度選択**: JSONファイルから読み込んだ事前定義済み解像度のドロップダウン選択
- **カテゴリベース組織化**: 自動カテゴリ分類（SDXL、SD15、Custom）とプレフィックス表示 `[カテゴリ] Width x Height (アスペクト比)`
- **アスペクト比表示**: `width / height` で計算された小数点アスペクト比（精度設定可能）

### 使用統計と視覚的フィードバック
- **使用統計追跡**: 解像度の使用頻度と履歴の自動記録
- **視覚的状態インジケータ**: 解像度ラベルの末尾に表示される動的マーク:
  - ★ **お気に入り**解像度（手動マーク）
  - 🔥 **頻繁に使用**される解像度（閾値設定可能）
  - 🕒 **最近使用**した解像度（表示数設定可能）
- **永続統計**: `usage_stats.json`にタイムスタンプ付きで使用データ保存

### 高度な設定機能
- **外部設定**: `config.json`による包括的設定と環境変数オーバーライド
- **パフォーマンス最適化**: ファイル更新時刻検証付きキャッシュシステム
- **エラーハンドリング**: 堅牢なエラー処理とグレースフルデグラデーション、フォールバック機構
- **ログシステム**: 設定可能なログレベルとデバッグ情報

### アーキテクチャ改善
- **モジュラー設計**: 責任分離による専用マネージャー:
  - `ResolutionManager`: 解像度読み込みと処理
  - `UsageStatsManager`: 使用統計とお気に入り管理
  - `CacheManager`: ファイルキャッシュと検証
  - `ConfigurableLatentGenerator`: Latentテンソル生成
- **インターフェースベース**: テスト容易性のための依存注入パターン
- **型安全性**: コードベース全体での包括的型ヒント

## JSON形式
解像度ファイルは以下の構造に従ってください:
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

## プリインクルード解像度セット
- **[sdxl_resolution_set.json](sdxl_resolution_set.json)**: SDXL学習用最適解像度
- **[sd_resolution_set.json](sd_resolution_set.json)**: 標準SD1.5解像度セット

## 設定

### config.json設定
拡張機能は`config.json`による幅広い設定をサポートします。`config.json.example`を`config.json`にコピーして必要に応じてカスタマイズしてください:

```json
{
  "display_settings": {
    "show_usage_marks": true,
    "frequent_threshold": 2,
    "recent_limit": 5,
    "usage_marks": {
      "favorite": "★",
      "frequent": "🔥", 
      "recent": "🕒"
    }
  },
  "batch_settings": {
    "default_batch_size": 1,
    "max_batch_size": 64
  },
  "logging": {
    "debug": false,
    "log_level": "WARNING"
  }
}
```

### 環境変数
環境変数による設定オーバーライド:
- `SDXL_DEBUG`: デバッグログ有効化
- `SDXL_MAX_RESOLUTION`: 最大許可解像度
- `SDXL_MAX_BATCH_SIZE`: 最大バッチサイズ
- `SDXL_ENABLE_CACHE`: キャッシュ有効/無効

## 使用統計

拡張機能は以下を自動追跡します:
- **使用回数**: 各解像度の使用回数
- **タイムスタンプ**: 初回と最終使用時刻
- **お気に入り**: 手動でマークしたお気に入り解像度
- **最近の履歴**: 直近10回使用した解像度

### デバッグ使用情報
詳細統計を表示するデバッグユーティリティを実行:
```bash
python debug_usage.py
```

## インストール
1. ComfyUIをインストールしたフォルダの `custom_nodes`フォルダに移動
2. `git clone`コマンドを使用してリポジトリをクローン:
```bash
git clone https://github.com/shingo1228/ComfyUI-SDXL-EmptyLatentImage
```
3. （オプション）設定ファイルをコピーしてカスタマイズ:
```bash
cd ComfyUI-SDXL-EmptyLatentImage
cp config.json.example config.json
# config.jsonを編集して設定をカスタマイズ
```
4. ComfyUIを再起動して拡張機能をロード
