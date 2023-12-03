import asyncio
import json
import socket
import time
import copy
import re
from threading import Thread

try:  # 试图导入mysql处理
    import mysql.connector
except ImportError:
    mysql = None

import requests
import websockets
from mcdreforged.api.all import *
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from .config import Config, bot_data, BotMsg, Commands, create_string_number
from .MySQL_Control import (connect_and_delete_data, connect_and_query_db, connect_and_insert_db,
                            create_table_if_not_exists)

global __mcdr_server, config, debug_status, stop_status, sn, server_restart, session_id, heart_start, url, pong_back
global heart_stop, server_start, fin_stop_status, wait_admin, botdata, botmsg, server_list_number, server_list_id
global botid, botname, data, online_players, commands, wait_list, server_first_start, start_time1, httpd
global password_group_websocket, address, g_socket_server, g_conn_pool

global group_help, person_help, admin_person_help, set_server_help, t_and_c_group_help, bound_help, admin_bound_help


# -------------------------
# Help editor event listener
# -------------------------
# 处理command里的命令和描述
def make_help_msg():
    global group_help, person_help, admin_person_help, set_server_help, t_and_c_group_help, bound_help, admin_bound_help
    group_help = f'''
        {" / ".join(commands.help[0])} -- {commands.help[1]}
        {" / ".join(commands.admin_help[0])} -- {commands.admin_help[1]}
        {" / ".join(commands.list_player[0])} -- {commands.list_player[1]}
        {" / ".join(commands.bound[0])} -- {commands.bound[1]}'''
    t_and_c_group_help = f'''
        {config.command_prefix}{f" / {config.command_prefix}".join(commands.help[0])} -- {commands.help[1]}
        {config.command_prefix}{f" / {config.command_prefix}".join(commands.admin_help[0])} -- {commands.admin_help[1]}
        {config.command_prefix}{f" / {config.command_prefix}".join(commands.list_player[0])} -- {commands.list_player[1]}
        {config.command_prefix}{f" / {config.command_prefix}".join(commands.bound[0])} -- {commands.bound[1]}'''
    person_help = f'''
        {" / ".join(commands.help[0])} -- {commands.help[1]}
        {" / ".join(commands.admin_help[0])} -- {commands.admin_help[1]}
        {" / ".join(commands.get_admin[0])} -- {commands.get_admin[1]}'''
    admin_person_help = f'''
        {" / ".join(commands.set_server[0])} -- {commands.set_server[1]}'''
    set_server_help = f'''
        {" / ".join(commands.set_server_list[0])} -- {commands.set_server_list[1]}
        {" / ".join(commands.set_server_add[0])} -- {commands.set_server_add[1]}
        {" / ".join(commands.set_server_del[0])} -- {commands.set_server_del[1]}'''
    bound_help = f'''
        {" / ".join(commands.bound_check[0])} -- {commands.bound_check[1]}'''
    admin_bound_help = f'''
        {" / ".join(commands.bound_list[0])} -- {commands.bound_list[1]}
        {" / ".join(commands.bound_unbound[0])} -- {commands.bound_unbound[1]}
        {" / ".join(commands.bound_check[0])} -- {commands.bound_check[1]}'''


# -------------------------
# WebSocket event listener
# -------------------------
@new_thread('KookBot')  # 新建线程
def start_kook_bot():
    global server_restart, url, heart_start, heart_stop, server_start, fin_stop_status
    # 初始化信号变量
    heart_start = False
    heart_stop = False
    server_restart = False
    fin_stop_status = False
    while True:  # 开始底层循环
        if not stop_status:  # 检查关服信号
            if server_restart:  # 检查gateway重连信号
                url_r = url + f"&resume=1&sn={sn}&session_id={session_id}"  # 重制重试地址
                asyncio.run(get_websocket(url_r))
            else:
                server_start = False
                url = get_gateway()  # 获取gateway地址
                if url:
                    asyncio.run(get_websocket(url))  # 如果地址获取成功，就开始连接websocket
                else:
                    __mcdr_server.logger.error("机器人启动失败！")
                    break  # 启动失败
        else:
            break
    fin_stop_status = True
    __mcdr_server.logger.info(f"机器人关闭成功！")


# 获取gateway地址
def get_gateway() -> str:
    if config.token:  # 检查token是否填写
        header = {"Authorization": f"Bot {config.token}"}  # 写入token
        gateway_uri = f"/api/v{str(config.api_version)}/gateway/index?compress=0"  # 写入api版本
        # 发送请求
        get = requests.get(config.uri + gateway_uri, headers=header)
        # 返回地址
        if get.text:  # 检查是否回复
            json_dict = json.loads(get.text)  # 转json字典解析
            if debug_status:
                __mcdr_server.logger.info(f"获取到websocket地址：{json_dict['data']['url']}")
            return json_dict['data']['url']  # 返回地址
        else:
            __mcdr_server.logger.error("websocket地址获取失败")
            return ""
    else:
        __mcdr_server.logger.error("未找到token！")
        return ""


async def get_websocket(uri: str) -> None:  # 获取websocket连接
    global botid, botname
    async with websockets.connect(uri) as websocket:
        __mcdr_server.logger.info(f"websocket服务器连接成功！")
        if server_start:  # 检查是否第一次启动
            await asyncio.gather(get_service(websocket), bot_heart(websocket))
        else:
            await asyncio.gather(get_service(websocket))  # 如果两个async同时启动居然苏都不够快，来不及获取第一个包呜呜呜
            res = get_msg("/user/me")
            botid = res['data']['id']
            botname = res['data']['username']
            __mcdr_server.logger.info(f"已登录至机器人{botname}({botid})")
            await asyncio.gather(get_service(websocket), bot_heart(websocket))  # 正式启动


