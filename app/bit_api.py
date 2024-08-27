import requests
import json
import time

# 官方文档地址
# https://doc2.bitbrowser.cn/jiekou/ben-di-fu-wu-zhi-nan.html

# 此demo仅作为参考使用，以下使用的指纹参数仅是部分参数，完整参数请参考文档

url = "http://127.0.0.1:54345"
headers = {'Content-Type': 'application/json'}


def createBrowser():  # 创建或者更新窗口，指纹参数 browserFingerPrint 如没有特定需求，只需要指定下内核即可，如果需要更详细的参数，请参考文档
    json_data = {
        'name': 'Android',  # 窗口名称
        'remark': '',  # 备注
        'proxyMethod': 2,  # 代理方式 2自定义 3 提取IP
        # 代理类型  ['noproxy', 'http', 'https', 'socks5', 'ssh']
        'proxyType': 'noproxy',
        'host': '',  # 代理主机
        'port': '',  # 代理端口
        'proxyUserName': '',  # 代理账号
        'proxyPassword': '',  # 代理账号
        "browserFingerPrint": {  # 指纹对象
            'coreVersion': '124'  # 内核版本，注意，win7/win8/winserver 2012 已经不支持112及以上内核了，无法打开
        }
    }

    res = requests.post(f"{url}/browser/update",
                        data=json.dumps(json_data), headers=headers).json()
    browserId = res['data']['id']
    print(browserId)
    return browserId


def updateBrowser():  # 更新窗口，支持批量更新和按需更新，ids 传入数组，单独更新只传一个id即可，只传入需要修改的字段即可，比如修改备注，具体字段请参考文档，browserFingerPrint指纹对象不修改，则无需传入
    json_data = {'ids': ['93672cf112a044f08b653cab691216f0'],
                 'remark': '我是一个备注', 'browserFingerPrint': {}}
    res = requests.post(f"{url}/browser/update/partial",
                        data=json.dumps(json_data), headers=headers).json()
    print(res)


def openBrowser(id):  # 直接指定ID打开窗口，也可以使用 createBrowser 方法返回的ID
    json_data = {"id": f'{id}',"queue":True}
    res = requests.post(f"{url}/browser/open",
                        data=json.dumps(json_data), headers=headers).json()
    return res


def closeBrowser(id):  # 关闭窗口
    json_data = {'id': f'{id}'}
    requests.post(f"{url}/browser/close",
                  data=json.dumps(json_data), headers=headers).json()


def deleteBrowser(id):  # 删除窗口
    json_data = {'id': f'{id}'}
    print(requests.post(f"{url}/browser/delete",
          data=json.dumps(json_data), headers=headers).json())

def check_proxy(proxy): # 检测代理是否可用
    json_data = {
        'host': f'{proxy['ip']}',  # 代理主机
        'port':  f'{proxy['port']}',  # 代理端口
        'proxyType': 'https',
        'proxyUserName': f'{proxy['username']}',# 代理账号
        'proxyPassword': f'{proxy['password']}',  # 代理账号密码
        'ipCheckService': 'ip-api',  # IP检测渠道，默认ip-api，选项 ip-api | ip123in | luminati，luminati为Luminati专用
        'checkExists': 0
    }
    res = requests.post(f"{url}/checkagent",
                        data=json.dumps(json_data), headers=headers).json()
    print(res)
    if not res['data']['success']:
        print(f'代理不可用：{':'.join(proxy.values())}')
    return res['data']['success']

if __name__ == '__main__':
    json_data = {
        'ip': 'proxy.ipipgo.com',  # 代理主机
        'port': '31212',  # 代理端口
        'username': 'customer-fdd151c0-country-US-region-Louisiana-city-Alexandria-session-68da66416fdb428-time-5',  # 代理账号
        'password': '618fed4c',  # 代理账号

    }
    check_proxy(json_data)

    # browser_id = createBrowser()
    # openBrowser(browser_id)
    #
    # time.sleep(10)  # 等待10秒自动关闭窗口
    #
    # closeBrowser(browser_id)
    #
    # time.sleep(10)  # 等待10秒自动删掉窗口
    #
    # deleteBrowser(browser_id)
