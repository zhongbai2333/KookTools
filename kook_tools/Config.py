import random
import string
from typing import Dict

from mcdreforged.api.utils.serializer import Serializable


def create_string_number(n):
    m = random.randint(1, n)
    a = "".join([str(random.randint(0, 9)) for _ in range(m)])
    b = "".join([random.choice(string.ascii_letters) for _ in range(n - m)])
    return ''.join(random.sample(list(a + b), n))


class Commands(Serializable):
    help: list = [["help", "帮助"], "获取帮助"]
    admin_help: list = [["admin_help", "管理员帮助"], "获取管理员帮助"]
    get_admin: list = [["get_admin", "获取管理员"], "将当前用户添加至管理员（需后台验证）"]
    set_server: list = [["set_server", "设置服务器"], "获取机器人在的服务器并选择管理哪些"]
    set_server_list: list = [["list", "列表"], "列出机器人所在的服务器列表"]
    set_server_add: list = [["add", "添加"], "添加机器人所管理的服务器"]
    set_server_del: list = [["del", "删除"], "删除机器人所管理的服务器"]
    set_talk_group: list = [["set_talk_group", "设置聊天组"], "设置或取消设置为聊天频道"]
    set_command_group: list = [["set_command_group", "设置命令组"], "设置或取消设置为命令频道"]
    bound: list = [["bound", "绑定"], "与 Minecraft ID 绑定"]
    bound_list: list = [["list", "列表"], "显示绑定列表"]
    bound_unbound: list = [["unbound", "解绑"], "解除 Player/ID 的绑定"]
    bound_check: list = [["check", "检查"], "检索绑定成员"]
    bound_player: list = [["player", "玩家ID"], "玩家ID选择器"]
    bound_kook: list = [["kook"], "KookID选择器"]
    list_player: list = [["list", "玩家列表"], "查看在线玩家列表"]


class BotMsg(Serializable):
    group_help: str = "群聊帮助列表：{}"
    person_help: str = "私聊帮助列表：{}"
    admin_group_help: str = ""
    admin_person_help: str = "管理员 {} 你好，这是您的管理帮助列表：{}"
    help_set_server: str = "设置服务器帮助列表：{}"
    not_admin: str = " {} ，您不是管理员"
    get_admin_msg: str = "请到后台确认管理员权限！"
    nothing_msg: str = "未知的命令，使用 {} 来查询命令列表"
    cant_get_server_list: str = "无法获取服务器列表，或许是机器人未加入服务器？"
    found_server_list: str = "已找到下列服务器，可使用 {} {} <number> 来添加服务器"
    cant_found_server_list: str = "未找到服务器列表，请先使用 {} {} 来获取服务器列表"
    add_server: str = "已添加{}为管理服务器！"
    already_add_server: str = "{}已是管理服务器！"
    del_server: str = "已删除管理服务器{}！"
    already_del_server: str = "{}不是已添加的服务器！"
    add_server_help: str = "命令错误！请使用 {} {} <number>"
    del_server_help: str = "命令错误！请使用 {} {} <number>"
    at_msg: str = "如果需要添加为聊天组请用 {}，如果需要添加为命令组请用 {}"
    del_talk_group: str = "已删除此频道({})为聊天组！"
    add_talk_group: str = "已添加此频道({})为聊天组！"
    del_command_group: str = "已删除此频道({})为命令组！"
    add_command_group: str = "已添加此频道({})为命令组！"
    already_add_command_group: str = "命令组频道只能有一个！({})"
    need_bound: str = "{} 在绑定 ID 前无法互通消息，请使用 {} <ID> 绑定游戏ID"
    bound_error: str = "命令错误！请使用 {} <ID>"
    already_bound: str = "{} 您已在服务器绑定ID: {}, 请联系管理员修改"
    already_be_bound: str = "{} ID：{} 已被 {} 在服务器绑定, 请联系管理员修改"
    fin_bound: str = "{} 已为您绑定并添加至白名单！"
    fin_bound_without_whitelist: str = "{} 已在服务器成功绑定{}"
    error_player_name: str = "{} 不合法的用户名！"
    wrong_player_name: str = "{} 不存在的用户名！"
    start_server: str = "{} 已启动！用时{}秒！"
    restart_server: str = "{} 核心已重启！"
    stop_server: str = "{} 核心已关闭！"
    online_player_info: str = "{} 在线玩家共{}人\n玩家列表: {}"
    server_not_start: str = "{} 服务器核心未启动！"
    person_bound_list_error: str = "命令错误！请使用 {} {}"
    person_bound_unbound_check_error: str = "命令错误！请使用 {} {} {} <ID>"
    person_bound_list: str = "绑定列表：\n"
    person_bound_cant_list: str = "还没有人在 {} 绑定"
    person_bound_unbound_with_whitelist_fin: str = "已删除 {}({}) 的绑定并自动解除了白名单"
    person_bound_unbound_fin: str = "已删除 {}({}) 的绑定"
    person_bound_unbound_cant_player: str = "未找到该玩家，该玩家不存在或未绑定！({})"
    person_bound_check_found: str = "{}({})"
    person_bound_check_cant_found: str = "无法查询到此人！（{}）"
    person_bound_help: str = "bound 帮助列表：{}"
    person_bound_admin_help = "bound 管理员帮助列表：{}"