# 机器人接收数据包系统
async def get_service(websocket):
    global session_id, sn, heart_start, server_restart, pong_back, heart_stop, server_start
    if debug_status:
        __mcdr_server.logger.info(f"机器人接收数据包系统启动！")
    while True:
        if server_restart:  # 检查gateway重连信号
            retry = 0  # 初始化重试次数
            while retry < 3:  # 建立重试循环，2次机会
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=8)  # 超时8秒
                    if debug_status:
                        __mcdr_server.logger.info(f"已收到数据包！")
                    response_dict = json.loads(response)  # json字典处理
                    if response_dict['s'] == 1:  # 重连后hello数据包
                        await websocket.send('{"s": 4, "sn": ' + str(sn) + '}')  # 返回resume数据包
                        __mcdr_server.logger.info(f"发起Resume！")
                    elif response_dict['s'] == 0:  # 返回离线期间未同步的数据
                        sn = response_dict['sn']  # 同步sn
                        parse_get_msg(response_dict)
                        __mcdr_server.logger.info(f"收到离线期间数据包！")
                    elif response_dict['s'] == 6:  # resume完成数据包
                        __mcdr_server.logger.info(f"Gateway重连成功！")
                        server_restart = False  # 取消gateway连接重试
                        heart_start = True  # 启动维生系统
                        break  # 返回正常循环
                except asyncio.TimeoutError:  # 超时
                    retry += 1  # 添加重试次数
                    __mcdr_server.logger.warn(f"Gateway重连超时！准备重试{retry}/2次！")
            else:
                __mcdr_server.logger.error(f"Gateway重连严重超时！准备重新获取gateway地址！")
                heart_stop = True  # 退出机器人维生系统
                heart_start = True
                break
        else:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=36)  # 36秒超时
                if debug_status:
                    __mcdr_server.logger.info(f"已收到数据包！")
            except asyncio.TimeoutError:
                if stop_status:  # 检查关服信号
                    break
                __mcdr_server.logger.error(f"机器人接收数据包系统严重超时！")  # 超时判断维生系统崩溃，退出机器人接收数据包系统开始gateway重连
                heart_start = False  # 关闭维生系统启动信号
                server_restart = True  # 开启gateway重连信号
                break  # 退出机器人接收数据包系统
            response_dict = json.loads(response)  # 解码json字典
            if debug_status:
                __mcdr_server.logger.info(f"获取到数据：{response_dict}")
            if response_dict['s'] == 1:  # 第一次启动的Hello数据包
                if debug_status:
                    __mcdr_server.logger.info(f"已收到Hello数据包！")
                sn = 0  # 初始化sn
                session_id = response_dict['d']['session_id']  # 同步session_id
                heart_start = True  # 开启机器人维生系统
                server_start = True  # 确认第一次启动成功
                break  # 退出机器人接收数据包系统以启动机器人维生系统
            elif response_dict['s'] == 3:  # Pong包
                if debug_status:
                    __mcdr_server.logger.info(f"已收到Pong包！")
                pong_back = True  # 开启Pong包收取成功信号
            elif response_dict['s'] == 5:  # Reconnect数据包
                __mcdr_server.logger.error(f"收到强制重新获取地址数据包，机器人接收数据包系统已退出！")
                heart_stop = True  # 关闭机器人维生系统
                break  # 退出机器人接收数据包系统以完全重新获取gateway地址
            elif response_dict['s'] == 0:  # 正常的event事件数据包
                sn = response_dict['sn']  # 同步sn
                parse_get_msg(response_dict)  # 将数据包转交给另一个线程处理数据
        if server_restart or stop_status:  # 如果gateway重连信号启动或关服信号启动无需进行循环
            break  # 退出机器人接收数据包系统


# 机器人维生系统
async def bot_heart(websocket):
    global server_restart, heart_start, pong_back, heart_stop
    retry = 0  # 初始化重试次数
    if debug_status:
        __mcdr_server.logger.info(f"机器人维生系统正在启动……")
    while True:  # 开启维生循环
        if heart_start:  # 等待维生系统启动信号
            if server_restart:  # 确认gateway重连信号是否存在
                heart_start = False  # 关闭机器人维生系统
                break
            if heart_stop:  # 确认机器人维生系统退出信号
                heart_stop = False
                heart_start = False
                break
            if stop_status:  # 确认关服信号
                break
            while retry < 3:  # 三次重试机会
                await websocket.send('{"s": 2, "sn": ' + str(sn) + '}')  # 发送Ping包
                if debug_status:
                    __mcdr_server.logger.info(f"已发送Ping包！")
                await asyncio.sleep(2)  # 延迟等待
                if pong_back:  # 如果接收到Pong包
                    pong_back = False  # 关闭信号
                    retry = 0  # 重置
                    await asyncio.sleep(28)  # 等待28+2秒
                    break
                retry += 1
            if retry == 3:  # 检查是否超时
                __mcdr_server.logger.error(f"机器人维生系统严重超时！")
                heart_start = False  # 关闭维生系统
                server_restart = True  # 启动gateway重连系统
                break


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
        global password_group_websocket
        # 解析URL中的查询字符串
        query = parse_qs(urlparse(self.path).query)

        # 获取参数值
        password = query.get('password', [''])[0]

        # 构造响应
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        if password == config.password:
            password_group_websocket = create_string_number(10)
            self.wfile.write(bytes(str(password_group_websocket), "utf-8"))
        else:
            self.wfile.write(bytes("STOP", "utf-8"))


