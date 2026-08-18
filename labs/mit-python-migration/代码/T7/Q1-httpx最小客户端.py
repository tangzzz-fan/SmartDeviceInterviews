# T7-Q1 httpx 异步最小客户端 + mock 服务器（参考解法）
import asyncio, json, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
import httpx

class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.05)
        body = json.dumps({"ok": True, "data": self.path}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass

server = HTTPServer(("127.0.0.1", 0), MockHandler)
port = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()

def classify(exc=None, status=None):
    if isinstance(exc, httpx.TimeoutException): return "timeout"
    if status == 429: return "rate_limited"
    if status == 401: return "auth_error"
    if status and 500 <= status < 600: return "server_error"
    return "ok" if status == 200 else "unknown"

async def main():
    async with httpx.AsyncClient(
        base_url=f"http://127.0.0.1:{port}",
        timeout=1.0,
        headers={"Authorization": "Bearer test-token"},
    ) as client:
        r = await client.get("/chat/completions")
        print("成功路径:", classify(status=r.status_code), "| data =", r.json()["data"])
        try:
            await client.get("/slow", timeout=0.001)
        except httpx.TimeoutException as e:
            print("超时路径:", classify(exc=e))

asyncio.run(main())
server.shutdown()
