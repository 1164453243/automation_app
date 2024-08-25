import requests

# 初始化一些基本参数
base_url = "https://www.g2a.com/search/api/v2/products"
params = {
    "itemsPerPage": 18,  # 每页显示的项目数量，可以增加这个值以减少请求次数
    "include[0]": "filters",
    "include[1]": "frodo",
    "currency": "USD",
    "isWholesale": "false",
    "sort": "price-highest-first",
    "category": "189",
    "price[min]": "11",
    "price[max]": "22",
}
# 设置自定义的请求头信息
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}
# 用于存储所有获取到的商品
all_products = []

# 假设有10页数据
page = 1
total_pages = 10  # 这个值可以根据响应中的 `totalPages` 动态调整

while page <= total_pages:
    params['page'] = page  # 设置当前页码

    response = requests.get(base_url, params=params, headers=headers)
    data = response.json()

    # 将获取到的商品加入到总列表中
    all_products.extend(data['items'])

    # 更新总页数（可选）
    total_pages = data['meta']['pagination']['totalPages']

    print(f"Fetched page {page} of {total_pages}")
    page += 1

# 输出所有商品
for product in all_products:
    print(product)

# 如果你需要保存结果到文件中
import json

with open('all_products.json', 'w') as f:
    json.dump(all_products, f, indent=4)
