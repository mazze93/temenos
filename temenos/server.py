"""The control plane — a small HTTP surface over the loop.

Three endpoints, all read-mostly:

    GET  /health        liveness
    POST /decide        evaluate a signal, record, return the verdict
    GET  /queue         the stratum projection (the review queue)

Stdlib `http.server` on purpose: no framework supply chain in the request path.
Temenos pairs with stratum's own Atrium for the human review UI — this server is
the programmatic surface, not the dashboard.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .cli import _signal_from
from .ledger import LedgerError
from .orchestrator import Temenos


def _handler_class(temenos: Temenos):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                return self._send(200, {"status": "ok"})
            if self.path == "/queue" or self.path.startswith("/queue"):
                try:
                    return self._send(200, temenos.ledger.projection())
                except LedgerError as e:
                    return self._send(502, {"error": str(e)})
            return self._send(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802
            if self.path != "/decide":
                return self._send(404, {"error": "not found"})
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                return self._send(400, {"error": "invalid JSON"})
            signal = _signal_from(payload)
            try:
                verdict = temenos.decide(signal)
            except Exception as e:  # noqa: BLE001 — surface, never crash the server
                return self._send(500, {"error": str(e)})
            self._send(200, verdict.to_dict())

        def log_message(self, *args):  # silence default stderr noise
            pass

    return Handler


def run(temenos: Temenos, host: str = "127.0.0.1", port: int = 8788) -> None:
    server = ThreadingHTTPServer((host, port), _handler_class(temenos))
    print(f"temenos control plane on http://{host}:{port}  (CTRL-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()