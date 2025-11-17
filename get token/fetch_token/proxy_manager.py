import platform
import subprocess
import re
import os

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
            subprocess.run(
                ["netsh", "winhttp", "set", "proxy", f"{host}:{port}"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
            )

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
            subprocess.run(
                ["netsh", "winhttp", "reset", "proxy"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
            )

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