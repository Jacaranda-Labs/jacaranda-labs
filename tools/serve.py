"""Tiny preview server for dist/ — clean URLs, correct media types, no cache."""
import http.server, socketserver, sys, os
from functools import partial

class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = super().translate_path(path)
        if not os.path.splitext(p)[1] and os.path.isdir(p):
            idx = os.path.join(p, "index.html")
            if os.path.isfile(idx):
                return idx
        return p
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()
    def log_message(self, *a):
        pass

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
handler = partial(H, directory="dist")
with socketserver.ThreadingTCPServer(("0.0.0.0", port), handler) as httpd:
    print(f"serving dist/ on http://0.0.0.0:{port}", flush=True)
    httpd.serve_forever()
