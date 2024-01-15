import copy

from mcdreforged.api.all import *
import json

import requests

global __mcdr_server, config, debug_status, botdata, botmsg, commands, botid, online_players
global group_help, person_help, admin_person_help, set_server_help, t_and_c_group_help, bound_help, admin_bound_help
global wait_admin, server_list_number, server_list_id


def init():
    from .Global_Variable import get_variable
    global __mcdr_server, config, debug_status, botdata, botmsg, commands, online_players
    __mcdr_server = get_variable("__mcdr_server")
    config = get_variable("config")
    botdata = get_variable("botdata")
    botmsg = get_variable("botmsg")
    commands = get_variable("commands")
    debug_status = get_variable("config").debug
    online_players = get_variable("online_players")
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


# 处理Get请求
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


# 消息转发处理
def turn_msg(userid: str, target_id: str, msg: str, command_talk: bool):
    from .__init__ import get_user_list
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
            from .__init__ import save_botdata
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
    from .__init__ import get_user_list, real_name, send_user_list, send_execute_mc
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
    from .__init__ import save_botdata, get_user_list, send_execute_mc, delete_user
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
                res = get_post_msg("/guild/list")
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
                            res_name = get_post_msg(f"/guild/view?guild_id={i}")
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
                reply_msg = copy.copy(botmsg.person_bound_cant_list.format(config.server_name)) if reply_msg == '' else \
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
