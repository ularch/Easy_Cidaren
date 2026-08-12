from mitmproxy import http
import os
from log.log import Log

# init log
addon_logger = Log("token_addon")

class TokenCatcher:
    def response(self, flow: http.HTTPFlow):
        if flow.request.host != "app.vocabgo.com":
            return

        token = flow.request.headers.get("UserToken")
        if token:
            addon_logger.logger.info(f"捕获到 UserToken: {token}")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            token_file = os.path.join(script_dir, "token.txt")
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(token)
            addon_logger.logger.info(f"已保存到 {token_file}")

addons = [TokenCatcher()]
