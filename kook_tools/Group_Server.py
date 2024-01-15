import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from mcdreforged.api.all import *

import websockets
import asyncio

global baby_list


def init():
    websocket_server()
    get_server()


@new_thread('Group websocket server')
def websocket_server():
    from .Global_Variable import set_variable
    group_server = GroupServer()
    set_variable("group_server", group_server)
    asyncio.run(group_server.main())


class GroupServer:
    def __init__(self):
        self.broadcast_websocket = set()
        self.websocket = {}
        from .Global_Variable import get_variable
        self.__mcdr_server = get_variable("__mcdr_server")
        self.config = get_variable("config")

    async def main(self):
        async with websockets.serve(self.group_handler, self.config.main_websocket_host, self.config.main_websocket_port):
            self.__mcdr_server.logger.info("Group websocket 启动成功！")
            await asyncio.Future()  # run forever

    async def group_handler(self, websocket):
        try:
            async for message in websocket:
                msg = json.loads(message)
                self.__mcdr_server.logger.info(f"已收到子服消息：{msg}")
                if msg["s"] == 1:
                    if msg["id"] in baby_list:
                        self.websocket[msg["id"]] = websocket
                        self.broadcast_websocket.add(websocket)
                        await self.websocket[msg["id"]].send(json.dumps({
                            's': 2,
                            'id': msg["id"],
                            'status': 'success'
                        }))
                    else:
                        websocket.wait_close()
                        return None
                elif msg["s"] == 3:
                    if self.config.debug:
                        self.__mcdr_server.logger.info("已收到子服务器Ping包！")
                    await self.websocket[msg["id"]].send(json.dumps({
                        's': 4,
                        'id': msg["id"],
                        'status': 'Pong'
                    }))
        except (websockets.ConnectionClosedOK, websockets.ConnectionClosedError):
            self.__mcdr_server.logger.info("Group Websocket 已关闭其中一个连接！")
            return None

    def broadcast(self, msg):
        websockets.broadcast(self.broadcast_websocket, json.dumps(msg))


# -------------------------
# Group servers Get event listener
# -------------------------
class MyHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        # 重写log_request方法，取消日志打印
        pass

    def do_GET(self):
        from .Global_Variable import get_variable
        # 构造响应
        self.send_response(405)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes(f"""<h1>405</h1>
        <h3>Only Post</h3><p>{get_variable("config").server_name} Provides</p>""", "utf-8"))

    def do_POST(self):
        from .Global_Variable import get_variable
        from .Config import create_string_number
        global baby_list
        authorization = self.headers['Authorization']
        if authorization:
            if authorization == get_variable("config").password:
                id_group_http = create_string_number(8)
                json_send = {
                    "code": 200,
                    "msg": "success",
                    "data": {
                        "host": get_variable("config").main_websocket_host,
                        "port": get_variable("config").main_websocket_port,
                        "id": id_group_http
                    }
                }
                baby_list.append(id_group_http)
                self.send_response(200)
            else:
                json_send = {
                    "code": 404,
                    "msg": "can't find password",
                    "data": {}
                }
                self.send_response(404)
        else:
            json_send = {
                "code": 404,
                "msg": "Can't find an authorization or id",
                "data": {}
            }
            self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(json_send).encode('utf-8'))


@new_thread('GetServer')
def get_server():
    from .Global_Variable import get_variable, set_variable
    global baby_list
    # 设置服务器地址和端口
    baby_list = []
    server_address = (get_variable('config').main_server_host, get_variable('config').main_server_port)
    httpd = HTTPServer(server_address, MyHandler)
    get_variable("__mcdr_server").logger.info("Get服务器于 {0} 启动...".format(str(get_variable('config').main_server_port)))
    set_variable("httpd", httpd)
    httpd.serve_forever()
