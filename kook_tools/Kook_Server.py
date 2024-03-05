import time

from mcdreforged.api.all import *

import asyncio
import json
import websockets
import requests


# ======================
# Kook Websockets Server
# ======================
@new_thread("Kook_Server")
def init():
    from .Global_Variable import set_variable
    kook_server = KookServer()
    set_variable("kook_server", kook_server)
    kook_server.start_server()  # 启动服务器


class KookServer:
    def __init__(self):  # 初始化
        from .Global_Variable import get_variable
        self.botname = None
        self.botid = None
        self.hello_pack = False
        self.finish_quit = 0
        self.connect_task = None
        self.send_task = None
        self.pong_back = False
        self.bot_heartbeat_task = None
        self.session_id = None
        self.sn = None
        self.receive_task = None
        self.__mcdr_server = get_variable("__mcdr_server")
        self.config = get_variable("config")
        self.ws = None
        self.debug = get_variable("debug")

    def get_gateway(self) -> str:
        if self.config.token:  # 检查token是否填写
            header = {"Authorization": f"Bot {self.config.token}"}  # 写入token
            gateway_uri = f"/api/v{str(self.config.api_version)}/gateway/index?compress=0"  # 写入api版本
            # 发送请求
            get = requests.get(self.config.uri + gateway_uri, headers=header)
            # 返回地址
            if get.text:  # 检查是否回复
                json_dict = json.loads(get.text)  # 转json字典解析
                if self.debug:
                    self.__mcdr_server.logger.info(f"获取到websocket地址：{json_dict['data']['url']}")
                return json_dict['data']['url']  # 返回地址
            else:
                self.__mcdr_server.logger.error("websocket地址获取失败")
                return ""
        else:
            self.__mcdr_server.logger.error("未找到token！")
            return ""

    async def connect(self) -> None:
        if self.ws is None:
            url = self.get_gateway()  # 获取 Gateway 地址
            if url:  # 如果成功获取地址
                async with websockets.connect(url) as self.ws:  # 创建连接
                    self.__mcdr_server.logger.info("Kook Websocket服务器连接成功！")
                    await self.receive()
            else:
                self.__mcdr_server.logger.error("Kook Websocket服务器无法启动！")
                self.finish_quit = 2

    # 断开连接
    async def disconnect(self) -> None:
        if self.ws is not None:
            self.bot_heartbeat_task.cancel()
            if self.debug:
                self.__mcdr_server.logger.info("已请求关闭心跳系统！")
            self.receive_task.cancel()
            if self.debug:
                self.__mcdr_server.logger.info("已请求与Kook Websocket服务器断开连接！")

    # 数据包接受服务
    async def receive(self):
        while True:
            if self.ws is None:
                self.__mcdr_server.logger.error("Receive 服务无法找到 Websockets 服务器连接！")
                return None
            self.receive_task = asyncio.create_task(self.get_recv())
            try:
                recv_data = await self.receive_task
                if self.debug:
                    self.__mcdr_server.logger.info(f"已收到Kook数据包：{recv_data}")
                self.parse_msg_service(recv_data)
            except asyncio.CancelledError:
                self.__mcdr_server.logger.info("Receive 服务已退出！")
                self.hello_pack = False
                self.finish_quit += 1
                return None

    # 获取数据包模块
    async def get_recv(self):
        while True:
            try:
                return await asyncio.wait_for(self.ws.recv(), timeout=4)  # 及时刷新状态
            except asyncio.TimeoutError:
                pass

    # 简单消息处理模块
    @new_thread("ParseMsgService")
    def parse_msg_service(self, recv_data: str) -> None:
        from .Msg_Parse import get_post_msg, parse_msg
        recv_data = json.loads(recv_data)  # 解码数据包
        # 普通数据包
        if recv_data["s"] == 0:
            self.sn = recv_data['sn']  # 获取sn
            parse_msg(self.botid, recv_data)  # 处理消息
        # hello 数据包
        elif recv_data["s"] == 1:
            if self.debug:  # 检测 debug 模式
                self.__mcdr_server.logger.info(f"已收到Hello数据包！")
            self.hello_pack = True
            res = get_post_msg("/user/me")
            self.botid = res['data']['id']
            self.botname = res['data']['username']
            self.__mcdr_server.logger.info(f"已登录至机器人{self.botname}({self.botid})")
            if self.sn is None:
                self.sn = 0  # 初始化 sn
                self.session_id = recv_data['d']['session_id']
                asyncio.run(self.init_bot_heartbeat_task())  # 运行心跳系统
        # Pong 数据包
        elif recv_data["s"] == 3:
            if self.debug:
                self.__mcdr_server.logger.info(f"已收到Pong包！({self.sn})")
            self.pong_back = True  # 发出pong包信号
        # Reconnect 数据包
        elif recv_data["s"] == 5:
            self.__mcdr_server.logger.error(f"收到强制重新获取地址数据包，开启重连程序！")
            self.stop_server()
            while self.finish_quit != 2:  # 确认退出信号
                time.sleep(1)
            if self.reconnect():  # 启动重连流程
                return None

    # 导入心跳 Task
    async def init_bot_heartbeat_task(self):
        self.bot_heartbeat_task = asyncio.create_task(self.bot_heartbeat())
        try:
            await self.bot_heartbeat_task
        except asyncio.CancelledError:
            self.__mcdr_server.logger.info("已关闭心跳系统！")
            self.finish_quit += 1  # 添加关闭信号

    # 心跳系统
    async def bot_heartbeat(self) -> None:
        while True:
            retry = 0  # 初始化 retry 信号
            await self.ws.send('{"s": 2, "sn": ' + str(self.sn) + '}')  # 发送 Ping 包
            if self.debug:
                self.__mcdr_server.logger.info(f"已发送Ping包！({self.sn})")
            await asyncio.sleep(2)  # 等待 2 秒
            if self.pong_back:  # 确认 Pong 包信号
                if self.debug:
                    self.__mcdr_server.logger.info(f"已确认收到Pong包！({self.sn})")
                self.pong_back = False  # 关闭 Pong 包信号
                for _ in range(7):
                    await asyncio.sleep(4)  # 28 秒等待
            else:  # 未等到 Pong 包，重试发送 Ping 包
                retry += 1  # 添加一次 retry
                self.__mcdr_server.logger.warn(f"已发送Ping包！已重试：{retry}({self.sn})")
                if retry == 2:  # 如果两次 retry 失败
                    self.__mcdr_server.logger.error("心跳系统严重超时！")
                    self.receive_task.cnacel()  # 退出主服务器
                    while self.finish_quit != 1:  # 等待退出信号
                        await asyncio.sleep(1)
                    else:
                        if self.reconnect():  # 启动重新流程
                            self.finish_quit = 0  # 删除退出信号
                            continue  # 继续循环

    # 重新流程
    def reconnect(self) -> bool:
        retry = 0  # 初始化 retry 信号
        while True:  # 无限重试
            asyncio.run(self.connect())  # 运行 connect
            time.sleep(8)  # 睡眠 8 秒
            if self.hello_pack:  # 等待 hello 数据包
                return True
            else:
                retry += 1  # retry 信号 +1
                self.__mcdr_server.logger.warn(f"Gateway重连超时！已经重试{retry}次！")

    # 启动服务器
    def start_server(self) -> None:
        asyncio.run(self.connect())

    # 关闭服务器
    def stop_server(self) -> None:
        asyncio.run(self.disconnect())
