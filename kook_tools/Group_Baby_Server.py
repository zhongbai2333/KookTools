# 处理Get请求
import json
import socket
import time

import requests
from mcdreforged.api.all import *
from http.server import BaseHTTPRequestHandler, HTTPServer

global config, botdata, botmsg, commands, data, server_info, __mcdr_server, httpd, pong_back, group_server_die


# -------------------------
# Group servers Get event listener
# -------------------------
@new_thread('GetServer')
def get_server(host: str, port: int):
    global httpd
    # 设置服务器地址和端口
    server_address = (host, port)
    httpd = HTTPServer(server_address, MyHandler)
    __mcdr_server.logger.info("Get服务器于 {0} 启动...".format(str(port)))
    httpd.serve_forever()


class MyHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        # 重写log_request方法，取消日志打印
        pass

    def do_GET(self):
        # 构造响应
        self.send_response(405)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes(f"""<h1>405</h1>
        <h3>Only Post</h3><p>{config.server_name} Provides</p>""", "utf-8"))

    def do_POST(self):
        global pong_back
        req_datas = self.rfile.read(int(self.headers['content-length']))  # 重点在此步!
        server_id = self.headers['id']
        if server_id:
            if server_id == server_info['data']["id"]:
                if json.loads(req_datas.decode())['code'] == 2:
                    json_send = {
                        "code": 200,
                        "msg": "success",
                        "data": {}
                    }
                    pong_back = True
                    self.send_response(200)
                else:
                    json_send = {
                        "code": 404,
                        "msg": "Unknown Code",
                        "data": {}
                    }
                    self.send_response(404)
            else:
                json_send = {
                    "code": 404,
                    "msg": "error id",
                    "data": {}
                }
                self.send_response(404)
        else:
            json_send = {
                "code": 404,
                "msg": "Can't find an id",
                "data": {}
            }
            self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(json_send).encode('utf-8'))


# -------------------------
# Group servers Heart event listener
# -------------------------
# 群组服维生系统
def post_group_server(code: int, msg: str, data_send=None):
    if data_send is None:
        data_send = {}
    header = {"id": f"{server_info['data']['id']}"}
    json_send = {
        "code": code,
        "msg": msg,
        "data": data_send
    }
    post = requests.post(f"http://{server_info['data']['host']}:{server_info['data']['port']}", json=json_send, headers=header)
    json_dict = json.loads(post.text)  # 转json字典解析
    return json_dict  # 返回地址


@new_thread("Post Heart Server")
def post_heart_server():
    global pong_back, group_server_die
    while True:
        break_die = 0
        while True:
            if break_die < 2:
                post_group_server(1, "PING")
                time.sleep(3)
                if pong_back:
                    pong_back = False
                    break
                else:
                    break_die += 1
            else:
                group_server_die = True
        if group_server_die:
            break
        else:
            time.sleep(30)


# 双方交流
def get_gateway(password_n: str, host: str) -> dict:
    header = {"Authorization": f"{password_n}"}  # 写入token
    if config.baby_server_port == 0:
        port = get_free_port()
    else:
        port = config.baby_server_port
    json_send = {
        "host": host,
        "port": port
    }

    # 发送请求
    post = requests.post(f"http://{config.main_server_host}:{config.main_server_port}", json=json_send, headers=header)
    # 返回地址
    json_dict = json.loads(post.text)  # 转json字典解析
    return json_dict  # 返回地址


# 获取可用端口
def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _, port = s.getsockname()
    return port


# 主接口
def main(config_input, botdata_input, botmsg_input, commands_input, data_input, mcdr):
    global config, botdata, botmsg, commands, data, __mcdr_server, server_info, group_server_die
    config = config_input
    botdata = botdata_input
    botmsg = botmsg_input
    commands = commands_input
    data = data_input
    password = config.password
    __mcdr_server = mcdr
    debug_status = config.debug
    group_server_die = False
    server_info = get_gateway(password, config.baby_server_host)
    if debug_status:
        __mcdr_server.logger.info(f"Server info: {server_info}")
    get_server(server_info['data']['host'], server_info['data']['port'])
    post_heart_server()
