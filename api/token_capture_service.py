"""
Token 捕获后端服务
负责调用 fetch_token 目录中的模块实现 token 捕获功能
"""
import os
import sys
import socket
import shutil
import subprocess
import threading
import time
import importlib.util
from pathlib import Path
from log.log import Log

service_logger = Log("token_capture_service").logger


class TokenCaptureService:
    """Token 捕获服务"""
    
    def __init__(self, fetch_token_path):
        """
        初始化 Token 捕获服务
        
        Args:
            fetch_token_path: fetch_token 目录的绝对路径
        """
        self.fetch_token_path = fetch_token_path
        self.mitm_process = None
        self.proxy_manager = None
        self._is_running = False
        self._cleanup_lock = threading.Lock()
        self._cleaned_up = False
    
    def start_capture(self, status_callback=None, token_callback=None, error_callback=None):
        """
        开始捕获 token（同步方法，会阻塞直到捕获成功或出错）
        
        Args:
            status_callback: 状态更新回调函数 callback(message)
            token_callback: token 捕获成功回调函数 callback(token)
            error_callback: 错误回调函数 callback(error_message)
            
        Returns:
            str: 捕获到的 token，失败返回 None
        """
        self._is_running = True
        service_logger.info("开始 token 捕获流程")
        
        try:
            # 导入 proxy_manager
            proxy_manager_path = os.path.join(self.fetch_token_path, "proxy_manager.py")
            spec = importlib.util.spec_from_file_location("proxy_manager", proxy_manager_path)
            proxy_manager_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(proxy_manager_module)
            ProxyManager = proxy_manager_module.ProxyManager
            
            self.proxy_manager = ProxyManager()
            
            # 检查 mitmdump 是否可用
            if not shutil.which("mitmdump"):
                raise RuntimeError("mitmdump 未找到，请先安装 mitmproxy: pip install mitmproxy")
            
            # 检查 8888 端口是否被占用
            if self._is_port_in_use(8888):
                raise RuntimeError("端口 8888 已被占用，请关闭占用该端口的程序（如其他代理软件）后重试")
            
            # 清空 token.txt 文件
            token_file = os.path.join(self.fetch_token_path, "token.txt")
            try:
                with open(token_file, 'w', encoding='utf-8') as f:
                    f.write('')
                service_logger.info(f"已清空 token 文件: {token_file}")
            except Exception as e:
                service_logger.error(f"清空 token.txt 失败: {e}")
                if status_callback:
                    status_callback(f"清空 token.txt 失败: {e}")
            
            # 启用代理
            if status_callback:
                status_callback("正在配置系统代理...")
            service_logger.info("正在启用系统代理 127.0.0.1:8888")
            self.proxy_manager.enable_proxy(host="127.0.0.1", port=8888)
            if status_callback:
                status_callback("系统代理已配置")
            
            # 启动 mitmdump
            if status_callback:
                status_callback("正在启动 mitmproxy...")
            
            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            addon_path = os.path.join(self.fetch_token_path, "addon.py")
            self.mitm_process = subprocess.Popen(
                [
                    "mitmdump",
                    "-s", addon_path,
                    "--listen-port", "8888",
                    "--quiet",
                    "--set", "console_eventlog_verbosity=error"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo
            )
            service_logger.info(f"mitmdump 已启动, PID={self.mitm_process.pid}")
            
            # 等待 mitmproxy 证书生成并自动导入（首次运行必需）
            self._ensure_mitm_cert_ready(status_callback)
            
            if status_callback:
                status_callback("请打开 PC 微信并访问授权链接...")
                status_callback("等待捕获 UserToken...")
            
            # 监控 token.txt 文件
            last_modified = 0
            
            while True:
                # 检查是否被用户停止
                if not self._is_running:
                    service_logger.info("捕获已被用户停止")
                    return None
                
                # 检查进程是否还在运行
                if self.mitm_process.poll() is not None:
                    if self._is_running:
                        service_logger.error(f"mitmproxy 进程意外退出, exit code={self.mitm_process.returncode}")
                        if error_callback:
                            error_callback("mitmproxy 进程意外退出")
                    return None
                
                # 检查 token 文件是否有更新
                if os.path.exists(token_file):
                    current_modified = os.path.getmtime(token_file)
                    if current_modified != last_modified:
                        last_modified = current_modified
                        try:
                            with open(token_file, 'r', encoding='utf-8') as f:
                                token = f.read().strip()
                                if token:
                                    service_logger.info(f"成功捕获到 UserToken: {token[:8]}...")
                                    if status_callback:
                                        status_callback("成功捕获到 UserToken!")
                                    if token_callback:
                                        token_callback(token)
                                    return token
                        except Exception as e:
                            service_logger.error(f"读取 token 文件失败: {e}")
                            if error_callback:
                                error_callback(f"读取 token 文件失败: {e}")
                            return None
                
                time.sleep(0.5)
            
        except Exception as e:
            service_logger.error(f"捕获流程发生错误: {e}")
            if error_callback:
                error_callback(f"发生错误: {str(e)}")
            return None
        finally:
            self.cleanup(status_callback)
    
    def _is_port_in_use(self, port):
        """检测端口是否被占用"""
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                service_logger.warning(f"端口 {port} 已被占用")
                return True
        except OSError:
            return False
    
    def _ensure_mitm_cert_ready(self, status_callback=None):
        """等待 mitmproxy 首次运行生成证书并自动导入系统证书库"""
        cert_path = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.cer"
        deadline = time.time() + 15
        while time.time() < deadline:
            if cert_path.exists():
                break
            if self.mitm_process.poll() is not None:
                service_logger.error("mitmproxy 在生成证书前已退出")
                return
            time.sleep(0.5)
        
        if not cert_path.exists():
            service_logger.warning(f"等待证书生成超时: {cert_path}")
            return
        
        service_logger.info(f"mitmproxy 证书已生成: {cert_path}")
        
        # 导入证书到系统证书库（仅 Windows 支持免管理员导入）
        if sys.platform == "win32" and self.proxy_manager:
            try:
                if status_callback:
                    status_callback("正在导入 mitmproxy 证书...")
                self.proxy_manager._ensure_windows_mitm_cert()
                service_logger.info("mitmproxy 证书导入完成")
            except Exception as e:
                service_logger.error(f"导入 mitmproxy 证书失败: {e}")
        elif sys.platform != "win32":
            service_logger.info("非 Windows 系统，请手动信任 mitmproxy 证书")
    
    def cleanup(self, status_callback=None):
        """清理资源（线程安全，可重复调用，只执行一次）"""
        with self._cleanup_lock:
            if self._cleaned_up:
                return
            self._cleaned_up = True
            self._is_running = False
        
        service_logger.info("开始清理捕获资源")
        
        try:
            if self.mitm_process and self.mitm_process.poll() is None:
                service_logger.info("正在停止 mitmproxy 进程")
                self.mitm_process.terminate()
                try:
                    self.mitm_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    service_logger.warning("mitmproxy 未在 3 秒内退出，强制结束")
                    self.mitm_process.kill()
                    self.mitm_process.wait()
                service_logger.info(f"mitmproxy 已停止, exit code={self.mitm_process.returncode}")
                if status_callback:
                    status_callback("mitmproxy 已停止")
        except Exception as e:
            service_logger.error(f"停止 mitmproxy 失败: {e}")
        
        try:
            if self.proxy_manager:
                if status_callback:
                    status_callback("正在恢复系统代理...")
                service_logger.info("正在恢复系统代理")
                self.proxy_manager.disable_proxy()
                service_logger.info("系统代理已恢复")
                if status_callback:
                    status_callback("系统代理已恢复")
        except Exception as e:
            service_logger.error(f"恢复系统代理失败: {e}")
    
    def stop(self):
        """停止捕获"""
        service_logger.info("收到停止请求")
        self._is_running = False
        self.cleanup()
