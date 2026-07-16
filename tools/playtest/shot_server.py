import base64
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

OUT = Path(r"E:\code\norfolk-path\docs\playtest\round-1")
OUT.mkdir(parents=True, exist_ok=True)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        name = self.path.lstrip("/").split("?")[0]
        if not re.fullmatch(r"[A-Za-z0-9._-]+\.png", name):
            self.send_response(400)
            self._cors()
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("ascii")
        b64 = body.split(",", 1)[1] if "," in body else body
        (OUT / name).write_bytes(base64.b64decode(b64))
        self.send_response(200)
        self._cors()
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


HTTPServer(("127.0.0.1", 8643), Handler).serve_forever()
