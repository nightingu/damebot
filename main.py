import nonebot

from os import path

from nonebot.adapters.cqhttp import Bot as CQHTTPBot

nonebot.init(command_start = {',', '，'})
driver = nonebot.get_driver()
driver.register_adapter("cqhttp", CQHTTPBot)
nonebot.load_builtin_plugins()

if __name__ == '__main__':
    nonebot.run(host='127.0.0.1', port=8081)

    