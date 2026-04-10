from datetime import datetime
from html import escape
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

from app.config import REPORT_DIR
from app.utils.state_utils import append_agent_message


def build_reference_markdown(state, draft: str) -> str:
    if "## REFERENCE" in draft:
        return draft

    ref_lines = []
    ref_lines.append("\n## REFERENCE\n")
    ref_lines.append("\n[PDF]\n")

    seen_pdf = set()
    for item in state["retrieval_data"].get("rag_raw_chunks", []):
        source_file = item.get("source_file", "")
        if source_file and source_file not in seen_pdf:
            seen_pdf.add(source_file)
            ref_lines.append(f"- {source_file}\n")

    ref_lines.append("\n[WEB]\n")
    seen_web = set()
    for item in state["retrieval_data"].get("web_raw_results", []):
        url = item.get("url", "")
        if url and url not in seen_web:
            seen_web.add(url)
            ref_lines.append(f"- {url}\n")

    return draft + "\n" + "".join(ref_lines)


def build_html_from_markdown(markdown_text: str) -> str:
    html_body = markdown.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "nl2br"]
    )

    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="utf-8" />
        <title>반도체 R&D 전략 보고서</title>
        <style>
            @page {{
                size: A4;
                margin: 20mm 18mm 20mm 18mm;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo",
                             "Malgun Gothic", "Noto Sans CJK KR", "NanumGothic",
                             sans-serif;
                color: #111;
                line-height: 1.65;
                font-size: 12px;
                word-break: keep-all;
            }}

            h1 {{
                font-size: 24px;
                margin: 0 0 18px 0;
                padding-bottom: 10px;
                border-bottom: 2px solid #222;
            }}

            h2 {{
                font-size: 18px;
                margin-top: 28px;
                margin-bottom: 10px;
                padding-bottom: 6px;
                border-bottom: 1px solid #bbb;
            }}

            h3 {{
                font-size: 14px;
                margin-top: 20px;
                margin-bottom: 8px;
            }}

            p {{
                margin: 8px 0;
            }}

            ul {{
                margin: 8px 0 8px 20px;
                padding: 0;
            }}

            li {{
                margin: 4px 0;
            }}

            code {{
                font-family: SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                background: #f4f4f4;
                padding: 2px 4px;
                border-radius: 4px;
                font-size: 11px;
            }}

            pre {{
                background: #f7f7f7;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 12px;
                overflow-x: auto;
                white-space: pre-wrap;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 12px 0;
                font-size: 11px;
            }}

            th, td {{
                border: 1px solid #ccc;
                padding: 8px;
                text-align: left;
                vertical-align: top;
            }}

            th {{
                background: #f2f2f2;
            }}

            .meta-note {{
                margin-top: 24px;
                font-size: 11px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """


def formatter(state):
    print("\n[Formatting Node - Playwright] started")

    draft = state["draft_work"]["current_draft"]

    if state["supervisor_ctrl"]["missing_info_log"]:
        fallback_section = "\n\n## 추가 메모\n"
        fallback_section += "- 정보 부족 또는 추정 보류 항목\n"
        for item in state["supervisor_ctrl"]["missing_info_log"]:
            fallback_section += f"- {item}\n"
        draft += fallback_section

    draft = build_reference_markdown(state, draft)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = REPORT_DIR / f"technology_strategy_report_{ts}.md"
    html_path = REPORT_DIR / f"technology_strategy_report_{ts}.html"
    pdf_path = REPORT_DIR / f"technology_strategy_report_{ts}.pdf"

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md_path.write_text(draft, encoding="utf-8")

    html = build_html_from_markdown(draft)
    html_path.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={
                "top": "20mm",
                "right": "18mm",
                "bottom": "20mm",
                "left": "18mm",
            },
        )
        browser.close()

    state["global_info"]["final_report_markdown"] = draft
    state["global_info"]["final_report_pdf_path"] = str(pdf_path)
    state["global_info"]["workflow_status"] = "FORMATTED"
    append_agent_message(
        state,
        "formatter",
        f"saved report artifacts to markdown={md_path.name}, html={html_path.name}, pdf={pdf_path.name}",
    )

    print(f"[Formatting Node] markdown saved -> {md_path}")
    print(f"[Formatting Node] html saved -> {html_path}")
    print(f"[Formatting Node] pdf saved -> {pdf_path}")

    return state
