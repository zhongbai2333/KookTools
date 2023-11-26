from typing import List, Dict

from mcdreforged.api.utils.serializer import Serializable

global help_info, admin_help_info, help_private_info, admin_help_private_info, bound_help


class AdminCommands(Serializable):
    to_mcdr: str = "tomcdr"
    to_minecraft: str = "togame"
    whitelist: str = "whitelist"


class Admins(Serializable):
    admins: list[str] = []


class Talk_group(Serializable):
    talk_group: list[str] = []


class ServerList(Serializable):
    server_list: list[str] = []


class Config(Serializable):
    uri: str = "https://www.kookapp.cn"
    api_version: int = 3
    token: str = ""
    command_group: str = ""
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
    auto_forwards: Dict[str, bool] = {
        'mc_to_qq': False,
        'qq_to_mc': False
    }
    mysql_enable: bool = False
    mysql_config: Dict[str, str] = {
        'host': "127.0.0.1",
        'port': "3306",
        'database': "MCDR_QQTools",
        'user': "root",
        'password': "123"
    }
    whitelist_command: List[str] = ["tomcdr", "togame"]
