"""
Token 捕获后端服务
负责调用 fetch_token 目录中的模块实现 token 捕获功能
"""
import os
import sys
import shutil
import subprocess
import time
import importlib.util


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
        
        try:
            # 导入 proxy_manager
            proxy_manager_path = os.path.join(self.fetch_token_path, "proxy_manager.py")
            spec = importlib.util.spec_from_file_location("proxy_manager", proxy_manager_path)
            proxy_manager_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(proxy_manager_module)
            ProxyManager = proxy_manager_module.ProxyManager
            
            self.proxy_manager = ProxyManager()
            
            # 清空 token.txt 文件
            token_file = os.path.join(self.fetch_token_path, "token.txt")
            try:
                with open(token_file, 'w', encoding='utf-8') as f:
                    f.write('')
            except Exception as e:
                if status_callback:
                    status_callback(f"清空 token.txt 失败: {e}")
            
            # 启用代理
            if status_callback:
                status_callback("正在配置系统代理...")
            self.proxy_manager.enable_proxy(host="127.0.0.1", port=8888)
            if status_callback:
                status_callback("系统代理已配置")
            
            # 检查 mitmdump 是否可用
            if not shutil.which("mitmdump"):
                raise RuntimeError("mitmdump 未找到，请先安装 mitmproxy: pip install mitmproxy")
            
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
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                startupinfo=startupinfo
            )
            
            if status_callback:
                status_callback("请打开 PC 微信并访问授权链接...")
                status_callback("等待捕获 UserToken...")
            
            # 监控 token.txt 文件
            last_modified = 0
            
            while self._is_running:
                # 检查进程是否还在运行
                if self.mitm_process.poll() is not None:
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
                                    if status_callback:
                                        status_callback("成功捕获到 UserToken!")
                                    if token_callback:
                                        token_callback(token)
                                    return token
                        except Exception as e:
                            if error_callback:
                                error_callback(f"读取 token 文件失败: {e}")
                            return None
                
                time.sleep(0.5)
                
        except Exception as e:
            if error_callback:
                error_callback(f"发生错误: {str(e)}")
            return None
        finally:
            self.cleanup(status_callback)
    
    def cleanup(self, status_callback=None):
        """清理资源"""
        try:
            if self.mitm_process and self.mitm_process.poll() is None:
                self.mitm_process.terminate()
                try:
                    self.mitm_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.mitm_process.kill()
                    self.mitm_process.wait()
                if status_callback:
                    status_callback("mitmproxy 已停止")
        except:
            pass
        
        try:
            if self.proxy_manager:
                if status_callback:
                    status_callback("正在恢复系统代理...")
                self.proxy_manager.disable_proxy()
                if status_callback:
                    status_callback("系统代理已恢复")
        except:
            pass
    
    def stop(self):
        """停止捕获"""
        self._is_running = False
        self.cleanup()
