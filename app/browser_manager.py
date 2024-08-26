import requests
import json
from PyQt5.QtCore import QObject, pyqtSignal

from app.bit_api import headers, url

class BrowserManager(QObject):
    browser_list_updated = pyqtSignal()  # 用于通知UI更新浏览器列表

    def __init__(self, max_browsers):
        super().__init__()
        self.max_browsers = max_browsers
        self.available_browsers = ['ff370bf53ec049c9a02fbff4ae08002a']
        self.allocated_browsers = {}

    def create_browser(self, proxy_info=None):
        if len(self.available_browsers) < self.max_browsers:
            browser_id = self._create_new_browser(proxy_info)
            self.available_browsers.append(browser_id)
            self.browser_list_updated.emit()
            return browser_id
        else:
            return None

    def _create_new_browser(self, proxy_info=None):
        # 设置代理相关的配置信息，如果有提供代理信息的话
        proxy_type = proxy_info.get("proxyType", "noproxy") if proxy_info else "noproxy"
        host = proxy_info.get("ip", "") if proxy_info else ""
        port = proxy_info.get("port", "") if proxy_info else ""
        proxy_user_name = proxy_info.get("username", "") if proxy_info else ""

        json_data = {
            'name': 'google',  # 窗口名称
            'remark': '',  # 备注
            # 'proxyMethod': 2 if proxy_info else 0,  # 代理方式 2 自定义
            "proxyMethod": 2,
            "proxyType": "noproxy",
            # 'proxyType': proxy_type,  # 代理类型
            # 'host': host,  # 代理主机
            # 'port': port,  # 代理端口
            # 'proxyUserName': proxy_user_name,  # 代理账号
            "browserFingerPrint": {  # 指纹对象
                'coreVersion': '124'  # 内核版本
            }
        }
        res = requests.post(f"{url}/browser/update",
                            data=json.dumps(json_data), headers=headers).json()
        browser_id = res['data']['id']
        print(f"Browser created with ID: {browser_id}")
        return browser_id

    def allocate_browser(self, thread_name):
        if self.available_browsers:
            browser_id = self.available_browsers.pop(0)
            self.allocated_browsers[thread_name] = browser_id
            self.browser_list_updated.emit()
            return browser_id
        else:
            return None

    def release_browser(self, thread_name):
        if thread_name in self.allocated_browsers:
            browser_id = self.allocated_browsers.pop(thread_name)
            self.available_browsers.append(browser_id)
            self.browser_list_updated.emit()
            return browser_id
        return None

    def get_allocated_browsers(self):
        return self.allocated_browsers

    def get_available_browsers(self):
        return self.available_browsers

    def set_max_browsers(self, max_browsers):
        self.max_browsers = max_browsers
        self.browser_list_updated.emit()
