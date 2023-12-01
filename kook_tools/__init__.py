import asyncio
import json
import time
import copy

import requests
import websockets
from mcdreforged.api.all import *

from .config import Config, bot_data, BotMsg

global __mcdr_server, config, debug_status, stop_status, sn, server_restart, session_id, heart_start, url, pong_back
global heart_stop, server_start, fin_stop_status, wait_admin, botdata, botmsg, server_list_number, server_list_id
global botid, botname


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
            parse_person_command(msg['d']['content'], msg['d']['extra']['author']['username'], msg['d']['author_id'])


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
        data = {
            "target_id": target_id,
            "content": msg
        }
        header = {"Authorization": f"Bot {config.token}"}  # 写入token
        gateway_uri = f"/api/v{str(config.api_version)}"  # 写入api版本
        uri_p = "/direct-message/create"
        post = requests.post(url=config.uri + gateway_uri + uri_p, json=data, headers=header)
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
        data = {
            "target_id": target_id,
            "content": msg
        }
        header = {"Authorization": f"Bot {config.token}"}  # 写入token
        gateway_uri = f"/api/v{str(config.api_version)}"  # 写入api版本
        uri_p = "/message/create"
        post = requests.post(url=config.uri + gateway_uri + uri_p, json=data, headers=header)
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
    if (target_id in botdata.talk_group and target_id in botdata.command_group
            and userid != botid and msg_c[0] != "(met)"+botid+"(met)"):
        if target_id in botdata.talk_group and target_id in botdata.command_group:
            if msg[0] == "#":
                msg_c = msg[1:].split()
                if msg_c[0] == "help" or msg_c[0] == "帮助":
                    send_group_person_msg(botmsg.group_help, target_id, 1)
            else:
                __mcdr_server.logger.info("_________________")
        elif target_id in botdata.talk_group:
            __mcdr_server.logger.info("_________________")
        elif target_id in botdata.command_group:
            if msg_c[0] == "help" or msg_c[0] == "帮助":
                send_group_person_msg(botmsg.group_help, target_id, 1)
    elif msg_c[0] == "(met)"+botid+"(met)" and len(msg_c) <= 1:
        if target_id in botdata.command_group and target_id in botdata.talk_group:
            send_group_person_msg(botmsg.at_msg.format("已添加聊天组和命令组"), target_id, 1)
        elif target_id in botdata.command_group:
            send_group_person_msg(botmsg.at_msg.format("已添加命令组"), target_id, 1)
        elif target_id in botdata.talk_group:
            send_group_person_msg(botmsg.at_msg.format("已添加聊天组"), target_id, 1)
        else:
            send_group_person_msg(botmsg.at_msg.format("未添加为任何组"), target_id, 1)
    elif msg_c[0] == "(met)" + botid + "(met)" and len(msg_c) > 1:
        if userid in botdata.admins:
            if msg_c[1] == "设置聊天组" or msg_c[1] == "set_talk_group":
                if target_id in botdata.talk_group:
                    save_botdata("talk_group", target_id, False)
                    send_group_person_msg(botmsg.del_talk_group.format(target_id), target_id, 1)
                else:
                    save_botdata("talk_group", target_id, True)
                    send_group_person_msg(botmsg.add_talk_group.format(target_id), target_id, 1)
            elif msg_c[1] == "设置命令组" or msg_c[1] == "set_command_group":
                if target_id == botdata.command_group:
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