class GroupConfig(Serializable):
    uri: str = "https://www.kookapp.cn"
    api_version: int = 3
    token: str = ""
    password: str = str(create_string_number(10))
    server_host: str = "0.0.0.0"
    server_port: int = 8080
    command_prefix = "#"
    server_name: str = "Survival Server"
    whitelist_add_with_bound: bool = True
    why_no_whitelist: str = ""
    whitelist_path: str = "./server/whitelist.json"
    online_mode: bool = True
    mysql_enable: bool = False
    mysql_config: Dict[str, str] = {
        'host': "127.0.0.1",
        'port': "3306",
        'database': "MCDR_QQTools",
        'user': "root",
        'password': "123"
    }


class BabyConfig(Serializable):
    far_server_host: str = "127.0.0.1"
    far_server_port: int = 8080
    password: str = ""
    server_name: str = "Survival Server"
    whitelist_path: str = "./server/whitelist.json"


class FirstConfig(Serializable):
    first_start: bool = True
    main_server: bool = False
    debug: bool = False


class GroupBotData(Serializable):
    server_seed: str = ""
    admins: list[str] = []
    command_group: str = ""
    talk_groups: list[str] = []


class BabyBotData(Serializable):
    command_group: str = ""
    talk_groups: list[str] = []


def get_config():
    from .Global_Variable import get_variable, set_variable
    __mcdr_server = get_variable('__mcdr_server')
    is_first = __mcdr_server.load_config_simple('isFirst.json', target_class=FirstConfig)
    set_variable('debug', is_first.debug)
    set_variable('main_server', is_first.main_server)
    if is_first.first_start:
        set_variable('first_start', True)
    else:
        if is_first.main_server:
            config = __mcdr_server.load_config_simple(target_class=GroupConfig)
            botdata = __mcdr_server.load_config_simple('botData.json', target_class=GroupBotData)
            botmsg = __mcdr_server.load_config_simple('botMsg.json', target_class=BotMsg)
            commands = __mcdr_server.load_config_simple('commands.json', target_class=Commands)
            set_variable('botmsg', botmsg)
            set_variable('commands', commands)
        else:
            config = __mcdr_server.load_config_simple(target_class=BabyConfig)
            botdata = __mcdr_server.load_config_simple('botData.json', target_class=BabyBotData)
        set_variable('config', config)
        set_variable('botdata', botdata)


# 添加机器人管理员
def add_admin(command_s):
    from .Global_Variable import get_variable, set_variable
    __mcdr_server = get_variable('__mcdr_server')
    if str(command_s).split()[0] == 'Console':
        botdata = get_variable('botdata')
        if get_variable('debug'):
            __mcdr_server.logger.info(f"当前管理员列表：{botdata.admins}")
        if get_variable('wait_admin'):
            if get_variable('wait_admin') not in botdata.admins:
                botdata.admins.append(get_variable('wait_admin'))
                botdata_n = {
                    "server_seed": botdata.server_seed,
                    "admins": botdata.admins,
                    "command_group": botdata.command_group,
                    "talk_groups": botdata.talk_groups
                }
                __mcdr_server.save_config_simple(botdata_n, 'botData.json')
                botdata = __mcdr_server.load_config_simple('botData.json', target_class=GroupBotData)
                set_variable('botdata', botdata)
                __mcdr_server.logger.info("已为其获取Admin权限！")
                set_variable('wait_admin', None)
            else:
                __mcdr_server.logger.info("此玩家已获得 Kook Bot 管理员！")
                set_variable('wait_admin', None)
        else:
            __mcdr_server.logger.info("无玩家正在请求！")
    else:
        __mcdr_server.logger.error(f"有非控制台用户({str(command_s).split()[1]})试图获取管理员权限！")


# 修改Botdata
def save_botdata(option: str, input_sth: str, add: bool = False):
    from .Global_Variable import get_variable, set_variable
    __mcdr_server = get_variable('__mcdr_server')
    if get_variable('main_server'):
        botdata = get_variable("botdata")
        if option == "command_group":
            if add:
                botdata.command_group = input_sth
            else:
                botdata.command_group = ""
        elif option == "talk_groups":
            if add:
                botdata.talk_groups.append(input_sth)
            else:
                botdata.talk_groups.remove(input_sth)
        elif option == "server_seed":
            if add:
                botdata.server_seed = input_sth
            else:
                botdata.server_seed = ""
        botdata_n = {
            "server_seed": botdata.server_seed,
            "admins": botdata.admins,
            "command_group": botdata.command_group,
            "talk_groups": botdata.talk_groups
        }
        __mcdr_server.save_config_simple(botdata_n, 'botData.json')
        botdata = __mcdr_server.load_config_simple('botData.json', target_class=GroupBotData)
        set_variable('botdata', botdata)
    else:
        botdata = get_variable("botdata")
        if option == "command_group":
            if add:
                botdata.command_group = input_sth
            else:
                botdata.command_group = ""
        elif option == "talk_groups":
            if add:
                botdata.talk_groups.append(input_sth)
            else:
                botdata.talk_groups.remove(input_sth)
        botdata_n = {
            "command_group": botdata.command_group,
            "talk_groups": botdata.talk_groups
        }
        __mcdr_server.save_config_simple(botdata_n, 'botData.json')
        botdata = __mcdr_server.load_config_simple('botData.json', target_class=BabyBotData)
        set_variable('botdata', botdata)
