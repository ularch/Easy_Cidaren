import os
import subprocess
import sys
from proxy_manager import ProxyManager
import shutil
from log.log import Log

# init log
main_logger = Log("fetch_token_main")

proxy = ProxyManager()
main_logger.logger.info("")

try:
    main_logger.logger.info("正在自动配置代理...")
    proxy.enable_proxy()

    main_logger.logger.info("启动 mitmproxy...")

    # 检查 mitmdump 是否可用（支持当前 python 环境、本地 venv、系统 PATH 及 python 模块兜底）
    def _find_mitmdump():
        cand = os.path.join(os.path.dirname(sys.executable), "mitmdump" + (".exe" if sys.platform == "win32" else ""))
        if os.path.exists(cand) and os.access(cand, os.X_OK):
            return [cand]
        which_p = shutil.which("mitmdump")
        if which_p:
            return [which_p]
        root_venv = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".venv", "Scripts" if sys.platform == "win32" else "bin", "mitmdump" + (".exe" if sys.platform == "win32" else "")))
        if os.path.exists(root_venv) and os.access(root_venv, os.X_OK):
            return [root_venv]
        try:
            import mitmproxy
            return [sys.executable, "-c", "import sys; from mitmproxy.tools.main import mitmdump; sys.exit(mitmdump())"]
        except ImportError:
            return None

    mitmdump_cmd = _find_mitmdump()
    if not mitmdump_cmd:
        raise RuntimeError("mitmdump 未找到，请先安装 mitmproxy: pip install mitmproxy")

    # 在 Windows 上隐藏子进程窗口和错误输出
    startupinfo = None
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    mitm = subprocess.Popen(
        mitmdump_cmd + [
            "-s", "addon.py",
            "--listen-port", "8888",
            "--quiet",
            "--set", "console_eventlog_verbosity=error"
        ],
        stderr=subprocess.DEVNULL,  # 隐藏 asyncio 异常
        startupinfo=startupinfo
    )

    main_logger.logger.info("请打开 PC 微信并访问授权链接...")
    main_logger.logger.info("程序将持续运行以监听 UserToken 更新，按 Ctrl+C 可退出程序\n")

    # 持续运行，直到用户手动中断
    try:
        mitm.wait()
    except KeyboardInterrupt:
        pass

except KeyboardInterrupt:
    main_logger.logger.warning("用户中断")
    if 'mitm' in locals():
        mitm.terminate()
        try:
            mitm.wait(timeout=3)
        except subprocess.TimeoutExpired:
            mitm.kill()
            mitm.wait()

finally:
    proxy.disable_proxy()
    main_logger.logger.info("已完成，可关闭窗口。")