# -------------------------
# Group servers Websocket event listener
# -------------------------
@new_thread(f"Group Servers Websocket")
def group_servers_websocket():
    init()
    # 新开一个线程，用于接收新连接
    thread = Thread(target=accept_client)
    thread.daemon = True
    thread.start()
    # 主线程逻辑
    while True:
        time.sleep(0.1)


def init():
    global address, g_socket_server, g_conn_pool
    address = (config.main_websocket_server_host, config.main_websocket_server_port)  # 绑定地址
    g_socket_server = None  # 负责监听的socket
    g_conn_pool = {}  # 连接池
    g_socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    g_socket_server.bind(address)
    g_socket_server.listen(5)  # 最大等待数（有很多人理解为最大连接数，其实是错误的）
    __mcdr_server.logger.info(f"Websocket服务器已开始等待连接！")


# 接收新连接
def accept_client():
    while True:
        client, info = g_socket_server.accept()  # 阻塞，等待客户端连接
        # 给每个客户端创建一个独立的线程进行管理
        thread = Thread(target=message_handle, args=(client, info))
        # 设置成守护线程
        thread.daemon = True
        thread.start()


# 消息处理
def message_handle(client, info):
    client.sendall("connect server successfully!".encode(encoding='utf8'))
    client_type = ""
    while True:
        try:
            bytes_server = client.recv(1024)
            msg = bytes_server.decode(encoding='utf8')
            jd = json.loads(msg)
            cmd = jd['COMMAND']
            client_type = jd['client_type']
            if client_type != password_group_websocket:
                break
            if 'CONNECT' == cmd:
                g_conn_pool[client_type] = client
                print('on client connect: ' + client_type, info)
            elif 'SEND_DATA' == cmd:
                print('recv client msg: ' + client_type, jd['data'])
        except Exception as e:
            print(e)
            remove_client(client_type)
            break


def remove_client(client_type):
    client = g_conn_pool[client_type]
    if client is not None:
        client.close()
        g_conn_pool.pop(client_type)
        print("client offline: " + client_type)


# -------------------------
# Parse msg event listener
# -------------------------
# 机器人event处理系统
@new_thread('parse_get_msg')
def parse_get_msg(msg) -> dict or str:
    if msg['d']['channel_type'] == "GROUP":
        if debug_status:
            __mcdr_server.logger.info(f"收到群聊消息！发送者：{msg['d']['extra']['author']['username']}"
                                      f"({msg['d']['author_id']}),"
                                      f"于文字聊天室“{msg['d']['extra']['channel_name']}({msg['d']['target_id']})”发送，"
                                      f"内容为：{msg['d']['content']}")
        if msg['d']['extra']['guild_id'] in botdata.server_list:
            parse_group_command(msg['d']['content'], msg['d']['extra']['author']['username'], msg['d']['author_id'],
                                msg['d']['target_id'])
    elif msg['d']['channel_type'] == "PERSON":
        if debug_status:
            if msg['d']['type'] == 255:
                __mcdr_server.logger.info(f"收到系统信息！")
            else:
                __mcdr_server.logger.info(f"收到私聊消息！发送者：{msg['d']['extra']['author']['username']}"
                                          f"({msg['d']['author_id']}),"
                                          f"于私聊({msg['d']['target_id']})发送，"
                                          f"内容为：{msg['d']['content']}")
                if not msg['d']['extra']['author']['bot']:
                    parse_person_command(msg['d']['content'], msg['d']['extra']['author']['username'],
                                         msg['d']['author_id'])


# 处理Get请求
def get_msg(msg) -> dict or str:
    header = {"Authorization": f"Bot {config.token}"}  # 写入token
    gateway_uri = f"/api/v{str(config.api_version)}"  # 写入api版本
    # 发送请求
    get = requests.get(config.uri + gateway_uri + msg, headers=header)
    # 返回地址
    if get.text:  # 检查是否回复
        json_dict = json.loads(get.text)  # 转json字典解析
        if debug_status:
            __mcdr_server.logger.info(f"获取到的Get反馈：{json_dict}")
        return json_dict  # 返回数据
    else:
        return ""


# 发送消息
def send_group_person_msg(msg: str, target_id: str, mode: int):
    if mode == 0:  # person
        if debug_status:
            __mcdr_server.logger.info(f"发送到私聊({target_id})：{msg}")
        data_send = {
            "target_id": target_id,
            "content": msg
        }
        header = {"Authorization": f"Bot {config.token}"}  # 写入token
        gateway_uri = f"/api/v{str(config.api_version)}"  # 写入api版本
        uri_p = "/direct-message/create"
        post = requests.post(url=config.uri + gateway_uri + uri_p, json=data_send, headers=header)
        json_dict = json.loads(post.text)  # 转json字典解析
        if debug_status:
            __mcdr_server.logger.info(f"获取的Post回复：{json_dict}")
        if json_dict['code'] == "0":
            return True
        else:
            return False
    elif mode == 1:  # group
        if debug_status:
            __mcdr_server.logger.info(f"发送到群聊({target_id})：{msg}")
        data_send = {
            "target_id": target_id,
            "content": msg
        }
        header = {"Authorization": f"Bot {config.token}"}  # 写入token
        gateway_uri = f"/api/v{str(config.api_version)}"  # 写入api版本
        uri_p = "/message/create"
        post = requests.post(url=config.uri + gateway_uri + uri_p, json=data_send, headers=header)
        json_dict = json.loads(post.text)  # 转json字典解析
        if debug_status:
            __mcdr_server.logger.info(f"获取的Post回复：{json_dict}")
        if json_dict['code'] == "0":
            return True
        else:
            return False


