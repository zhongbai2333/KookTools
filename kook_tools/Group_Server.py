import asyncio
import json

import websockets
from mcdreforged.api.all import *


@new_thread('Group_Server')
def init():
    from .Global_Variable import set_variable
    group_server = GroupServer()
    set_variable('group_server', group_server)
    group_server.start_server()


class GroupServer:
    def __init__(self):
        # 初始化函数
        self.finish_close = False
        self.websockets = {}
        self.broadcast_websockets = set()
        self.main_task = None
        # 获取函数
        from .Global_Variable import get_variable
        self.__mcdr_server = get_variable('__mcdr_server')
        self.config = get_variable('config')
        self.debug = get_variable('debug')
        self.botdata = get_variable('botdata')
        # 初始化组列表
        self.server_infos = {
            '-----': [self.config.server_name, self.botdata.command_group, self.botdata.talk_groups]
        }
        self.command_group_list = {}
        self.talk_groups_list = {}
        if self.botdata.command_group:
            self.command_group_list[self.botdata.command_group] = ['-----']
        for i in self.botdata.talk_groups:
            self.talk_groups_list[i] = ['-----']

    def add_command_group(self, g_id, target_id, add: bool):
        if add:
            self.server_infos[g_id][1] = target_id
            # 记录至组列表
            if target_id in self.command_group_list.keys():
                self.command_group_list[target_id].append(g_id)
            else:
                self.command_group_list[target_id] = [g_id]
        else:
            self.server_infos[g_id][1] = ""
            # 记录至组列表
            if g_id == self.command_group_list[target_id][0]:
                del self.command_group_list[target_id]
            else:
                self.command_group_list[target_id].remove(g_id)

    def add_talk_group(self, g_id, target_id, add: bool):
        if add:
            self.server_infos[g_id][2].append(target_id)
            # 记录至组列表
            if target_id in self.talk_groups_list.keys():
                self.talk_groups_list[target_id].append(g_id)
            else:
                self.talk_groups_list[target_id] = [g_id]
        else:
            self.server_infos[g_id][2].remove(target_id)
            # 记录至组列表
            if g_id == self.talk_groups_list[target_id][0]:
                del self.talk_groups_list[target_id]
            else:
                self.talk_groups_list[target_id].remove(g_id)

    # 启动服务器
    def start_server(self):
        asyncio.run(self.init_main())

    # 关闭服务器
    def close_server(self):
        self.main_task.cancel()

    # 导入主服务器 task
    async def init_main(self):
        self.main_task = asyncio.create_task(self.main())
        try:
            await self.main_task  # 运行主服务器
        except asyncio.CancelledError:
            self.__mcdr_server.logger.info('Group Websocket 已关闭！')
            self.finish_close = True

    # 主服务监听
    async def main(self):
        async with websockets.serve(self.handler, self.config.server_host, self.config.server_port):
            self.__mcdr_server.logger.info("Group websocket 启动成功！")
            await asyncio.Future()  # run forever

    # 主服务器管理
    async def handler(self, websocket):
        server_id = None  # 初始化 server_id
        while True:
            try:
                msg = await websocket.recv()  # 接收数据包
                msg = json.loads(msg)  # 解码
                if self.debug:
                    self.__mcdr_server.logger.info(f"已收到子服消息：{msg}")

                # hello 数据包
                if msg['s'] == 1:
                    if msg['password'] == self.config.password:  # 判断密码是否正确
                        from .Config import create_string_number
                        # 生成 5 位随机 id
                        server_id = create_string_number(5)
                        # 记录至列表
                        self.websockets[server_id] = websocket
                        self.broadcast_websockets.add(websocket)
                        self.server_infos[server_id] = [
                            msg['data']['server_name'],
                            msg['data']['command_group'],
                            msg['data']['talk_groups']
                        ]
                        # 记录至组列表
                        if msg['data']['command_group'] in self.command_group_list.keys():
                            self.command_group_list[msg['data']['command_group']].append(server_id)
                        else:
                            self.command_group_list[msg['data']['command_group']] = [server_id]
                        for i in msg['data']['talk_groups']:
                            if i in self.talk_groups_list.keys():
                                self.talk_groups_list[i].append(server_id)
                            else:
                                self.talk_groups_list[i] = [server_id]
                        # 返回数据包
                        await websocket.send(json.dumps({
                            's': 1,
                            'id': server_id,
                            'status': 'Succeed',
                            'data': {
                                'server_name': self.config.server_name
                            }
                        }))
                        # 广播服务器启动
                        self.__mcdr_server.say(f"§7{self.server_infos[server_id][0]} 已启动！")
                        self.broadcast({
                            's': 0,
                            'id': 'all',
                            'from': server_id,
                            'data': {
                                'type': 0,
                                'msg': f"§7{self.server_infos[server_id][0]} 已启动！"
                            }
                        })
                    else:
                        await websocket.close(reason="Error Password!")  # 密码错误关闭连接
                        break

                # msg 数据包
                elif msg['s'] == 0:
                    if msg['data']['type'] == 1:  # 确认是否为广播消息
                        self.__mcdr_server.say(msg['data']['msg'])
                        self.broadcast({
                            's': 0,
                            'id': 'all',
                            'from': server_id,
                            'data': {
                                'type': 0,
                                'msg': msg['data']['msg']
                            }
                        })
            except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosedError):
                self.close_connect(server_id, websocket)
                break

    # 断开连接并删除记录
    def close_connect(self, server_id=None, websocket=None):
        if server_id is not None and websocket is not None:
            # 广播服务关闭消息
            self.__mcdr_server.say(f"§7{self.server_infos[server_id][0]} 已关闭！")
            self.broadcast({
                's': 0,
                'id': 'all',
                'from': server_id,
                'data': {
                    'type': 0,
                    'msg': f"§7{self.server_infos[server_id][0]} 已关闭！"
                }
            })
            del self.websockets[server_id]
            self.broadcast_websockets.remove(websocket)
            del self.server_infos[server_id]
            self.__mcdr_server.logger.info(f"子服务器 {server_id} 已与 Group Websockets 断开连接！")
        else:
            self.__mcdr_server.logger.info("Group Websockets 已断开一个陌生的连接！")

    async def send_message(self, s, s_id, s_type, s_msg):
        await self.websockets[s_id].send(json.dumps({
            's': s,
            'id': s_id,
            'from': '-----',
            'data': {
                'type': s_type,
                'msg': s_msg
            }
        }))

    # 广播
    def broadcast(self, msg):
        websockets.broadcast(self.broadcast_websockets, json.dumps(msg))
