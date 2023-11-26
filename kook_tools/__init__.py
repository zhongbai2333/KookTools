import asyncio
import json
import time

import requests
import websockets
from mcdreforged.api.all import *

from .config import Config, Admins, Talk_group, ServerList

global __mcdr_server, config, debug_status, stop_status, sn, server_restart, session_id, heart_start, url, pong_back
global heart_stop, server_start, fin_stop_status, wait_admin, admins, talk_group, server_list


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
    async with websockets.connect(uri) as websocket:
        __mcdr_server.logger.info(f"websocket服务器连接成功！")
        if server_start:  # 检查是否第一次启动
            await asyncio.gather(get_service(websocket), bot_heart(websocket))
        else:
            await asyncio.gather(get_service(websocket))  # 如果两个async同时启动居然苏都不够快，来不及获取第一个包呜呜呜
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
                        parse_get_msg(response_dict, "parse")
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
                parse_get_msg(response_dict, "parse")  # 将数据包转交给另一个线程处理数据
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


# 机器人发送Get系统
# 机器人event处理系统
@new_thread('parse_get_msg')
def parse_get_msg(msg, mode: str):
    if mode == "parse":
        if msg['d']['channel_type'] == "GROUP":
            if debug_status:
                __mcdr_server.logger.info(f"收到群聊消息！发送者：{msg['d']['extra']['author']['username']}"
                                          f"({msg['d']['author_id']}),"
                                          f"于文字聊天室“{msg['d']['extra']['channel_name']}({msg['d']['target_id']})”发送，"
                                          f"内容为：{msg['d']['content']}")
            if (msg['d']['extra']['server_list'] in server_list.server_list and
                    msg['d']['target_id'] == config.command_group):
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
            parse_person_command(msg['d']['content'], msg['d']['extra']['author']['username'], msg['d']['author_id'],
                                 msg['d']['target_id'])
    elif mode == "get":
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
    msg = msg.split(" ")
    if msg[0] == "help" or msg[0] == "帮助":
        __mcdr_server.logger.info("收到群聊帮助命令")
        send_group_person_msg("看什么看？没见本大爷忙着吗！帮助你？纸条自己拿去看！", target_id, 0)
        send_group_person_msg('''尾巴大爷拿出张纸条，上面写着：
                help / 帮助 -- 获取帮助信息       
                admin_help / 管理员帮助 -- 获取管理员帮助列表
                ''', target_id, 0)
    else:
        send_group_person_msg("有什么事？如果你开口“帮助”问问我说不定我会给你点提示", target_id, 1)


# 处理私聊命令
def parse_person_command(msg: str, username: str, userid: str, target_id: str):
    global wait_admin
    msg = msg.split(" ")
    if msg[0] == "help" or msg[0] == "帮助":
        __mcdr_server.logger.info("收到私聊帮助命令")
        send_group_person_msg("看什么看？没见本大爷忙着吗！帮助你？纸条自己拿去看！", userid, 0)
        send_group_person_msg('''一张字条被贴在屏幕上，上面写着：
        help / 帮助 -- 获取帮助信息       
        get_admin / 获取管理员 -- 将当前用户添加至管理员（需后台验证）
        admin_help / 管理员帮助 -- 获取管理员帮助列表
        ''', userid, 0)
    elif msg[0] == "admin_help" or msg[0] == "管理员帮助":
        if userid in admins.admins:
            send_group_person_msg(f"哼~ {username} ，管理员帮助列表自己拿去看", userid, 0)
            send_group_person_msg('''一张字条被贴在屏幕上，上面写着：
            set_server / 设置服务器 -- 获取机器人在的服务器并选择管理哪些
            set_command_group / 设置频道组 -- 设置机器人需要处理命令的频道
            set_talk_group / 设置聊天组 -- 设置机器人需要转发消息的频道
            ''', userid, 0)
        else:
            send_group_person_msg(f"哼~ {username} ，你是个屁管理员，滚！", userid, 0)
    elif msg[0] == "get_admin" or msg[0] == "获取管理员":
        __mcdr_server.logger.info(f"{username}({userid})正在获取管理员权限，使用命令 !!kt admin allow 确认其管理员身份！")
        wait_admin = userid
        send_group_person_msg("去去去，去后台要权限吧！", userid, 0)
    else:
        send_group_person_msg(f"{username} 有什么事？如果你开口“帮助”问问我说不定我会给你点提示", userid, 0)


# 添加机器人管理员
def add_admin():
    admins_list = admins.admins
    admins_list.append(wait_admin)
    __mcdr_server.save_config_simple({'admins': admins_list}, 'admin.json')
    __mcdr_server.logger.info("已为其获取Admin权限！")


# 插件加载
def on_load(server: PluginServerInterface, _):
    global __mcdr_server, config, debug_status, stop_status, admins, talk_group, server_list
    # 变量初始化
    __mcdr_server = server  # 导入mcdr
    config = __mcdr_server.load_config_simple(target_class=Config)
    admins = __mcdr_server.load_config_simple('admin.json', target_class=Admins)
    talk_group = __mcdr_server.load_config_simple('TalkGroup.json', target_class=Talk_group)
    server_list = __mcdr_server.load_config_simple('ServerList.json', target_class=ServerList)
    debug_status = config.debug
    stop_status = False

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