# 处理群聊命令
def parse_group_command(msg: str, username: str, userid: str, target_id: str):
    msg_c = msg.split()
    if userid != botid and msg_c[0] != "(met)" + botid + "(met)":
        if target_id in botdata.talk_group and target_id in botdata.command_group:
            if msg[0] == config.command_prefix:
                msg_c = msg[1:].split()
                if msg_c[0] in commands.help[0]:
                    send_group_person_msg(botmsg.group_help.format(t_and_c_group_help), target_id, 1)
                elif msg_c[0] in commands.bound[0] and len(msg_c) == 2:
                    bound_player(userid, msg_c, target_id)
                elif msg_c[0] in commands.bound[0] and len(msg_c) != 2:
                    send_group_person_msg(botmsg.bound_error.format(config.command_prefix +
                                                                    f" / {config.command_prefix}"
                                                                    .join(commands.bound[0])),
                                          target_id, 1)
                elif msg_c[0] in commands.list_player[0]:
                    if __mcdr_server.is_server_running():
                        send_group_person_msg(botmsg.online_player_info.format(config.server_name,
                                                                               len(online_players),
                                                                               ', '.join(online_players)),
                                              target_id, 1)
                    else:
                        send_group_person_msg(botmsg.server_not_start.format(config.server_name), target_id, 1)
            else:
                turn_msg(userid, target_id, msg, True)
        elif target_id in botdata.talk_group:
            turn_msg(userid, target_id, msg, False)
        elif target_id in botdata.command_group:
            if msg_c[0] in commands.help[0]:
                send_group_person_msg(botmsg.group_help.format(group_help), target_id, 1)
            elif msg_c[0] in commands.bound[0] and len(msg_c) == 2:
                bound_player(userid, msg_c, target_id)
            elif msg_c[0] in commands.bound[0] and len(msg_c) != 2:
                send_group_person_msg(botmsg.bound_error.format(" / ".join(commands.bound[0])), target_id, 1)
            elif msg_c[0] in commands.list_player[0]:
                if __mcdr_server.is_server_running():
                    send_group_person_msg(botmsg.online_player_info.format(config.server_name,
                                                                           len(online_players),
                                                                           ', '.join(online_players)),
                                          target_id, 1)
                else:
                    send_group_person_msg(botmsg.server_not_start.format(config.server_name), target_id, 1)
    elif msg_c[0] == "(met)" + botid + "(met)" and len(msg_c) <= 1:
        if target_id in botdata.command_group and target_id in botdata.talk_group:
            send_group_person_msg(botmsg.at_msg.format(" / ".join(commands.set_talk_group[0]),
                                                       " / ".join(commands.set_command_group[0]),
                                                       "已添加为聊天组和命令组"), target_id, 1)
        elif target_id in botdata.command_group:
            send_group_person_msg(botmsg.at_msg.format(" / ".join(commands.set_talk_group[0]),
                                                       " / ".join(commands.set_command_group[0]),
                                                       "已添加为命令组"), target_id, 1)
        elif target_id in botdata.talk_group:
            send_group_person_msg(botmsg.at_msg.format(" / ".join(commands.set_talk_group[0]),
                                                       " / ".join(commands.set_command_group[0]),
                                                       "已添加为聊天组"), target_id, 1)
        else:
            send_group_person_msg(botmsg.at_msg.format(" / ".join(commands.set_talk_group[0]),
                                                       " / ".join(commands.set_command_group[0]),
                                                       "未添加为任何组"), target_id, 1)
    elif msg_c[0] == "(met)" + botid + "(met)" and len(msg_c) > 1:
        if userid in botdata.admins:
            if msg_c[1] in commands.set_talk_group[0]:
                if target_id in botdata.talk_group:
                    save_botdata("talk_group", target_id, False)
                    send_group_person_msg(botmsg.del_talk_group.format(target_id), target_id, 1)
                else:
                    save_botdata("talk_group", target_id, True)
                    send_group_person_msg(botmsg.add_talk_group.format(target_id), target_id, 1)
            elif msg_c[1] in commands.set_command_group[0]:
                if target_id == botdata.command_group[0]:
                    save_botdata("command_group", target_id, False)
                    send_group_person_msg(botmsg.del_command_group.format(target_id), target_id, 1)
                else:
                    if botdata.command_group:
                        send_group_person_msg(botmsg.already_add_command_group.format(botdata.command_group),
                                              target_id, 1)
                    else:
                        save_botdata("command_group", target_id, True)
                        send_group_person_msg(botmsg.add_command_group.format(target_id), target_id, 1)
        else:
            send_group_person_msg(botmsg.not_admin.format(username), target_id, 1)


