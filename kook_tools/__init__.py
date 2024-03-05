import time

from mcdreforged.api.all import *


# =============
# MCDR Listener
# =============
def on_load(server: PluginServerInterface, _):
    from .Global_Variable import set_variable, get_variable
    from .Config import get_config

    # 模块导入初始化
    from .Global_Variable import init as global_variable_init
    global_variable_init()

    # 配置文件初始化
    set_variable('__mcdr_server', server)
    get_config()

    if get_variable('first_start'):
        # 命令初始化
        builder = SimpleCommandBuilder()

        from .First_Start import (set_main_server, set_token, set_server_host, set_server_port, set_server_name,
                                  set_password)

        # declare your commands
        builder.command('!!kt config main_server <bool>', set_main_server)
        builder.command('!!kt config token <token>', set_token)
        builder.command('!!kt config server_host <server_host>', set_server_host)
        builder.command('!!kt config server_port <server_port>', set_server_port)
        builder.command('!!kt config server_name <server_name>', set_server_name)
        builder.command('!!kt config password <password>', set_password)

        # define your command nodes
        builder.arg('bool', Boolean)
        builder.arg('token', Text)
        builder.arg('server_host', Text)
        builder.arg('server_port', Text)
        builder.arg('password', Text)
        builder.arg('server_name', GreedyText)

        # done, now register the commands to the server
        builder.register(server)
    else:
        if get_variable('main_server'):
            from .Group_Server import init as group_server_init
            from .Kook_Server import init as kook_server_init
            from .Msg_Parse import init as parse_msg_init

            builder = SimpleCommandBuilder()

            from .Config import add_admin
            builder.command('!!kt admin allow', add_admin)

            builder.register(server)

            parse_msg_init()
            group_server_init()
            kook_server_init()
        else:
            from .Baby_Server import init as baby_server_init
            baby_server_init()


# 插件卸载
def on_unload(_):
    from .Global_Variable import get_variable
    from .Msg_Parse import get_post_msg
    if get_variable('main_server'):
        kook_server = get_variable('kook_server')
        group_server = get_variable('group_server')
        get_post_msg("", "/user/offline", 1)
        kook_server.stop_server()
        group_server.close_server()
        while kook_server.finish_quit != 2 and not group_server.finish_close:
            time.sleep(1)
    else:
        baby_server = get_variable('baby_server')
        baby_server.stop_server()
        while not baby_server.finish_quit:
            time.sleep(1)


def on_server_startup(_):
    from .Global_Variable import get_variable
    from .First_Start import init as first_start_init
    __mcdr_server = get_variable('__mcdr_server')
    if get_variable('first_start'):
        first_start_init()
