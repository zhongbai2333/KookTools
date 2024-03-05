import asyncio
import json

import websockets
from mcdreforged.api.all import *


@new_thread('Baby_server')
def init():
    from .Global_Variable import set_variable
    baby_server = BabyServer()
    set_variable('baby_server', baby_server)
    baby_server.start_server()


class BabyServer:
    def __init__(self):
        self.fin_start = False
        self.main_task = None
        self.main_server_name = None
        self.server_id = None
        self.finish_quit = False
        self.receive_task = None
        self.websocket = None
        from .Global_Variable import get_variable
        self.__mcdr_server = get_variable('__mcdr_server')
        self.debug = get_variable('debug')
        self.config = get_variable('config')
        self.botdata = get_variable('botdata')

    def start_server(self):
        asyncio.run(self.init_main())

    def stop_server(self):
        if self.receive_task:
            self.receive_task.cancel()
        else:
            self.finish_quit = True
            pass

    async def init_main(self):
        self.main_task = asyncio.create_task(self.main())
        try:
            await self.main_task
        except asyncio.CancelledError:
            self.__mcdr_server.logger.info('Baby Websockets 关闭！')

    async def main(self):
        while True:
            try:
                async with (websockets.connect(f"ws://{self.config.far_server_host}:{self.config.far_server_port}")
                            as self.websocket):
                    self.fin_start = True
                    self.__mcdr_server.logger.info("Group Websockets 连接成功！")
                    await self.receive()
                break
            except ConnectionRefusedError:
                self.fin_start = False
                await asyncio.sleep(1)

    async def receive(self):
        await self.websocket.send(json.dumps({
            's': 1,
            'password': self.config.password,
            'status': 'Connect',
            'data': {
                'server_name': self.config.server_name,
                'command_group': self.botdata.command_group,
                'talk_groups': self.botdata.talk_groups
            }
        }))
        while True:
            self.receive_task = asyncio.create_task(self.get_recv())
            try:
                recv_data = await self.receive_task
                if recv_data:
                    if self.debug:
                        self.__mcdr_server.logger.info(f"已收到 Baby 数据包：{recv_data}")
                    self.parse_msg_service(json.loads(recv_data))
                else:
                    break
            except asyncio.CancelledError:
                self.__mcdr_server.logger.info("Receive 服务已退出！")
                self.finish_quit = True
                return None

    async def get_recv(self):
        while True:
            try:
                return await asyncio.wait_for(self.websocket.recv(), timeout=4)
            except asyncio.TimeoutError:
                pass
            except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK):
                self.__mcdr_server.say(f"§7{self.main_server_name} 已关闭！")
                self.__mcdr_server.logger.error("已与主服务器断开连接！")
                init()
                return None

    @new_thread('ParseMsgService')
    def parse_msg_service(self, recv_data: dict):
        # hello 数据包
        if recv_data['s'] == 1:
            self.__mcdr_server.logger.info("已成功与 Group Server 建立连接！")
            self.__mcdr_server.say(f"§7{recv_data['data']['server_name']} 已启动！")
            self.server_id = recv_data['id']
            self.main_server_name = recv_data['data']['server_name']

        # msg 数据包
        elif recv_data['s'] == 0:
            if recv_data['from'] != self.server_id and recv_data['data']['type'] == 0:
                self.__mcdr_server.say(recv_data['data']['msg'])
            elif recv_data['from'] != self.server_id and recv_data['data']['type'] == 3:
                from .Config import save_botdata
                msg_c = recv_data['data']['msg'].split()
                if msg_c[1] == 'ADD':
                    save_botdata("command_group", msg_c[0], True)
                else:
                    save_botdata("command_group", msg_c[0], False)
            elif recv_data['from'] != self.server_id and recv_data['data']['type'] == 4:
                from .Config import save_botdata
                msg_c = recv_data['data']['msg'].split()
                if msg_c[1] == 'ADD':
                    save_botdata("talk_groups", msg_c[0], True)
                else:
                    save_botdata("talk_groups", msg_c[0], False)
