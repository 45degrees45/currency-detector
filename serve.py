"""Simple markdown-rendering HTTP server for the currency-detector project."""

import http.server
import os
import urllib.parse
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
PORT = 9999

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           max-width: 860px; margin: 60px auto; padding: 0 24px;
           color: #222; line-height: 1.7; }}
    h1, h2, h3 {{ color: #111; }}
    code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
    pre {{ background: #f4f4f4; padding: 16px; border-radius: 6px; overflow-x: auto; }}
    pre code {{ background: none; padding: 0; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px 12px; }}
    th {{ background: #f0f0f0; }}
    blockquote {{ border-left: 4px solid #ccc; margin: 0; padding-left: 16px; color: #555; }}
    a {{ color: #0969da; }}
    hr {{ border: none; border-top: 1px solid #eee; margin: 32px 0; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""

DIR_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{path}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           max-width: 860px; margin: 60px auto; padding: 0 24px; color: #222; }}
    a {{ display: block; padding: 6px 0; color: #0969da; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    h2 {{ color: #111; }}
  </style>
</head>
<body>
<h2>📁 {path}</h2>
{links}
</body>
</html>
"""


class MarkdownHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"  {self.address_string()} — {format % args}")

    def do_GET(self):
        url_path = urllib.parse.unquote(self.path.split("?")[0])
        local = ROOT / url_path.lstrip("/")

        if local.is_dir():
            self._serve_dir(local, url_path)
        elif local.suffix == ".md" and local.is_file():
            self._serve_md(local)
        elif local.is_file():
            self._serve_file(local)
        else:
            self.send_error(404, "Not found")

    def _serve_md(self, path: Path):
        text = path.read_text(encoding="utf-8")
        body = markdown.markdown(text, extensions=["fenced_code", "tables"])
        html = HTML_TEMPLATE.format(title=path.name, body=body)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _serve_dir(self, path: Path, url_path: str):
        entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
        links = []
        if url_path != "/":
            parent = str(Path(url_path).parent)
            links.append(f'<a href="{parent}">⬆ ..</a>')
        for entry in entries:
            href = url_path.rstrip("/") + "/" + entry.name
            icon = "📁" if entry.is_dir() else ("📄" if entry.suffix == ".md" else "📎")
            links.append(f'<a href="{href}">{icon} {entry.name}</a>')
        html = DIR_TEMPLATE.format(path=url_path, links="\n".join(links))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _serve_file(self, path: Path):
        data = path.read_bytes()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    os.chdir(ROOT)
    server = http.server.HTTPServer(("0.0.0.0", PORT), MarkdownHandler)
    print(f"Serving {ROOT} at http://0.0.0.0:{PORT}")
    server.serve_forever()
