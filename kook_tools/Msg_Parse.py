import asyncio

from mcdreforged.api.all import *

import json

import requests

global __mcdr_server, config, debug_status, botdata, botid, commands, main_server, botmsg
global group_help, person_help, admin_person_help, set_server_help, t_and_c_group_help, bound_help, admin_bound_help
global server_list_id, server_list_number


def init():
    from .Global_Variable import get_variable
    global __mcdr_server, config, debug_status, botdata, commands, main_server, botmsg
    global server_list_id, server_list_number
    __mcdr_server = get_variable('__mcdr_server')
    config = get_variable('config')
    debug_status = get_variable('debug')
    botdata = get_variable('botdata')
    botmsg = get_variable('botmsg')
    commands = get_variable('commands')

    server_list_id = []
    server_list_number = 0

    main_server = get_variable('main_server')

    make_help_msg()


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


def parse_msg(bot_id, msg):
    global botid
    botid = bot_id
    parse_get_msg(msg)


# -------------------------
# Parse msg event listener
# -------------------------
# 机器人event处理系统
@new_thread('parse_get_msg')
def parse_get_msg(msg) -> dict or str:
    if msg['d']['channel_type'] == "GROUP":
        if msg['d']['type'] == 255:
            __mcdr_server.logger.info(f"收到系统信息！")
        else:
            if debug_status:
                __mcdr_server.logger.info(f"收到群聊消息！发送者：{msg['d']['extra']['author']['username']}"
                                          f"({msg['d']['author_id']}),"
                                          f"于文字聊天室“{msg['d']['extra']['channel_name']}({msg['d']['target_id']})”发送，"
                                          f"内容为：{msg['d']['content']}")
            if msg['d']['extra']['guild_id'] in botdata.server_seed and msg['d']['author_id'] != botid:
                parse_group_command(msg['d']['content'], msg['d']['extra']['author']['username'], msg['d']['author_id'],
                                    msg['d']['target_id'])
    elif msg['d']['channel_type'] == "PERSON":
        if msg['d']['type'] == 255:
            __mcdr_server.logger.info(f"收到系统信息！")
        else:
            if debug_status:
                __mcdr_server.logger.info(f"收到私聊消息！发送者：{msg['d']['extra']['author']['username']}"
                                          f"({msg['d']['author_id']}),"
                                          f"于私聊({msg['d']['target_id']})发送，"
                                          f"内容为：{msg['d']['content']}")
            if not msg['d']['extra']['author']['bot']:
                parse_person_command(msg['d']['content'], msg['d']['extra']['author']['username'],
                                     msg['d']['author_id'])


# 处理 Get Post 请求
def get_post_msg(msg, uri_p: str = "", mode: int = 0) -> dict or str:
    if mode == 0:
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
    else:
        if debug_status:
            __mcdr_server.logger.info(f"发送Post请求：{msg}")
        header = {"Authorization": f"Bot {config.token}"}  # 写入token
        gateway_uri = f"/api/v{str(config.api_version)}"  # 写入api版本
        post = requests.post(url=config.uri + gateway_uri + uri_p, json=msg, headers=header)
        if post.text:  # 检查是否回复
            json_dict = json.loads(post.text)  # 转json字典解析
            if debug_status:
                __mcdr_server.logger.info(f"获取到的Post反馈：{json_dict}")
            return json_dict  # 返回数据
        else:
            return ""


