# T7-Q2 重试器：指数退避 + 抖动 + Retry-After + 预算（参考解法）
import asyncio, json, random, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import httpx

calls = {"n": 0}
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        calls["n"] += 1
        if calls["n"] <= 2:
            body = json.dumps({"error": "rate limited"}).encode()
            self.send_response(429)
            self.send_header("Retry-After", "0.01")
        else:
            body = json.dumps({"ok": True}).encode()
            self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass

server = HTTPServer(("127.0.0.1", 0), H)
port = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()

class RetryableError(Exception):
    def __init__(self, kind, retry_after=None):
        super().__init__(kind); self.kind = kind; self.retry_after = retry_after

RETRYABLE = {"rate_limited", "server_error", "timeout"}

def classify(status):
    if status == 429: return "rate_limited"
    if 500 <= status < 600: return "server_error"
    return "ok"

async def call_once(client):
    r = await client.get("/api")
    kind = classify(r.status_code)
    if kind != "ok":
        ra = float(r.headers.get("Retry-After", "0")) if kind == "rate_limited" else None
        raise RetryableError(kind, ra)
    return r.json()

def retry_async(factory, *, max_attempts=5, base=0.05, jitter=0.1):
    async def run():
        last = None
        for attempt in range(max_attempts):
            try:
                return await factory()
            except RetryableError as e:
                last = e
                if e.kind not in RETRYABLE:
                    raise
                delay = min(1.0, base * 2 ** attempt) * (1 + random.uniform(0, jitter))
                if e.retry_after:
                    delay = max(delay, e.retry_after)
                print(f"第{attempt+1}次失败({e.kind}) 等待 {delay:.3f}s")
                await asyncio.sleep(delay)
        raise last
    return run()

async def main():
    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}", timeout=2.0) as client:
        async def factory():
            return await call_once(client)
        result = await retry_async(factory, max_attempts=5)
        print("最终结果:", result, "| 总请求次数:", calls["n"])

asyncio.run(main())
server.shutdown()
