# LLM Test Case Generator

テスト対象となる一次情報源（URL など）を入力すると、LLM が手動テストケースを生成し、視認性の高い Excel ファイルとしてダウンロードできるツールです。

## セットアップ

1. 依存関係をインストールします。

   ```bash
   pip install -r requirements.txt
   ```

2. OpenAI API キーを環境変数に設定します。

   ```bash
   export OPENAI_API_KEY="sk-..."
   export OPENAI_MODEL="gpt-5"  # 任意、未設定の場合は gpt-5
   ```

3. アプリケーションを起動します。

   ```bash
   python app.py
   ```

4. ブラウザで `http://localhost:8000` を開き、一次情報源の URL と補足情報（任意）を入力して Excel を生成します。

## 仕組み

- 入力された URL からコンテンツを取得して LLM に渡し、テストケースを JSON 形式で生成します。
- 生成されたテストケースは、テスト担当者が実行・記録しやすいように以下の項目で構成された Excel ファイルに整形されます。
  - Test ID
  - Title
  - Objective
  - Preconditions / Test Data
  - Steps
  - Expected Results
  - Priority
  - Notes
  - Status（記入欄のみ）
  - Assignee（記入欄のみ）
- Excel には Summary シートも含まれ、テスト対象の URL と生成されたテストケース数を記載します。
- LLM へのプロンプトは `temperature=0`、`seed=42`、`response_format=json` で固定しているため、出力結果の揺らぎを最小限に抑えています。

## 注意事項

- 一部の Web サイトはクロールが禁止されている場合があります。必要に応じて開発チームと調整してください。
- OpenAI API 利用時の料金にご注意ください。
- 生成結果は必ず人間がレビューし、必要に応じて調整してください。