# 处理私聊命令
def parse_person_command(msg: str, username: str, userid: str):
    global wait_admin, server_list_number, server_list_id
    msg = msg.split()
    if msg[0] == "help" or msg[0] == "帮助":
        send_group_person_msg(botmsg.person_help, userid, 0)
    elif msg[0] == "admin_help" or msg[0] == "管理员帮助":
        if userid in botdata.admins:
            send_group_person_msg(botmsg.admin_person_help.format(username), userid, 0)
        else:
            send_group_person_msg(botmsg.not_admin.format(username), userid, 0)
    elif msg[0] == "get_admin" or msg[0] == "获取管理员":
        __mcdr_server.logger.info(f"{username}({userid})正在获取管理员权限，使用命令 !!kt admin allow 确认其管理员身份！")
        wait_admin = userid
        send_group_person_msg(botmsg.get_admin_msg, userid, 0)
    elif msg[0] == "set_server" or msg[0] == "设置服务器":
        if userid in botdata.admins:
            if msg[1] == "list" or msg[1] == "列表":
                server_list_id = []
                server_list_number = 0
                res = get_msg("/guild/list")
                if res:
                    if res['code'] == 0:
                        send_group_person_msg(botmsg.found_server_list, userid, 0)
                        already_add_server_list = copy.copy(botdata.server_list)
                        for i in res['data']['items']:
                            server_list_number += 1
                            server_list_id.append(i['id'])
                            if i['id'] in already_add_server_list:
                                send_group_person_msg(f"{server_list_number}. {i['name']}({i['id']})(已添加)", userid, 0)
                                already_add_server_list.remove(i['id'])
                            else:
                                send_group_person_msg(f"{server_list_number}. {i['name']}({i['id']})", userid, 0)
                        for i in already_add_server_list:
                            server_list_number += 1
                            server_list_id.append(i)
                            res_name = get_msg(f"/guild/view?guild_id={i}")
                            send_group_person_msg(f"{server_list_number}. {res_name['data']['name']}({i})(已添加)", userid,
                                                  0)
                            already_add_server_list.remove(i)
                    else:
                        send_group_person_msg(botmsg.cant_get_server_list, userid, 0)
                else:
                    send_group_person_msg(botmsg.cant_get_server_list, userid, 0)
            elif len(msg) == 3 and msg[1] == "add" or msg[1] == "添加":
                if server_list_number != 0:
                    if int(msg[2]) <= server_list_number:
                        if not server_list_id[int(msg[2]) - 1] in botdata.server_list:
                            save_botdata("server_list", server_list_id[int(msg[2]) - 1], True)
                            send_group_person_msg(botmsg.add_server.format(server_list_id[int(msg[2]) - 1]), userid, 0)
                        else:
                            send_group_person_msg(botmsg.already_add_server.format(server_list_id[int(msg[2]) - 1]),
                                                  userid, 0)
                else:
                    send_group_person_msg(botmsg.cant_found_server_list, userid, 0)
            elif len(msg) != 3 and msg[1] == "add" or msg[1] == "添加":
                send_group_person_msg(botmsg.add_server_help, userid, 0)
            elif len(msg) == 3 and msg[1] == "del" or msg[1] == "删除":
                if server_list_number != 0:
                    if server_list_id[int(msg[2]) - 1] in botdata.server_list:
                        save_botdata("server_list", server_list_id[int(msg[2]) - 1], False)
                        send_group_person_msg(botmsg.del_server.format(server_list_id[int(msg[2]) - 1]), userid, 0)
                    else:
                        send_group_person_msg(botmsg.already_del_server.format(server_list_id[int(msg[2]) - 1]),
                                              userid, 0)
                else:
                    send_group_person_msg(botmsg.cant_found_server_list, userid, 0)
            elif len(msg) != 3 and msg[1] == "del" or msg[1] == "删除":
                send_group_person_msg(botmsg.del_server_help, userid, 0)
            else:
                send_group_person_msg(botmsg.person_help, userid, 0)
        else:
            send_group_person_msg(botmsg.not_admin.format(username), userid, 0)
    else:
        send_group_person_msg(botmsg.nothing_msg, userid, 0)


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


# 插件加载
def on_load(server: PluginServerInterface, _):
    global __mcdr_server, config, debug_status, stop_status, botdata, botmsg, server_list_number, server_list_id
    # 变量初始化
    __mcdr_server = server  # 导入mcdr
    config = __mcdr_server.load_config_simple(target_class=Config)
    botdata = __mcdr_server.load_config_simple('botdata.json', target_class=bot_data)
    botmsg = __mcdr_server.load_config_simple('botmsg.json', target_class=BotMsg)
    debug_status = config.debug
    stop_status = False
    server_list_number = 0
    server_list_id = []

    # 命令初始化
    builder = SimpleCommandBuilder()
    # declare your commands
    builder.command('!!kt admin allow', add_admin)
    # done, now register the commands to the server
    builder.register(server)

    # 主服务器启动
    if config.main_server:
        __mcdr_server.logger.info("机器人正在启动……")
        start_kook_bot()


# 插件卸载
def on_unload(_):
    global stop_status
    stop_status = True
    __mcdr_server.logger.info("机器人开始关闭，正在等待关闭成功信号……")
    while not fin_stop_status:
        time.sleep(0.5)
