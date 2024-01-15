import json
import asyncio
import time

import websockets
import requests

from mcdreforged.api.all import *

global config, __mcdr_server, pass_id, uri


@new_thread("Baby Websocket Server")
def init():
    from .Global_Variable import get_variable, set_variable
    global config, __mcdr_server, pass_id, uri
    config = get_variable("config")
    __mcdr_server = get_variable("__mcdr_server")
    data = get_gateway(config.password)
    uri = f"ws://{data['data']['host']}:{data['data']['port']}"
    pass_id = data['data']['id']
    baby_server = BabyServer(__mcdr_server)
    set_variable("baby_server", baby_server)
    time.sleep(1)
    asyncio.run(baby_server.connect(uri))


# 双方交流
def get_gateway(password_n: str) -> dict:
    header = {"Authorization": f"{password_n}"}  # 写入token
    json_send = {
        "code": 200
    }
    __mcdr_server.logger.info("正在获取Gateway地址")
    while True:
        try:
            # 发送请求
            post = requests.post(f"http://{config.main_server_host}:{config.main_server_port}", json=json_send, headers=header)
            # 返回地址
            json_dict = json.loads(post.text)  # 转json字典解析
            return json_dict  # 返回地址
        except requests.ConnectionError:
            pass


class BabyServer:
    def __init__(self, mcdr):
        self.ping_task = None
        self.pong_back = False
        self.finish_quit = 0
        self.receive_task = None
        self.ws = None
        self.__mcdr_server = mcdr

    async def connect(self, url) -> None:
        if self.ws is None:
            if url:
                async with websockets.connect(url) as self.ws:
                    self.__mcdr_server.logger.info("Group Server服务器连接成功！")
                    await self.receive()
            else:
                self.__mcdr_server.logger.error("Group Server服务器无法启动！")

    async def receive(self):
        await self.ws.send(json.dumps({
            's': 1,
            'id': pass_id,
            'status': 'success'
        }))
        while True:
            if self.ws is None:
                self.__mcdr_server.logger.error("Receive 服务无法找到 Websockets 服务器连接！")
                return None
            self.receive_task = asyncio.create_task(self.get_recv())
            try:
                recv_data = await self.receive_task
                if config.debug:
                    self.__mcdr_server.logger.info(f"已收到Baby数据包：{recv_data}")
                self.ParseMsgService(json.loads(recv_data))
            except asyncio.CancelledError:
                self.__mcdr_server.logger.info("Receive 服务已退出！")
                self.finish_quit += 1
                return None

    async def get_recv(self):
        while True:
            try:
                return await asyncio.wait_for(self.ws.recv(), timeout=4)
            except asyncio.TimeoutError:
                pass
            except websockets.ConnectionClosedError:
                self.__mcdr_server.logger.error("已与主服务器断开连接！")
                self.reconnect()
                break

    def disconnect(self) -> None:
        if self.ws is not None:
            self.receive_task.cancel()
            self.__mcdr_server.logger.info("已请求与Group Websocket服务器断开连接！")
            self.ping_task.cancel()
            self.__mcdr_server.logger.info("已请求关闭Ping服务！")

    async def ping(self):
        retry = 0
        while retry < 2:
            await self.ws.send(json.dumps({
                's': 3,
                'id': pass_id,
                'status': 'Ping'
            }))
            await asyncio.sleep(5)
            if self.pong_back:
                self.pong_back = False
                for _ in range(5):
                    await asyncio.sleep(5)
                continue
            else:
                retry += 1
        else:
            self.reconnect()

    @new_thread("Group Server Reconnect")
    def reconnect(self):
        if self.ws is not None:
            self.receive_task.cancel()
            self.__mcdr_server.logger.info("已请求与Group Websocket服务器断开连接！")
            self.ping_task.cancel()
            self.__mcdr_server.logger.info("已请求关闭Ping服务！")
        while self.finish_quit != 2:
            time.sleep(0.5)
        else:
            self.finish_quit = 0
            init()

    async def init_ping_task(self):
        self.ping_task = asyncio.create_task(self.ping())
        try:
            await self.ping_task
        except asyncio.CancelledError:
            self.__mcdr_server.logger.info("Ping服务已关闭！")
            self.finish_quit += 1

    @new_thread("Baby Server Parse Msg")
    def ParseMsgService(self, recv_data):
        from .Msg_Parse import parse_msg
        if recv_data['s'] == 2:
            self.__mcdr_server.logger.info("已成功与Group Server建立连接！")
            asyncio.run(self.init_ping_task())
        elif recv_data['s'] == 4:
            if config.debug:
                self.__mcdr_server.logger.info("已收到Pong包！")
            self.pong_back = True
        elif recv_data['s'] == 0:
            if config.debug:
                self.__mcdr_server.logger.info("已收到普通数据包！")
            parse_msg(recv_data['data']['botid'], recv_data['data']['msg'])

