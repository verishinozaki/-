import json
import os
from typing import Any, Dict, List

import requests
from openai import OpenAI


class TestCaseGenerationError(RuntimeError):
    """Raised when test case generation fails."""


class TestCaseGenerator:
    """Generate structured test cases with an LLM."""

    DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise TestCaseGenerationError(
                "OpenAI APIキーが設定されていません。環境変数 OPENAI_API_KEY をセットしてください。"
            )
        self.client = OpenAI(api_key=self.api_key)
        self.model = model or self.DEFAULT_MODEL

    def _fetch_source_text(self, source_url: str) -> str:
        """Fetch textual content from the given URL for context."""
        try:
            response = requests.get(source_url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network failure handling
            raise TestCaseGenerationError(f"一次情報源の取得に失敗しました: {exc}") from exc

        # Prefer the textual body; limit size to keep prompt concise.
        text = response.text
        if len(text) > 10_000:
            text = text[:10_000]
        return text

    def generate_test_cases(self, source_url: str, additional_context: str = "") -> List[Dict[str, Any]]:
        """Generate test cases based on the source URL and optional context."""
        if not source_url:
            raise ValueError("source_url must not be empty")

        source_text = self._fetch_source_text(source_url)

        prompt = self._build_prompt(source_url, source_text, additional_context)

        response = self.client.chat.completions.create(  # type: ignore[attr-defined]
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "あなたは熟練したQAエンジニアです。与えられた情報から手動テストケースを整理し、"
                        "人が実行・記録しやすいようにExcelの行として展開できる形式で回答してください。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            top_p=1,
            seed=42,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content  # type: ignore[index]
        if content is None:
            raise TestCaseGenerationError("LLMからの応答が空でした。")

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise TestCaseGenerationError("LLMからの応答をJSONとして解析できませんでした。") from exc

        test_cases = payload.get("test_cases")
        if not isinstance(test_cases, list) or not test_cases:
            raise TestCaseGenerationError("有効なテストケースが生成されませんでした。")

        return test_cases

    def _build_prompt(self, source_url: str, source_text: str, additional_context: str) -> str:
        sections = [
            "以下の一次情報源から手動テストケースを抽出・整備してください。",
            f"一次情報源URL: {source_url}",
            "--- 一次情報源の抜粋ここから ---",
            source_text,
            "--- 一次情報源の抜粋ここまで ---",
        ]

        if additional_context:
            sections.append("補足情報:" + additional_context)

        sections.append(
            """
必ず次のJSONスキーマに沿って回答してください。
{
  "test_cases": [
    {
      "test_id": "TC-001",
      "title": "テストケースのタイトル",
      "objective": "テスト目的",
      "preconditions": ["前提条件やテストデータ"],
      "steps": ["ステップを順序どおりに列挙"],
      "expected_results": ["期待される結果を箇条書きで"],
      "priority": "High | Medium | Low のいずれか",
      "notes": "補足事項や確認ポイント"
    }
  ]
}
JSON以外の出力や説明文を含めないでください。
可能な限り冗長さを避けつつ、テスト担当者が実行状況を記録しやすいように整理してください。
            """.strip()
        )

        return "\n\n".join(sections)
