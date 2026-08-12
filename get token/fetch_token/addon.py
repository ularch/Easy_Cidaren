from mitmproxy import http
import os
import logging
from logging.handlers import RotatingFileHandler

script_dir = os.path.dirname(os.path.abspath(__file__))

# 独立日志文件，避免依赖主程序的 log.log（防止 mitmdump 进程污染主日志并引入 PyQt6 依赖）
capture_logger = logging.getLogger("token_addon")
capture_logger.setLevel(logging.INFO)
capture_logger.propagate = False
if not capture_logger.handlers:
    handler = RotatingFileHandler(
        os.path.join(script_dir, "capture.log"),
        maxBytes=1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(name)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    capture_logger.addHandler(handler)

class TokenCatcher:
    def response(self, flow: http.HTTPFlow):
        if flow.request.host != "app.vocabgo.com":
            return

        token = flow.request.headers.get("UserToken")
        if token:
            capture_logger.info(f"捕获到 UserToken: {token}")
            token_file = os.path.join(script_dir, "token.txt")
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(token)
            capture_logger.info(f"已保存到 {token_file}")

addons = [TokenCatcher()]
