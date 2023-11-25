import asyncio
import json
import requests
import websockets
from mcdreforged.api.all import *

from .config import Config

global __mcdr_server, config, debug_status, stop_status, sn, server_restart, session_id, heart_start, url, pong_back
global heart_stop, server_start


# -------------------------
# WebSocket event listener
# -------------------------
@new_thread('KookBot')
def start_kook_bot():
    global server_restart, url, heart_start, heart_stop, server_start
    heart_start = False
    heart_stop = False
    server_restart = False
    server_start = False
    while True:
        if not stop_status:
            if server_restart:
                url_r = url + f"&resume=1&sn={sn}&session_id={session_id}"  # 重制重试地址
                asyncio.run(get_websocket(url_r))
            else:
                url = get_gateway()
                if url:
                    asyncio.run(get_websocket(url))
                else:
                    __mcdr_server.logger.error("机器人启动失败！")
                    break
        else:
            break


# 获取gateway地址
def get_gateway() -> str:
    if config.token:
        header = {"Authorization": f"Bot {config.token}"}
        gateway_uri = f"/api/v{str(config.api_version)}/gateway/index?compress=0"
        # 发送请求
        get = requests.get(config.uri + gateway_uri, headers=header)
        # 返回地址
        if get.text:
            json_dict = json.loads(get.text)
            if debug_status:
                __mcdr_server.logger.info(f"获取到websocket地址：{json_dict['data']['url']}")
            return json_dict['data']['url']
        else:
            __mcdr_server.logger.error("websocket地址获取失败")
            return ""
    else:
        __mcdr_server.logger.error("未找到token！")
        return ""


async def get_websocket(uri: str) -> None:
    async with websockets.connect(uri) as websocket:
        __mcdr_server.logger.info(f"websocket服务器连接成功！")
        if server_start:
            await asyncio.gather(get_service(websocket), bot_heart(websocket))
        else:
            await asyncio.gather(get_service(websocket))
            await asyncio.gather(get_service(websocket), bot_heart(websocket))


# 机器人接收数据包系统
async def get_service(websocket):
    global session_id, sn, heart_start, server_restart, pong_back, heart_stop, server_start
    if debug_status:
        __mcdr_server.logger.info(f"机器人接收数据包系统启动！")
    while True:
        if server_restart:
            retry = 0
            while retry < 3:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=8)
                    if debug_status:
                        __mcdr_server.logger.info(f"已收到数据包！")
                    response_dict = json.loads(response)
                    if response_dict['s'] == 6:
                        __mcdr_server.logger.info(f"Gateway重连成功！")
                        server_restart = False
                        heart_start = True
                        break
                except asyncio.TimeoutError:
                    retry += 1
                    __mcdr_server.logger.warn(f"Gateway重连超时！准备重试{retry}/2次！")
            else:
                __mcdr_server.logger.error(f"Gateway重连严重超时！准备重新获取gateway地址！")
                heart_start = True
                break
        else:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=36)
                if debug_status:
                    __mcdr_server.logger.info(f"已收到数据包！")
            except asyncio.TimeoutError:
                __mcdr_server.logger.error(f"机器人接收数据包系统严重超时！")
                heart_start = False
                server_restart = True
                break
            response_dict = json.loads(response)
            if debug_status:
                __mcdr_server.logger.info(f"获取到数据：{response_dict}")
            if response_dict['s'] == 1:
                if debug_status:
                    __mcdr_server.logger.info(f"已收到Hello数据包！")
                sn = 0
                session_id = response_dict['d']['session_id']
                heart_start = True
                server_start = True
                break
            elif response_dict['s'] == 3:
                if debug_status:
                    __mcdr_server.logger.info(f"已收到Pong包！")
                pong_back = True
            elif response_dict['s'] == 5:
                __mcdr_server.logger.error(f"收到强制重新获取地址数据包，机器人接收数据包系统已退出！")
                heart_stop = True
                break
            elif response_dict['s'] == 0:
                sn = response_dict['sn']


# 机器人维生系统
async def bot_heart(websocket):
    global server_restart, heart_start, pong_back, heart_stop
    retry = 0
    if debug_status:
        __mcdr_server.logger.info(f"机器人维生系统正在启动……")
    while True:
        if heart_start:
            if server_restart:
                heart_start = False
                break
            if heart_stop:
                heart_stop = False
                heart_start = False
                break
            if stop_status:
                break
            while retry < 3:
                await websocket.send('{"s": 2, "sn": ' + str(sn) + '}')
                if debug_status:
                    __mcdr_server.logger.info(f"已发送Ping包！")
                await asyncio.sleep(2)
                if pong_back:
                    pong_back = False
                    retry = 0
                    await asyncio.sleep(28)
                    break
                retry += 1
            if retry == 3:
                __mcdr_server.logger.error(f"机器人维生系统严重超时！")
                heart_start = False
                break


# 机器人发送Get系统
# 插件加载
def on_load(server: PluginServerInterface, _):
    global __mcdr_server, config, debug_status, stop_status
    # 变量初始化
    __mcdr_server = server  # 导入mcdr
    config = __mcdr_server.load_config_simple(target_class=Config)
    debug_status = config.debug
    stop_status = False

    # 主服务器启动
    if config.main_server:
        __mcdr_server.logger.info("机器人正在启动……")
        start_kook_bot()


# 插件卸载
def on_unload(_):
    global stop_status
    stop_status = True
    __mcdr_server.logger.info("机器人正在关闭……")