# bound系统
def bound_player(userid: str, msg_c: list, target_id: str):
    user_list = get_user_list()
    if debug_status:
        __mcdr_server.logger.info(f"获取到玩家列表：{user_list}")
    if userid in user_list.keys():  # 检测玩家是否已经绑定
        send_group_person_msg(botmsg.already_bound.format("(met)" + userid + "(met)",
                                                          user_list[userid]), target_id, 1)
    elif msg_c[1] in user_list.values():  # 查看id是否已存在
        player_id_kook = list(user_list.keys())[list(user_list.values()).index(msg_c[1])]
        send_group_person_msg(botmsg.already_be_bound.format("(met)" + userid + "(met)",
                                                             user_list[userid], "(met)" + player_id_kook + "(met)"),
                              target_id, 1)
    else:
        if real_name(msg_c[1]) or not config.online_mode:
            if send_user_list(userid, msg_c[1]):  # 进行绑定
                if config.whitelist_add_with_bound:  # 是否添加白名单
                    send_execute_mc(f'whitelist add {msg_c[1]}')
                    send_group_person_msg(botmsg.fin_bound.format("(met)" + userid + "(met)"), target_id, 1)
                else:
                    send_execute_mc(f'whitelist reload')
                    send_group_person_msg(botmsg.fin_bound_without_whitelist.format("(met)" + userid + "(met)",
                                                                                    config.why_no_whitelist),
                                          target_id, 1)
            else:
                send_group_person_msg(botmsg.error_player_name.format("(met)" + userid + "(met)"), target_id, 1)
        else:
            send_group_person_msg(botmsg.worng_player_name.format("(met)" + userid + "(met)"), target_id, 1)


