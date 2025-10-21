import os

from src.utils.dependencies import ensure_dependencies

ensure_dependencies(
    {
        "flask": "Webアプリケーションを提供するために必要です。",
        "openai": "テストケース生成にLLMを利用するために必要です。",
        "pandas": "Excelファイルを整形するために必要です。",
        "requests": "一次情報源を取得するために必要です。",
        "xlsxwriter": "Excelファイルを書き出すために必要です。",
    }
)

from flask import Flask, render_template, request, send_file, flash, redirect, url_for

from src.services.test_case_generator import TestCaseGenerator
from src.utils.excel_exporter import build_excel_workbook


def create_app() -> Flask:
    app = Flask(__name__, template_folder="src/templates")
    app.secret_key = os.getenv("APP_SECRET_KEY", "change-me")

    generator = TestCaseGenerator()

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            source_url = request.form.get("source_url", "").strip()
            context = request.form.get("context", "").strip()

            if not source_url:
                flash("テスト対象のURLを入力してください。", "error")
                return redirect(url_for("index"))

            try:
                test_cases = generator.generate_test_cases(source_url, context)
                workbook = build_excel_workbook(source_url, test_cases)
            except Exception as exc:  # pylint: disable=broad-except
                flash(str(exc), "error")
                return redirect(url_for("index"))

            filename = "test_cases.xlsx"
            return send_file(
                workbook,
                as_attachment=True,
                download_name=filename,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=False)
