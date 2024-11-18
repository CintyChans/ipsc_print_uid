import json

cert = ("client.crt", "client.key")
ca_cert = "root.crt"
with open("config.json", "r") as file:
    # 加载 JSON 数据
    config_data = json.load(file)

with open("uBeacon Hardware Batch_20241021.json", "r") as file:
    # 加载 JSON 数据
    hardware_info_data = json.load(file)