# 处理私聊命令
def parse_person_command(msg: str, username: str, userid: str):
    global wait_admin, server_list_number, server_list_id
    msg = msg.split()
    if msg[0] in commands.help[0]:
        send_group_person_msg(botmsg.person_help.format(person_help), userid, 0)
    elif msg[0] in commands.admin_help[0]:
        if userid in botdata.admins:
            send_group_person_msg(botmsg.admin_person_help.format(username, admin_person_help), userid, 0)
        else:
            send_group_person_msg(botmsg.not_admin.format(username), userid, 0)
    elif msg[0] in commands.get_admin[0]:
        __mcdr_server.logger.info(f"{username}({userid})正在获取管理员权限，使用命令 !!kt admin allow 确认其管理员身份！")
        wait_admin = userid
        send_group_person_msg(botmsg.get_admin_msg, userid, 0)
    elif msg[0] in commands.set_server[0] and len(msg) > 1:
        if userid in botdata.admins:
            if msg[1] in commands.set_server_list[0]:
                server_list_id = []
                server_list_number = 0
                res = get_msg("/guild/list")
                if res:
                    if res['code'] == 0:
                        send_group_person_msg(botmsg.found_server_list.format(" / ".join(commands.set_server[0]),
                                                                              " / ".join(commands.set_server_add[0])),
                                              userid, 0)
                        already_add_server_list = copy.copy(botdata.server_list)
                        for i in res['data']['items']:
                            server_list_number += 1
                            server_list_id.append(i['id'])
                            if i['id'] in already_add_server_list:
                                send_group_person_msg(f"{server_list_number}. {i['name']}({i['id']})(已添加)", userid,
                                                      0)
                                already_add_server_list.remove(i['id'])
                            else:
                                send_group_person_msg(f"{server_list_number}. {i['name']}({i['id']})", userid, 0)
                        for i in already_add_server_list:
                            server_list_number += 1
                            server_list_id.append(i)
                            res_name = get_msg(f"/guild/view?guild_id={i}")
                            send_group_person_msg(f"{server_list_number}. {res_name['data']['name']}({i})(已添加)",
                                                  userid,
                                                  0)
                            already_add_server_list.remove(i)
                    else:
                        send_group_person_msg(botmsg.cant_get_server_list, userid, 0)
                else:
                    send_group_person_msg(botmsg.cant_get_server_list, userid, 0)
            elif len(msg) == 3 and msg[1] in commands.set_server_add[0]:
                if server_list_number != 0:
                    if int(msg[2]) <= server_list_number:
                        if not server_list_id[int(msg[2]) - 1] in botdata.server_list:
                            save_botdata("server_list", server_list_id[int(msg[2]) - 1], True)
                            send_group_person_msg(botmsg.add_server.format(server_list_id[int(msg[2]) - 1]), userid, 0)
                        else:
                            send_group_person_msg(botmsg.already_add_server.format(server_list_id[int(msg[2]) - 1]),
                                                  userid, 0)
                else:
                    send_group_person_msg(botmsg.cant_found_server_list.format(" / ".join(commands.set_server[0]),
                                                                               " / ".join(commands.set_server_list[0])),
                                          userid, 0)
            elif len(msg) != 3 and msg[1] in commands.set_server_add[0]:
                send_group_person_msg(botmsg.add_server_help.format(" / ".join(commands.set_server[0]),
                                                                    " / ".join(commands.set_server_add[0])),
                                      userid, 0)
            elif len(msg) == 3 and msg[1] in commands.set_server_del[0]:
                if server_list_number != 0:
                    if server_list_id[int(msg[2]) - 1] in botdata.server_list:
                        save_botdata("server_list", server_list_id[int(msg[2]) - 1], False)
                        send_group_person_msg(botmsg.del_server.format(server_list_id[int(msg[2]) - 1]), userid, 0)
                    else:
                        send_group_person_msg(botmsg.already_del_server.format(server_list_id[int(msg[2]) - 1]),
                                              userid, 0)
                else:
                    send_group_person_msg(botmsg.cant_found_server_list.format(" / ".join(commands.set_server[0]),
                                                                               " / ".join(commands.set_server_list[0])),
                                          userid, 0)
            elif len(msg) != 3 and msg[1] in commands.set_server_del[0]:
                send_group_person_msg(botmsg.del_server_help.format(" / ".join(commands.set_server[0]),
                                                                    " / ".join(commands.set_server_del[0])),
                                      userid, 0)
            else:
                send_group_person_msg(botmsg.person_help, userid, 0)
        else:
            send_group_person_msg(botmsg.not_admin.format(username), userid, 0)
    elif msg[0] in commands.set_server[0] and len(msg) == 1:
        send_group_person_msg(botmsg.help_set_server.format(set_server_help), userid, 0)
    elif msg[0] in commands.bound[0] and len(msg) > 1:
        user_list = get_user_list()
        # check 命令
        if msg[1] in commands.bound_check[0] and len(msg) == 4:
            if msg[2] in commands.bound_kook[0]:
                if msg[3] in user_list.keys():
                    send_group_person_msg(botmsg.person_bound_check_found.format(user_list[msg[3]],
                                                                                 msg[3]), userid, 0)
                else:
                    send_group_person_msg(botmsg.person_bound_check_cant_found.format(msg[3]), userid, 0)
            elif msg[2] in commands.bound_player[0]:
                if msg[3] in user_list.values():
                    player_id_kook = list(user_list.keys())[list(user_list.values()).index(msg[3])]
                    send_group_person_msg(botmsg.person_bound_check_found.format(msg[3],
                                                                                 player_id_kook), userid, 0)
                else:
                    send_group_person_msg(botmsg.person_bound_check_cant_found.format(msg[3]), userid, 0)
            else:
                send_group_person_msg(botmsg.person_bound_unbound_check_error.format(' / '.join(commands.bound[0]),
                                                                                     ' / '.join(
                                                                                         commands.bound_check[0]),
                                                                                     ' / '.join(
                                                                                         commands.bound_player[0]) +
                                                                                     ' / ' +
                                                                                     ' / '.join(
                                                                                         commands.bound_kook[0])),
                                      userid, 0)
        elif msg[1] in commands.bound_check[0] and len(msg) != 4:
            send_group_person_msg(botmsg.person_bound_unbound_check_error.format(' / '.join(commands.bound[0]),
                                                                                 ' / '.join(
                                                                                     commands.bound_check[0]),
                                                                                 ' / '.join(
                                                                                     commands.bound_player[0]) +
                                                                                 ' / ' +
                                                                                 ' / '.join(
                                                                                     commands.bound_kook[0])),
                                  userid, 0)
        # list 命令
        elif msg[1] in commands.bound_list[0] and len(msg) == 2:
            if userid in botdata.admins:
                bound_list = [f'{a} - {b}' for a, b in user_list.items()]
                reply_msg = copy.copy(botmsg.person_bound_list)
                for i in range(0, len(bound_list)):
                    reply_msg += f'{i + 1}. {bound_list[i]}\n'
                reply_msg = copy.copy(botmsg.person_bound_cant_list.format(config.server_name)) if reply_msg == '' else\
                    reply_msg
                send_group_person_msg(reply_msg, userid, 0)
            else:
                send_group_person_msg(botmsg.not_admin.format(username), userid, 0)
        elif msg[1] in commands.bound_list[0] and len(msg) != 2:
            send_group_person_msg(botmsg.person_bound_list_error.format(' / '.join(commands.bound[0]),
                                                                        ' / '.join(commands.bound_list[0])),
                                  userid, 0)
        # unbound 命令
        elif msg[1] in commands.bound_unbound[0] and len(msg) == 4:
            if userid in botdata.admins:
                if msg[2] in commands.bound_kook[0]:
                    if msg[3] in user_list.keys():
                        if config.whitelist_add_with_bound:
                            player_name = user_list[msg[3]]
                            send_execute_mc(f'whitelist remove {player_name}')
                            delete_user(msg[3])
                            send_group_person_msg(botmsg.person_bound_unbound_with_whitelist_fin.format(player_name,
                                                                                                        msg[3]),
                                                  userid, 0)
                        else:
                            player_name = user_list[msg[3]]
                            delete_user(msg[3])
                            send_group_person_msg(botmsg.person_bound_unbound_fin.format(player_name, msg[3]),
                                                  userid, 0)
                    else:
                        send_group_person_msg(botmsg.person_bound_unbound_cant_player.format(msg[3]), userid, 0)
                elif msg[2] in commands.bound_player[0]:
                    if msg[3] in user_list.values():
                        player_id_kook = list(user_list.keys())[list(user_list.values()).index(msg[3])]
                        if config.whitelist_add_with_bound:
                            send_execute_mc(f'whitelist remove {msg[3]}')
                            delete_user(player_id_kook)
                            send_group_person_msg(botmsg.person_bound_unbound_with_whitelist_fin.format(msg[3],
                                                                                                        player_id_kook),
                                                  userid, 0)
                        else:
                            delete_user(player_id_kook)
                            send_group_person_msg(botmsg.person_bound_unbound_fin.format(msg[3], player_id_kook),
                                                  userid, 0)
                    else:
                        send_group_person_msg(botmsg.person_bound_unbound_cant_player.format(msg[3]), userid, 1)
                else:
                    send_group_person_msg(botmsg.person_bound_unbound_check_error.format(' / '.join(commands.bound[0]),
                                                                                         ' / '.join(
                                                                                             commands.bound_unbound[0]),
                                                                                         ' / '.join(
                                                                                             commands.bound_player[0]) +
                                                                                         ' / ' +
                                                                                         ' / '.join(
                                                                                             commands.bound_kook[0])),
                                          userid, 0)
            else:
                send_group_person_msg(botmsg.not_admin.format(username), userid, 0)
        elif msg[1] in commands.bound_unbound[0] and len(msg) != 4:
            send_group_person_msg(botmsg.person_bound_unbound_check_error.format(' / '.join(commands.bound[0]),
                                                                                 ' / '.join(
                                                                                     commands.bound_unbound[0]),
                                                                                 ' / '.join(
                                                                                     commands.bound_player[0]) +
                                                                                 ' / ' +
                                                                                 ' / '.join(
                                                                                     commands.bound_kook[0])),
                                  userid, 0)
        else:
            if userid in botdata.admins:
                send_group_person_msg(botmsg.person_bound_admin_help.format(admin_bound_help), userid, 0)
            else:
                send_group_person_msg(botmsg.person_bound_help.format(bound_help), userid, 0)
    elif msg[0] in commands.bound[0] and len(msg) == 1:
        if userid in botdata.admins:
            send_group_person_msg(botmsg.person_bound_admin_help.format(admin_bound_help), userid, 0)
        else:
            send_group_person_msg(botmsg.person_bound_help.format(bound_help), userid, 0)
    else:
        send_group_person_msg(botmsg.nothing_msg.format(" / ".join(commands.help[0])), userid, 0)


