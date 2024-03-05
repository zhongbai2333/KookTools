global __mcdr_server, token, server_host, server_port, server_name, main_server, password


def init():
    from .Global_Variable import get_variable
    global __mcdr_server
    __mcdr_server = get_variable('__mcdr_server')

    # 开始引导
    __mcdr_server.logger.info('看起来您是第一次运行本插件，接下来将运行 Kook Tools 配置流程：')
    __mcdr_server.logger.info('此服务器是否为主服务器？（!!kt config main_server <True/False>）')


def set_main_server(_, context):
    from .Config import get_config
    global main_server
    if context['bool']:
        main_server = True
        is_first = {
            "first_start": False,
            "main_server": True
        }
        __mcdr_server.save_config_simple(is_first, 'isFirst.json')
        __mcdr_server.logger.info('已记录为主服务器，正在生成默认配置文件')
        get_config()
        __mcdr_server.logger.info('请输入 Kook 机器人的 token （!!kt config token <token>）')
    else:
        main_server = False
        is_first = {
            "first_start": False,
            "main_server": False
        }
        __mcdr_server.save_config_simple(is_first, 'isFirst.json')
        __mcdr_server.logger.info('已记录为子服务器，正在生成默认配置文件')
        get_config()
        __mcdr_server.logger.info('请输入 Group 群组服主服务器 IP '
                                  '（!!kt config server_host <server_host>(输入 * 默认为 “127.0.0.1”)）')


def set_token(_, context):
    global token
    token = context['token']
    __mcdr_server.logger.info('已记录 token')
    __mcdr_server.logger.info('请输入 Group 群组服主服务器 IP '
                              '（!!kt config server_host <server_host>(输入 * 默认为 “0.0.0.0”)）')


def set_server_host(_, context):
    global server_host
    server_host = context['server_host']
    if server_host == "*":
        if main_server:
            server_host = "0.0.0.0"
        else:
            server_host = "127.0.0.1"
    __mcdr_server.logger.info('已记录 server_host')
    __mcdr_server.logger.info('请输入 Group 群组服主服务器 PORT '
                              '（!!kt config server_port <server_port>(输入 * 默认为 8080)）')


def set_server_port(_, context):
    global server_port
    server_port = context['server_port']
    if server_port == "*":
        server_port = 8080
    else:
        server_port = int(server_port)
    __mcdr_server.logger.info('已记录 server_port')
    __mcdr_server.logger.info('请输入服务器名称 '
                              '（!!kt config server_name <server_name>(输入 * 默认为 "Survival Server")）')


def set_server_name(_, context):
    global server_name
    server_name = context['server_name']
    if server_name == "*":
        server_name = "Survival Server"
    __mcdr_server.logger.info('已记录 server_name')
    if main_server:
        finish_start()
    else:
        __mcdr_server.logger.info('请输入主服务器密码 （!!kt config password <password>）')


def set_password(_, context):
    global password
    password = context['password']
    __mcdr_server.logger.info('已记录 Password')
    finish_start()


def finish_start():
    from .Global_Variable import get_variable
    config = get_variable('config')
    if main_server:
        new_config = {
            "uri": config.uri,
            "api_version": config.api_version,
            "token": token,
            "password": config.password,
            "server_host": server_host,
            "server_port": server_port,
            "command_prefix": config.command_prefix,
            "server_name": server_name,
            "whitelist_add_with_bound": config.whitelist_add_with_bound,
            "why_no_whitelist": config.why_no_whitelist,
            "whitelist_path": config.whitelist_path,
            "online_mode": config.online_mode,
            "mysql_enable": config.mysql_enable,
            "mysql_config": config.mysql_config
        }
    else:
        new_config = {
            "far_server_host": server_host,
            "far_server_port": server_port,
            "password": password,
            "server_name": server_name,
            "whitelist_path": config.whitelist_path
        }
    __mcdr_server.save_config_simple(new_config, 'config.json')
    __mcdr_server.logger.info('已完成服务器基础设置！请使用 !!MCDR plg reload kook_tools 重新加载本插件！')
