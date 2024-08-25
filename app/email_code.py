from time import sleep
from bs4 import BeautifulSoup
import requests

def getCodeAndUrl(username, password, count, max_retries=30):
    # 访问接口并获取页面内容
    url = f"http://gmall1.com/api/getcode.php?yhm={username}&mm={password}"
    response = requests.get(url)

    # 检查请求是否成功
    if response.status_code == 200:
        html_content = response.text
    else:
        print("请求失败，状态码:", response.status_code)
        return None, None

    # 解析 HTML 内容
    soup = BeautifulSoup(html_content, 'html.parser')

    # 提取 <span> 标签中的验证码
    span_element = soup.find('span', style="mso-text-raise: 15pt;")
    verification_code = ''
    if span_element:
        verification_code = span_element.find('strong').text
        print("验证码:", verification_code)
    else:
        print("未找到验证码")

    # 提取 <a> 标签中的 href 属性
    href_value = None
    a_element = soup.find('a', href=True)
    if a_element:
        href_value = a_element['href']
        print("链接:", href_value)
    else:
        print("未找到链接")

    # 如果未获取到验证码且未超过最大重试次数，则继续重试
    if not verification_code and count < max_retries:
        print(f"重试第 {count + 1} 次...")
        sleep(2)
        return getCodeAndUrl(username, password, count + 1, max_retries)

    # 返回获取到的验证码和链接
    return verification_code, href_value

# 调用函数并处理结果
# code, url = getCodeAndUrl('vdi964@gmall1.com', 'ghc478', 0)
#
# if code:
#     print(f"最终获取到的验证码: {code}")
# else:
#     print("未能获取到验证码")
#
# if url:
#     response = requests.get(url)
#     if response.status_code == 200:
#         print("訪問成功:", url)
#     else:
#         print("訪問失敗:", url)

