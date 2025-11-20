from mitmproxy import http, ctx
import os

class TokenCatcher:
    def response(self, flow: http.HTTPFlow):
        if flow.request.host != "app.vocabgo.com":
            return

        token = flow.request.headers.get("UserToken")
        if token:
            print("\n🎉 捕获到 UserToken:\n", token)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            token_file = os.path.join(script_dir, "token.txt")
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(token)
            print(f"📄 已保存到 {token_file}\n")
            ctx.master.shutdown()

addons = [TokenCatcher()]