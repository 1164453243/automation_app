from time import sleep
from bs4 import BeautifulSoup
import requests

# 支付失败标识
pay_fail_sign='We are sorry but your payment has been rejected by our system'

def get_email_content(username,password):
    # 访问接口并获取页面内容
    url = f"http://gmall1.com/api/getcode.php?yhm={username}&mm={password}"
    response = requests.get(url)

    # 检查请求是否成功
    if response.status_code == 200:
        return response.text
    else:
        print("请求失败，状态码:", response.status_code)
        return
def getCodeAndUrl(username, password, count, max_retries=30):
    # 获取 HTML 内容
    html_content = get_email_content(username, password)
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

def check_pay_status(username, password, count, max_retries=30): #获取支付状态
    # 获取返回文本
    text = get_email_content(username, password)
    # 如果未获取到返回内容且未超过最大重试次数，则继续重试
    if not text and count < max_retries:
        print(f"重试第 {count + 1} 次...")
        sleep(2)
        return check_pay_status(username, password, count + 1, max_retries)
    else:
        if pay_fail_sign in text:
            return False
        else:
            return True

if __name__ == '__main__':
   print(pay_fail_sign in 'We are sorry but your payment has been rejected by our system abc')