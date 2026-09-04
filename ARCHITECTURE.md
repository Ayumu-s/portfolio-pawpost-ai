# PawPost AI Architecture

## 処理の流れ

```text
Next.js form
  └─ multipart/form-data
      └─ FastAPI POST /api/posts/generate
          ├─ content type / size validation
          ├─ image_normalizer (HEIC/HEIF → EXIF-aware JPEG in memory)
          ├─ PostGenerator
          │   ├─ AIManager → MockProvider → fixed image description
          │   └─ AIManager → MockProvider → deterministic caption + hashtags
          └─ required hashtag normalization / re-attachment
              └─ JSON response → editable Instagram-style preview
```

## MockProvider境界

`backend/app/services/ai/base.py` の `AIProvider` が、画像解析と文章生成の共通インターフェースです。公開版では `MockProvider` だけを登録し、APIキー・外部ネットワーク・AI SDKなしで同じ入出力の流れを確認できます。

実AIを追加する場合も、APIルートや `PostGenerator` ではなく、Provider実装と `AIManager` の登録を変更する構成です。現在の公開コピーには実AI用コードと依存関係を含めていません。

## 情報の流れ

1. 画像・複数画像・動画を受け付け、形式とサイズを検証する
2. MockProviderが入力メディアを受け取ったことを示す固定説明を返す
3. プロフィール、入力メモ、カテゴリ、テンプレートをもとに固定の投稿案を返す
4. 必須ハッシュタグを正規化し、投稿案を編集可能なプレビューへ渡す

## データと秘密情報

プロフィールと生成結果はFrontendのstateに保持します。ユーザーが保存した投稿テンプレートだけはBackendのSQLite（`backend/data/pawpost.db`）へ保存します。APIキーや個人の画像はリポジトリへ含めません。

## MVPの対象外

Instagram API、ログイン、実投稿、予約投稿、アカウント管理、決済、分析は実装していません。Mockの画像説明は実画像の内容を認識せず、投稿案は公開デモ用の固定ロジックで生成します。