# 处理群聊消息
def parse_group_command(msg, user_name, user_id, target_id):
    global botdata
    from .Global_Variable import get_variable
    msg_c = msg.split()  # 分割
    if msg_c[0] == "(met)" + botid + "(met)" and len(msg_c) <= 1:
        if user_id in botdata.admins:
            send_group_person_msg(botmsg.at_msg.format(" / ".join(commands.set_talk_group[0]) + " <ID>",
                                                       " / ".join(commands.set_command_group[0]) + " <ID>")
                                  , target_id, 1)
            group_list = "<ID>. <Server Name> -- <Info> ----------"
            server_infos = get_variable('group_server').server_infos
            for i in server_infos.keys():
                if target_id in server_infos[i][1] and target_id in server_infos[i][2]:
                    group_list += f"\n{i}. {server_infos[i][0]} -- 已添加为聊天组和命令组"
                elif target_id in server_infos[i][1]:
                    group_list += f"\n{i}. {server_infos[i][0]} -- 已添加为命令组"
                elif target_id in server_infos[i][2]:
                    group_list += f"\n{i}. {server_infos[i][0]} -- 已添加为聊天组"
                else:
                    group_list += f"\n{i}. {server_infos[i][0]} -- 未添加为任何组"
            send_group_person_msg(group_list, target_id, 1)
        else:
            send_group_person_msg(botmsg.not_admin.format(user_name), user_id, 0)
    elif msg_c[0] == "(met)" + botid + "(met)" and len(msg_c) == 3:
        if user_id in botdata.admins:
            server_infos = get_variable('group_server').server_infos
            msg_c[2] = msg_c[2].replace('\\', '')
            if msg_c[2] in server_infos.keys():
                from .Config import save_botdata
                # set_talk_group 命令
                if msg_c[1] in commands.set_talk_group[0]:
                    if msg_c[2] == '-----':
                        botdata = get_variable('botdata')
                        if target_id in botdata.talk_groups:
                            save_botdata("talk_groups", target_id, False)
                            send_group_person_msg(botmsg.del_talk_group.format(target_id), target_id, 1)
                            get_variable('group_server').add_talk_group(msg_c[2], target_id, False)
                        else:
                            save_botdata("talk_groups", target_id, True)
                            send_group_person_msg(botmsg.add_talk_group.format(target_id), target_id, 1)
                            get_variable('group_server').add_talk_group(msg_c[2], target_id, True)
                    else:
                        if target_id in server_infos[msg_c[2]][2]:
                            asyncio.run(get_variable('group_server').send_message(0, msg_c[2], 4, f"{target_id} DEL"))
                            send_group_person_msg(botmsg.del_talk_group.format(target_id), target_id, 1)
                            get_variable('group_server').add_talk_group(msg_c[2], target_id, False)
                        else:
                            asyncio.run(get_variable('group_server').send_message(0, msg_c[2], 4, f"{target_id} ADD"))
                            send_group_person_msg(botmsg.add_talk_group.format(target_id), target_id, 1)
                            get_variable('group_server').add_talk_group(msg_c[2], target_id, True)
                # set_command_group 命令
                elif msg_c[1] in commands.set_command_group[0]:
                    if msg_c[2] == '-----':
                        botdata = get_variable('botdata')
                        if target_id == botdata.command_group:
                            save_botdata("command_group", target_id, False)
                            send_group_person_msg(botmsg.del_command_group.format(target_id), target_id, 1)
                            get_variable('group_server').add_command_group(msg_c[2], target_id, False)
                        else:
                            if botdata.command_group:
                                send_group_person_msg(botmsg.already_add_command_group.format(botdata.command_group),
                                                      target_id, 1)
                            else:
                                save_botdata("command_group", target_id, True)
                                send_group_person_msg(botmsg.add_command_group.format(target_id), target_id, 1)
                                get_variable('group_server').add_command_group(msg_c[2], target_id, True)
                    else:
                        if target_id == server_infos[msg_c[2]][1]:
                            asyncio.run(get_variable('group_server').send_message(0, msg_c[2], 3, f"{target_id} DEL"))
                            send_group_person_msg(botmsg.del_command_group.format(target_id), target_id, 1)
                            get_variable('group_server').add_command_group(msg_c[2], target_id, False)
                        else:
                            if server_infos[msg_c[2]][1]:
                                send_group_person_msg(botmsg.already_add_command_group.format(server_infos[msg_c[2]][1]),
                                                      target_id, 1)
                            else:
                                asyncio.run(get_variable('group_server').send_message(0, msg_c[2], 3, f"{target_id} ADD"))
                                send_group_person_msg(botmsg.add_command_group.format(target_id), target_id, 1)
                                get_variable('group_server').add_command_group(msg_c[2], target_id, True)
        else:
            send_group_person_msg(botmsg.not_admin.format(user_name), target_id, 1)
    else:
        if target_id in get_variable('group_server').command_group_list.keys():
            if msg[0] == config.command_prefix:  # 判断命令前缀
                msg_c = msg[1:].split()  # 去除命令前缀

                # help 命令
                if msg_c[0] in commands.help[0]:
                    send_group_person_msg(botmsg.group_help.format(t_and_c_group_help), target_id, 1)

                # bound 命令
                elif msg_c[0] in commands.bound[0] and len(msg_c) == 2:
                    bound_player(user_id, msg_c, target_id)
                elif msg_c[0] in commands.bound[0] and len(msg_c) != 2:
                    send_group_person_msg(botmsg.bound_error.format(config.command_prefix +
                                                                    f" / {config.command_prefix}"
                                                                    .join(commands.bound[0])),
                                          target_id, 1)

                # list 命令
                elif msg_c[0] in commands.list_player[0]:
                    if __mcdr_server.is_server_running():
                        send_group_person_msg(botmsg.online_player_info.format(config.server_name,
                                                                               len(online_players),
                                                                               ', '.join(online_players)),
                                              target_id, 1)
                    else:
                        send_group_person_msg(botmsg.server_not_start.format(config.server_name), target_id, 1)
            else:
                if target_id in get_variable('group_server').talk_groups_list.keys():
                    turn_msg(user_id, target_id, msg, True)
        elif target_id in get_variable('group_server').talk_groups_list.keys():
            turn_msg(user_id, target_id, msg, False)


