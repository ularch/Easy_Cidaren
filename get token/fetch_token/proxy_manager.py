import platform
import subprocess
import re
import os
from pathlib import Path
if platform.system() == "Windows":
    import winreg

class ProxyManager:
    def __init__(self):
        self.os = platform.system()
        self.original_settings = {}  # 保存原始代理设置

    def _get_network_services(self):
        """获取 macOS 网络服务列表"""
        output = subprocess.check_output(
            ["networksetup", "-listallnetworkservices"],
            text=True
        )
        return [s for s in output.splitlines()[1:] if not s.startswith("*")]

    def _get_proxy_info(self, service):
        """获取指定服务的当前代理设置"""
        try:
            # 获取 HTTP 代理
            web_output = subprocess.check_output(
                ["networksetup", "-getwebproxy", service],
                text=True
            )
            # 获取 HTTPS 代理
            secure_output = subprocess.check_output(
                ["networksetup", "-getsecurewebproxy", service],
                text=True
            )
            
            web_enabled = "Enabled: Yes" in web_output
            secure_enabled = "Enabled: Yes" in secure_output
            
            web_host = re.search(r'Server: (.+)', web_output)
            web_port = re.search(r'Port: (\d+)', web_output)
            secure_host = re.search(r'Server: (.+)', secure_output)
            secure_port = re.search(r'Port: (\d+)', secure_output)
            
            return {
                'web_enabled': web_enabled,
                'web_host': web_host.group(1).strip() if web_host else '',
                'web_port': web_port.group(1) if web_port else '',
                'secure_enabled': secure_enabled,
                'secure_host': secure_host.group(1).strip() if secure_host else '',
                'secure_port': secure_port.group(1) if secure_port else '',
            }
        except:
            return None

    def _get_linux_proxy_env(self):
        """获取 Linux 当前的代理环境变量"""
        return {
            'http_proxy': os.environ.get('http_proxy', ''),
            'https_proxy': os.environ.get('https_proxy', ''),
            'HTTP_PROXY': os.environ.get('HTTP_PROXY', ''),
            'HTTPS_PROXY': os.environ.get('HTTPS_PROXY', ''),
        }

    def _get_windows_proxy_settings(self):
        """获取 Windows 当前的代理设置"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0,
                winreg.KEY_READ
            )
            
            try:
                proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            except FileNotFoundError:
                proxy_enable = 0
            
            try:
                proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
            except FileNotFoundError:
                proxy_server = ""
            
            try:
                proxy_override, _ = winreg.QueryValueEx(key, "ProxyOverride")
            except FileNotFoundError:
                proxy_override = ""
            
            winreg.CloseKey(key)
            
            return {
                'enabled': bool(proxy_enable),
                'server': proxy_server,
                'override': proxy_override
            }
        except Exception as e:
            print(f"⚠️ 读取代理设置失败: {e}")
            return None

    def _set_windows_proxy_settings(self, enabled, server="", override="<local>"):
        """设置 Windows 代理"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0,
                winreg.KEY_WRITE
            )
            
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1 if enabled else 0)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, server)
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, override)
            
            winreg.CloseKey(key)
            
            # 通知系统代理设置已更改
            import ctypes
            INTERNET_OPTION_SETTINGS_CHANGED = 39
            INTERNET_OPTION_REFRESH = 37
            internet_set_option = ctypes.windll.Wininet.InternetSetOptionW
            internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
            internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)
            
            return True
        except Exception as e:
            print(f"⚠️ 设置代理失败: {e}")
            return False

    def _windows_store_has_cert(self, store_name):
        """检测指定证书存储是否已有 mitmproxy 证书"""
        try:
            ps_cmd = (
                f"(Get-ChildItem -Path Cert:\\CurrentUser\\{store_name} "
                f"| Where-Object {{$_.Subject -like '*mitmproxy*'}} | Measure).Count"
            )
            result = subprocess.run(
                ["powershell", "-NoLogo", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            return int(result.stdout.strip() or "0") > 0
        except Exception:
            return False

    def _ensure_windows_mitm_cert(self):
        """自动导入 mitmproxy 证书到 Windows 系统"""
        cert_path = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.cer"
        if not cert_path.exists():
            print("⚠️ 未找到 mitmproxy 证书，将在首次运行 mitmdump 时自动生成")
            return

        for store in ("Root", "CA"):
            if self._windows_store_has_cert(store):
                continue
            try:
                subprocess.run(
                    ["certutil", "-addstore", "-f", "-user", store, str(cert_path)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                    timeout=10
                )
                print(f"🔐 已将 mitmproxy 证书导入 CurrentUser\\{store}")
            except subprocess.CalledProcessError:
                print(f"⚠️ 导入证书到 {store} 失败，可手动执行：certutil -addstore -f -user {store} \"{cert_path}\"")
            except Exception as e:
                print(f"⚠️ 导入证书时出错: {e}")

    def enable_proxy(self, host="127.0.0.1", port=8888):
        print("🔧 启用系统代理...")

        if self.os == "Darwin":
            services = self._get_network_services()
            
            # 保存当前代理设置
            for service in services:
                self.original_settings[service] = self._get_proxy_info(service)
            
            # 设置新代理
            for service in services:
                subprocess.run(
                    ["networksetup", "-setwebproxy", service, host, str(port)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                )
                subprocess.run(
                    ["networksetup", "-setsecurewebproxy", service, host, str(port)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                )

        elif self.os == "Windows":
            # 先确保证书已导入
            self._ensure_windows_mitm_cert()
            
            # 保存当前代理设置
            self.original_settings['windows'] = self._get_windows_proxy_settings()
            
            # 设置新代理
            proxy_server = f"{host}:{port}"
            self._set_windows_proxy_settings(
                enabled=True,
                server=proxy_server,
                override="<local>"
            )
            print(f"🔧 已设置系统代理: {proxy_server}")

        elif self.os == "Linux":
            # 保存当前环境变量
            self.original_settings['linux_env'] = self._get_linux_proxy_env()
            
            # 设置新的代理环境变量
            proxy_url = f"http://{host}:{port}"
            os.environ['http_proxy'] = proxy_url
            os.environ['https_proxy'] = proxy_url
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
            
            print(f"🔧 已设置代理环境变量: {proxy_url}")

    def disable_proxy(self):
        print("🔧 恢复原代理设置...")

        if self.os == "Darwin":
            for service, settings in self.original_settings.items():
                if settings is None:
                    continue
                
                # 恢复 HTTP 代理 - 关键：只看 enabled 状态
                if settings['web_enabled']:
                    # 原来是启用的，恢复原配置
                    if settings['web_host'] and settings['web_port']:
                        subprocess.run(
                            ["networksetup", "-setwebproxy", service, 
                             settings['web_host'], settings['web_port']],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                        )
                else:
                    # 原来是关闭的，确保关闭
                    subprocess.run(
                        ["networksetup", "-setwebproxystate", service, "off"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                    )
                
                # 恢复 HTTPS 代理 - 关键：只看 enabled 状态
                if settings['secure_enabled']:
                    # 原来是启用的，恢复原配置
                    if settings['secure_host'] and settings['secure_port']:
                        subprocess.run(
                            ["networksetup", "-setsecurewebproxy", service,
                             settings['secure_host'], settings['secure_port']],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                        )
                else:
                    # 原来是关闭的，确保关闭
                    subprocess.run(
                        ["networksetup", "-setsecurewebproxystate", service, "off"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                    )

        elif self.os == "Windows":
            if 'windows' in self.original_settings:
                settings = self.original_settings['windows']
                
                if settings is None:
                    # 如果读取失败，直接关闭代理
                    self._set_windows_proxy_settings(enabled=False, server="")
                else:
                    # 恢复原始设置
                    self._set_windows_proxy_settings(
                        enabled=settings['enabled'],
                        server=settings['server'],
                        override=settings['override']
                    )
                
                print("🔧 已恢复原始代理设置")

        elif self.os == "Linux":
            if 'linux_env' in self.original_settings:
                original_env = self.original_settings['linux_env']
                
                # 恢复或删除环境变量
                for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
                    if original_env[key]:
                        # 原来有值，恢复它
                        os.environ[key] = original_env[key]
                    else:
                        # 原来没有值，删除它
                        if key in os.environ:
                            del os.environ[key]
                
                print("🔧 已恢复原始代理环境变量")

        print("🟢 代理已恢复")