# -------------------------
# Tools event listener
# -------------------------
# 消息转发处理
def turn_msg(userid: str, target_id: str, msg: str, command_talk: bool):
    user_list = get_user_list()
    if userid in user_list.keys():
        __mcdr_server.say(f"§7[KOOK][{user_list[userid]}] {msg}")  # 转发消息
    else:
        if command_talk:
            send_group_person_msg(botmsg.need_bound.format(f"(met){userid}(met)",
                                                           config.command_prefix +
                                                           f" / {config.command_prefix}".join(commands.bound[0])),
                                  target_id, 1)
        else:
            send_group_person_msg(botmsg.need_bound.format(f"(met){userid}(met)", " / ".join(commands.bound[0])),
                                  target_id, 1)


# 整合获取用户
def get_user_list():
    if config.mysql_enable:
        return dict(connect_and_query_db("kook_id,player_id", "user_list", config.mysql_config))
    else:
        return data


# 检测玩家名是否存在
def real_name(username: str):
    # 定义Minecraft API的URL
    url_m = "https://api.mojang.com/users/profiles/minecraft/{}"
    # 发送GET请求到Minecraft API
    response = requests.get(url_m.format(username))

    # 检查响应状态码
    if response.status_code == 200:
        # 如果状态码为200，则表示玩家用户名存在
        return True
    else:
        # 如果状态码不为200，则表示玩家用户名不存在
        return False


# 整合绑定用户
def send_user_list(send_id: str, name: str):
    pattern = r'[^a-zA-Z0-9_]'
    if not re.search(pattern, name):
        if config.mysql_enable:
            if config.main_server:
                db_data = (send_id, name)
                connect_and_insert_db("kook_id,player_id", "user_list", db_data, config.mysql_config)
                return True
            return True
        else:
            data[send_id] = name  # 进行绑定
            save_data(__mcdr_server)
            return True
    else:
        return False


# 整合删除用户
def delete_user(send_id: str):
    if config.mysql_enable:
        if config.main_server:
            connect_and_delete_data("user_list", f"kook_id = {send_id}", config.mysql_config)
    else:
        del data[send_id]
        save_data(__mcdr_server)


# 把命令执行独立出来，以防服务器处在待机状态
def send_execute_mc(command: str):
    global wait_list
    if __mcdr_server.is_server_running():  # 确认服务器是否启动
        __mcdr_server.execute(command)
        __mcdr_server.logger.info(f"KookTools execute:{command}")
    else:
        wait_list.append(command)  # 堆着等开服
        __mcdr_server.logger.info(f"KookTools can't execute:{command}, The list of commands:{str(wait_list)}")


# 获取白名单
def get_whitelist():
    name_list = []
    with open(config.whitelist_path, 'r', encoding='utf8') as fp:
        json_data = json.load(fp)
        for i in json_data:
            name_list.append(i['name'])
        return name_list


# 集合处理
def get_diff_list(set1: list, set2: list):
    if set1 and set2:
        set1 = set(set1)
        set2 = set(set2)
        diff = set1 - set2
        return list(diff)
    else:
        return set1


# -------------------------
# Config editor event listener
# -------------------------
# 修改Botdata
def save_botdata(option: str, input_sth: str, add: bool = False):
    global botdata
    if option == "command_group":
        if add:
            botdata.command_group = input_sth
        else:
            botdata.command_group = ""
    elif option == "talk_group":
        if add:
            botdata.talk_group.append(input_sth)
        else:
            botdata.talk_group.remove(input_sth)
    elif option == "server_list":
        if add:
            botdata.server_list.append(input_sth)
        else:
            botdata.server_list.remove(input_sth)
    botdata_n = {
        "server_list": botdata.server_list,
        "admins": botdata.admins,
        "talk_group": botdata.talk_group,
        "command_group": botdata.command_group
    }
    __mcdr_server.save_config_simple(botdata_n, 'botdata.json')
    botdata = __mcdr_server.load_config_simple('botdata.json', target_class=bot_data)


# 添加机器人管理员
def add_admin():
    global botdata
    if debug_status:
        __mcdr_server.logger.info(botdata.server_list)
    botdata.admins.append(wait_admin)
    botdata_n = {
        "server_list": botdata.server_list,
        "admins": botdata.admins,
        "talk_group": botdata.talk_group,
        "command_group": botdata.command_group
    }
    __mcdr_server.save_config_simple(botdata_n, 'botdata.json')
    botdata = __mcdr_server.load_config_simple('botdata.json', target_class=bot_data)
    __mcdr_server.logger.info("已为其获取Admin权限！")


