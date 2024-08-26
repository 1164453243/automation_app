import json
import os

# 获取项目的根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config(filename):
    file_path = os.path.join(BASE_DIR, 'config', filename)
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def save_config(data, filename):
    file_path = os.path.join(BASE_DIR, 'config', filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def parse_proxy_info(proxy_line):
    # 拆分代理信息
    parts = proxy_line.strip().split(":")

    if len(parts) != 4:
        print("代理信息格式错误:", proxy_line)
        return None

    # 提取IP和端口
    ip = parts[0]  # IP 地址
    port = parts[1]  # 端口号

    # 提取用户名和密码
    username = parts[2]  # 完整的用户名部分
    password = parts[3]  # 密码部分

    # 从用户名中提取国家、城市和省份
    username_parts = username.split("-")

    # 提取国家、省份、城市
    try:
        country = username_parts[username_parts.index("country") + 1]  # 国家
        region = username_parts[username_parts.index("region") + 1]  # 省份
        city = username_parts[username_parts.index("city") + 1]  # 城市
    except (ValueError, IndexError) as e:
        print(f"从用户名中提取信息时出错: {e}")
        return None

    return {
        "ip": ip,
        "port": port,
        "username": username,  # 完整的用户名
        "password": password,
        "country": country,
        "region": region,
        "city": city
    }


def load_and_parse_proxies(region, city):
    # 读取 proxies.json 文件内容
    proxies_data = load_config('proxies.json')
    matched_proxy = None

    # 遍历并解析每一行代理信息
    for proxy_line in proxies_data:
        proxy_info = parse_proxy_info(proxy_line)
        if proxy_info:
            if proxy_info['region'].lower() == region.lower() and proxy_info['city'].lower() == city.lower():
                # 如果匹配到完全符合 region 和 city 的代理信息，则返回此代理
                print(f"匹配到代理: {proxy_info}")
                return proxy_info
            elif proxy_info['region'].lower() == region.lower():
                # 如果只匹配到 region 相同的代理，先记录下来
                matched_proxy = proxy_info
                return matched_proxy

    print("未匹配到符合条件的代理")
    return matched_proxy
