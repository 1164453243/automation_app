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