# 保存data
def save_data(server: PluginServerInterface):
    server.save_config_simple({'data': data}, 'data.json')


# -------------------------
# MCDR event listener
# -------------------------
# 插件加载
def on_load(server: PluginServerInterface, _):
    global __mcdr_server, config, debug_status, stop_status, botdata, botmsg, server_list_number, server_list_id, data
    global online_players, commands, wait_list, server_first_start, start_time1
    # 变量初始化
    start_time1 = time.perf_counter()
    __mcdr_server = server  # 导入mcdr
    config = __mcdr_server.load_config_simple(target_class=Config)
    botdata = __mcdr_server.load_config_simple('botdata.json', target_class=bot_data)
    botmsg = __mcdr_server.load_config_simple('botmsg.json', target_class=BotMsg)
    commands = __mcdr_server.load_config_simple('commands.json', target_class=Commands)
    debug_status = config.debug
    stop_status = False
    server_list_number = 0
    server_list_id = []
    online_players = []
    wait_list = []
    server_first_start = True
    make_help_msg()

    # 命令初始化
    builder = SimpleCommandBuilder()
    # declare your commands
    builder.command('!!kt admin allow', add_admin)
    # done, now register the commands to the server
    builder.register(server)

    if not config.mysql_enable:
        data = server.load_config_simple(
            'data.json',
            default_config={'data': {}},
            echo_in_console=False
        )['data']

    if not config.mysql_enable:  # 未开启mysql功能
        # 主服务器启动
        if config.main_server:
            __mcdr_server.logger.info("机器人正在启动……")
            start_kook_bot()
            get_server(config.main_server_host, config.main_server_port)
            group_servers_websocket()
    elif config.mysql_enable and mysql:  # 启用mysql功能且mysql-connector-python已安装
        MySQL_Control.create_table_if_not_exists("user_list", "id INT AUTO_INCREMENT PRIMARY KEY,kook_id VARCHAR(15),"
                                                              "player_id VARCHAR(20),event_time TIMESTAMP DEFAULT "
                                                              "CURRENT_TIMESTAMP", config.mysql_config)
        __mcdr_server.logger.info("MySQL数据库功能已正常启动！")
        # 主服务器启动
        if config.main_server:
            __mcdr_server.logger.info("机器人正在启动……")
            start_kook_bot()
            get_server(config.main_server_host, config.main_server_port)
            group_servers_websocket()
    elif config.mysql_enable and not mysql:
        __mcdr_server.logger.error("KookTools无法启动，请安装mysql-connector-python或关闭数据库功能！")


# 插件卸载
def on_unload(_):
    global stop_status
    stop_status = True
    __mcdr_server.logger.info("机器人开始关闭，正在等待关闭成功信号……")
    while not fin_stop_status:
        time.sleep(0.5)


# 自动转发到Kook
def on_user_info(_, info):
    if botdata.talk_group:
        msg = info.content
        if config.forwards_mcdr_command:
            for i in botdata.talk_group:
                send_group_person_msg(f'[{info.player}] {info.content}', i, 1)
        else:
            if msg[0:2] != '!!':
                for i in botdata.talk_group:
                    send_group_person_msg(f'[{info.player}] {info.content}', i, 1)


# 在线玩家检测
def on_player_joined(_, player, __):
    global online_players
    if player not in online_players:
        online_players.append(player)
    for i in botdata.talk_group:
        send_group_person_msg(f'{player} 加入游戏', i, 1)


def on_player_left(_, player):
    global online_players
    if player in online_players:
        online_players.remove(player)
    for i in botdata.talk_group:
        send_group_person_msg(f'{player} 退出游戏', i, 1)


def on_server_startup(_):
    global server_first_start
    if wait_list:  # 服务器核心重启后处理堆积命令
        for i in wait_list:
            send_execute_mc(i)
            time.sleep(0.5)
    if config.mysql_enable and config.whitelist_add_with_bound:
        db_player_list = connect_and_query_db("player_id", "user_list", config.mysql_config)
        result_list = [element for tup in db_player_list for element in tup]
        if debug_status:
            __mcdr_server.logger.info(f"UserList: {result_list}")
            __mcdr_server.logger.info(f"WhiteList: {get_whitelist()}")
        diff_player = get_diff_list(  # 检查数据库有没有新的玩家
            result_list,
            get_whitelist()
        )
        if diff_player:
            for i in diff_player:
                __mcdr_server.logger.info(f"New Player! Name:{i}")
                send_execute_mc(f'whitelist add {i}')  # 加一下新玩家
                time.sleep(0.5)

        diff_player = get_diff_list(  # 检查数据库有没有老的玩家
            get_whitelist(),
            result_list
        )
        if diff_player:
            for i in diff_player:
                __mcdr_server.logger.info(f"Wrong Player! Name:{i}")
                send_execute_mc(f'whitelist remove {i}')  # 删一下老玩家
                time.sleep(0.5)

    if config.forwards_server_start_and_stop:
        start_time2 = time.perf_counter()
        if server_first_start:
            msg_start = botmsg.start_server.format(config.server_name, start_time2 - start_time1)
            server_first_start = False
        else:
            msg_start = botmsg.restart_server.format(config.server_name)
        for i in botdata.talk_group:
            send_group_person_msg(msg_start, i, 1)


def on_server_stop(_, __):
    if config.forwards_server_start_and_stop:
        msg_stop = botmsg.stop_server.format(config.server_name)
        for i in botdata.talk_group:
            send_group_person_msg(msg_stop, i, 1)
