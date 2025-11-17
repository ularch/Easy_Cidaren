import subprocess
from proxy_manager import ProxyManager

proxy = ProxyManager()

try:
    print("🔧 正在自动配置代理...")
    proxy.enable_proxy()

    print("🚀 启动 mitmproxy...")
    mitm = subprocess.Popen([
        "mitmdump",
        "-s", "addon.py",
        "--listen-port", "8888",
        "--quiet",
        "--set", "console_eventlog_verbosity=error"
    ])

    print("📱 请打开 PC 微信并访问授权链接...")
    print("等检测到 UserToken 后程序会自动退出")

    mitm.wait()

finally:
    proxy.disable_proxy()
    print("🎉 已完成，可关闭窗口。")
