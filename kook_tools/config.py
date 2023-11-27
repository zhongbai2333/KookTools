from typing import List, Dict

from mcdreforged.api.utils.serializer import Serializable

global help_info, admin_help_info, help_private_info, admin_help_private_info, bound_help


class AdminCommands(Serializable):
    to_mcdr: str = "tomcdr"
    to_minecraft: str = "togame"
    whitelist: str = "whitelist"


class BotMsg(Serializable):
    group_help: str = "群聊帮助列表：\n    help / 帮助 -- 获取帮助信息\n    admin_help / 管理员帮助 -- 获取管理员帮助列表"
    person_help: str = ("私聊帮助列表：\n   help / 帮助 -- 获取帮助信息\n    get_admin / 获取管理员 -- 将当前用户添加至管理员（需后台验证）\n    admin_help "
                        "/ 管理员帮助 -- 获取管理员帮助列表")
    admin_group_help: str = ""
    admin_person_help: str = ("管理员 {} 你好，这是您的管理帮助列表：\n    set_server / 设置服务器 -- 获取机器人在的服务器并选择管理哪些\n    "
                              "set_command_group / 设置频道组 -- 设置机器人需要处理命令的频道\n    set_talk_group / 设置聊天组 -- "
                              "设置机器人需要转发消息的频道")
    not_admin: str = " {} ，您不是管理员"
    get_admin_msg: str = "请到后台确认管理员权限！"
    nothing_msg: str = "未知的命令，使用 ”帮助“ 来查询命令列表"
    cant_get_server_list: str = "无法获取服务器列表，或许是机器人未加入服务器？"
    found_server_list: str = "已找到下列服务器，可使用 设置服务器 添加 <number> 来添加服务器"
    cant_found_server_list: str = "未找到服务器列表，请先使用 设置服务器 列表 来获取服务器列表"
    add_server: str = "已添加{}为管理服务器！"
    already_add_server: str = "{}已是管理服务器！"
    del_server: str = "已删除管理服务器{}！"
    already_del_server: str = "{}不是已添加的服务器！"


class bot_data(Serializable):
    server_list: list[str] = []
    admins: list[str] = []
    talk_group: list[str] = []
    command_group: str = ""


class Config(Serializable):
    uri: str = "https://www.kookapp.cn"
    api_version: int = 3
    token: str = ""
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
