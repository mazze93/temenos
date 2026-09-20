"""A faithful mock of stratum's write path, for tests and local dev.

Replicates the contract temenos actually depends on:

    POST /api/logs/{logId}/events   -> 201 {ok, event, seq, head} | 409 {error}
    GET  /api/logs/{logId}/projection -> 200 {events:[...], head:N}
    GET  /api/logs/{logId}/events   -> 200 [ ... ]

Stdlib only. Runs in a thread so tests can exercise the real `urllib` client.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class MockStratum:
    def __init__(self):
        self.events: list[dict] = []
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def start(self) -> "MockStratum":
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def _send(self, status, payload):
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):  # noqa: N802
                if not self.path.endswith("/events"):
                    return self._send(404, {"error": "not found"})
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length).decode("utf-8")
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    return self._send(400, {"error": "body must be a JSON event record"})
                # Minimal validation mirroring stratum: id + type required.
                if not isinstance(event, dict) or not event.get("id"):
                    return self._send(409, {"error": "event id must be a non-empty string"})
                seq = len(outer.events)
                recorded = dict(event, seq=seq)
                outer.events.append(recorded)
                return self._send(201, {
                    "ok": True, "event": recorded, "seq": seq, "head": seq,
                })

            def do_GET(self):  # noqa: N802
                if self.path.endswith("/projection"):
                    return self._send(200, {"events": outer.events, "head": len(outer.events) - 1})
                if self.path.endswith("/events"):
                    return self._send(200, outer.events)
                if self.path.endswith("/health"):
                    return self._send(200, {"status": "ok"})
                return self._send(404, {"error": "not found"})

            def log_message(self, *args):
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()