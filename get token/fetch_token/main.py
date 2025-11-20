import subprocess
import sys
from proxy_manager import ProxyManager

proxy = ProxyManager()

try:
    print("🔧 正在自动配置代理...")
    proxy.enable_proxy()

    print("🚀 启动 mitmproxy...")
    
    # 在 Windows 上隐藏子进程窗口和错误输出
    startupinfo = None
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    mitm = subprocess.Popen(
        [
            "mitmdump",
            "-s", "addon.py",
            "--listen-port", "8888",
            "--quiet",
            "--set", "console_eventlog_verbosity=error"
        ],
        stderr=subprocess.DEVNULL,  # 隐藏 asyncio 异常
        startupinfo=startupinfo
    )

    print("📱 请打开 PC 微信并访问授权链接...")
    print("等检测到 UserToken 后程序会自动退出\n")

    mitm.wait()

except KeyboardInterrupt:
    print("\n⚠️ 用户中断")
    if 'mitm' in locals():
        mitm.terminate()
        mitm.wait(timeout=3)

finally:
    proxy.disable_proxy()
    print("🎉 已完成，可关闭窗口。")
