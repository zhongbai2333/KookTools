import string
import random
from typing import Dict

from mcdreforged.api.utils.serializer import Serializable

global help_info, admin_help_info, help_private_info, admin_help_private_info, bound_help


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
    at_msg: str = "如果需要添加为聊天组请用 {}，如果需要添加为命令组请用 {}({})"
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


class bot_data(Serializable):
    server_list: list[str] = []
    admins: list[str] = []
    talk_group: list[str] = []
    command_group: str = ""


class Config(Serializable):
    uri: str = "https://www.kookapp.cn"
    api_version: int = 3
    token: str = ""
    password: str = str(create_string_number(10))
    main_server_host: str = "0.0.0.0"
    main_server_port: int = 8080
    main_websocket_server_host: str = "0.0.0.0"
    main_websocket_server_port: int = 9090
    command_prefix = "#"
    server_name: str = "Survival Server"
    main_server: bool = True
    whitelist_add_with_bound: bool = True
    why_no_whitelist: str = ""
    whitelist_path: str = "./server/whitelist.json"
    whitelist_remove_with_leave: bool = True
    forwards_mcdr_command: bool = True
    forwards_server_start_and_stop: bool = True
    debug: bool = False
    online_mode: bool = True
    mysql_enable: bool = False
    mysql_config: Dict[str, str] = {
        'host': "127.0.0.1",
        'port': "3306",
        'database': "MCDR_QQTools",
        'user': "root",
        'password': "123"
    }