# bound系统
def bound_player(userid: str, msg_c: list, target_id: str):
    from .Global_Variable import get_variable
    group_back = get_variable('group_back')
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
                    if group_back:
                        send_group_person_msg(botmsg.fin_bound.format("(met)" + userid + "(met)"), target_id, 1)
                else:
                    send_execute_mc(f'whitelist reload')
                    if group_back:
                        send_group_person_msg(botmsg.fin_bound_without_whitelist.format("(met)" + userid + "(met)",
                                                                                        config.why_no_whitelist),
                                              target_id, 1)
                    else:
                        if config.why_no_whitelist:
                            send_group_person_msg(config.why_no_whitelist, target_id, 1)
            else:
                if group_back:
                    send_group_person_msg(botmsg.error_player_name.format("(met)" + userid + "(met)"), target_id, 1)
        else:
            if group_back:
                send_group_person_msg(botmsg.worng_player_name.format("(met)" + userid + "(met)"), target_id, 1)


# 处理私聊命令
def parse_person_command(msg, username, userid):
    from .Global_Variable import set_variable
    msg = msg.split()  # 分割
    # help 命令
    if msg[0] in commands.help[0]:
        send_group_person_msg(botmsg.person_help.format(person_help), userid, 0)

    # admin_help 命令
    elif msg[0] in commands.admin_help[0]:
        if userid in botdata.admins:
            send_group_person_msg(botmsg.admin_person_help.format(username, admin_person_help), userid, 0)
        else:
            send_group_person_msg(botmsg.not_admin.format(username), userid, 0)

    # get_admin 命令
    elif msg[0] in commands.get_admin[0]:
        __mcdr_server.logger.info(
            f"{username}({userid})正在获取管理员权限，使用命令 !!kt admin allow 确认其管理员身份！")
        wait_admin = userid
        set_variable('wait_admin', wait_admin)
        send_group_person_msg(botmsg.get_admin_msg, userid, 0)

    # set_server 命令
    elif msg[0] in commands.set_server[0] and len(msg) > 1:
        global server_list_id, server_list_number
        if userid in botdata.admins:  # 判断 admin
            from .Config import save_botdata
            # 只有 set_server
            if msg[1] in commands.set_server_list[0]:
                # 初始化
                server_list_id = []
                server_list_number = 0
                # 获取列表
                res = get_post_msg("/guild/list")
                # 如果有回复且回复格式正确
                if res:
                    if res['code'] == 0:
                        # 反馈命令
                        send_group_person_msg(botmsg.found_server_list.format(" / ".join(commands.set_server[0]),
                                                                              " / ".join(commands.set_server_add[0])),
                                              userid, 0)
                        for i in res['data']['items']:
                            server_list_number += 1
                            server_list_id.append(i['id'])
                            if i['id'] == botdata.server_seed:
                                send_group_person_msg(f"{server_list_number}. {i['name']}({i['id']})(已添加)", userid,
                                                      0)
                            else:
                                send_group_person_msg(f"{server_list_number}. {i['name']}({i['id']})", userid, 0)
                    else:
                        send_group_person_msg(botmsg.cant_get_server_list, userid, 0)
                else:
                    send_group_person_msg(botmsg.cant_get_server_list, userid, 0)
            elif len(msg) == 3 and msg[1] in commands.set_server_add[0]:
                if server_list_number != 0:
                    if int(msg[2]) <= server_list_number:
                        if not server_list_id[int(msg[2]) - 1] in botdata.server_seed:
                            save_botdata("server_seed", server_list_id[int(msg[2]) - 1], True)
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
                    if server_list_id[int(msg[2]) - 1] in botdata.server_seed:
                        save_botdata("server_seed", server_list_id[int(msg[2]) - 1], False)
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
            if config.main_server:
                send_group_person_msg(botmsg.not_admin.format(username), userid, 0)
    elif msg[0] in commands.set_server[0] and len(msg) == 1:
        send_group_person_msg(botmsg.help_set_server.format(set_server_help), userid, 0)


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
