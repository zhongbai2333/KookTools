import asyncio
import re
import time

import requests
from mcdreforged.api.all import *

from .Config import get_config
from .MySQL_Control import *

global kook_server, debug_status, wait_list, online_players, botdata


# ======================
# Kook Websockets Server
# ======================
@new_thread("Kook_Server")
def Kook_Server():
    from .Kook_Server import KookServer
    global kook_server
    kook_server = KookServer()
    kook_server.start_server()


# ====================
# Tools event listener
# ====================
# 整合获取用户
def get_user_list():
    from .Global_Variable import get_variable
    if get_variable("config").mysql_enable:
        return dict(connect_and_query_db("kook_id,player_id", "user_list",
                                         get_variable("config").mysql_config))
    else:
        return get_variable("data")


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


# 把命令执行独立出来，以防服务器处在待机状态
def send_execute_mc(command: str):
    from .Global_Variable import get_variable
    global wait_list
    if get_variable("__mcdr_server").is_server_running():  # 确认服务器是否启动
        get_variable("__mcdr_server").execute(command)
        get_variable("__mcdr_server").logger.info(f"KookTools execute:{command}")
    else:
        wait_list.append(command)  # 堆着等开服
        get_variable("__mcdr_server").logger.info(f"KookTools can't execute:{command}, "
                                                  f"The list of commands:{str(wait_list)}")


# -------------------------
# Config editor event listener
# -------------------------
# 修改Botdata
def save_botdata(option: str, input_sth: str, add: bool = False):
    from .Global_Variable import get_variable
    from .Config import get_config
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
    get_variable("__mcdr_server").save_config_simple(botdata_n, 'botdata.json')
    get_config()


# 整合绑定用户
def send_user_list(send_id: str, name: str):
    from .Global_Variable import get_variable, set_variable
    data = get_variable("data")
    pattern = r'[^a-zA-Z0-9_]'
    if not re.search(pattern, name):
        if get_variable("config").mysql_enable:
            if get_variable("config").main_server:
                db_data = (send_id, name)
                connect_and_insert_db("kook_id,player_id", "user_list", db_data,
                                      get_variable("config").mysql_config)
                return True
            return True
        else:
            data[send_id] = name  # 进行绑定
            set_variable("data", data)
            save_data(get_variable("__mcdr_server"))
            return True
    else:
        return False


# 整合删除用户
def delete_user(send_id: str):
    from .Global_Variable import get_variable, set_variable
    data = get_variable("data")
    if get_variable("config").mysql_enable:
        if get_variable("config").main_server:
            connect_and_delete_data("user_list", f"kook_id = {send_id}",
                                    get_variable("config").mysql_config)
    else:
        del data[send_id]
        set_variable("data", data)
        save_data(get_variable("__mcdr_server"))


# 保存data
def save_data(server: PluginServerInterface):
    from .Global_Variable import set_variable, get_variable
    data = get_variable("data")
    server.save_config_simple({'data': data}, 'data.json')
    data = server.load_config_simple(
        'data.json',
        default_config={'data': {}},
        echo_in_console=False
    )['data']
    set_variable("data", data)


# =============
# MCDR Listener
# =============
# 插件入口
def on_load(server: PluginServerInterface, _):
    from .Msg_Parse import init as msg_parse_init
    global debug_status, online_players
    __mcdr_server = server
    from .Global_Variable import init, set_variable, get_variable
    init()
    set_variable("__mcdr_server", __mcdr_server)
    set_variable("online_players", [])
    online_players = []
    get_config()
    msg_parse_init()
    debug_status = get_variable("config").debug
    if not get_variable("config").mysql_enable:
        data = server.load_config_simple(
            'data.json',
            default_config={'data': {}},
            echo_in_console=False
        )['data']
        set_variable("data", data)
    if get_variable("config").main_server:
        from .Group_Server import init as start_group_server
        start_group_server()
        Kook_Server()
    else:
        from .Baby_Server import init as start_baby_server
        start_baby_server()


def on_unload(_):
    from .Global_Variable import get_variable
    if get_variable("config").main_server:
        kook_server.stop_server()
        while kook_server.finish_quit != 2:
            time.sleep(1)
    else:
        asyncio.run(get_variable("baby_server").disconnect())
        while get_variable("baby_server").finish_quit != 2:
            time.sleep(1)


# 在线玩家检测
def on_player_joined(_, player, __):
    from .Global_Variable import get_variable, set_variable
    global online_players
    online_players = get_variable("online_players")
    from .Msg_Parse import send_group_person_msg
    if player not in online_players:
        online_players.append(player)
        set_variable("online_players", online_players)
    for i in get_variable("botdata").talk_group:
        send_group_person_msg(f'{player} 加入游戏', i, 1)


def on_player_left(_, player):
    from .Global_Variable import get_variable, set_variable
    global online_players
    online_players = get_variable("online_players")
    from .Msg_Parse import send_group_person_msg
    if player in online_players:
        online_players.remove(player)
        set_variable("online_players", online_players)
    for i in get_variable("botdata").talk_group:
        send_group_person_msg(f'{player} 退出游戏', i, 1)
