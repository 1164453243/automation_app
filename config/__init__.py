import configparser

config = configparser.ConfigParser()
config.read('config/config.ini')

# 使用示例
browser_type = config['Browser']['type']
