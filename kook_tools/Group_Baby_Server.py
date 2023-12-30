# 处理Get请求
import json
import socket

import requests

global config, botdata, botmsg, commands, data


# 双方交流
def get_gateway(password_n: str) -> str:
    header = {"Authorization": f"{password_n}"}  # 写入token
    json_send = {
        "host": "0.0.0.0",
        "port": get_free_port()
    }

    # 发送请求
    get = requests.post("http://127.0.0.1:8080", json=json_send, headers=header)
    # 返回地址
    json_dict = json.loads(get.text)  # 转json字典解析
    return json_dict  # 返回地址


# 获取可用端口
def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _, port = s.getsockname()
    return port


# 主接口
def main(config_input, botdata_input, botmsg_input, commands_input, data_input):
    global config, botdata, botmsg, commands, data
    config = config_input
    botdata = botdata_input
    botmsg = botmsg_input
    commands = commands_input
    data = data_input
    password = config.password
    print(get_gateway(password))
