import nonebot
from nonebot import drivers
drivers.BaseWebSocket = drivers.WebSocket
from os import path
from fastapi.middleware.cors import CORSMiddleware
from nonebot.adapters.cqhttp import Bot as CQHTTPBot

nonebot.init(command_start = {',', '，'})
driver = nonebot.get_driver()
app = nonebot.get_app()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

driver.register_adapter("cqhttp", CQHTTPBot)
nonebot.load_builtin_plugins()
nonebot.load_plugin("nonebot_plugin_test")

if __name__ == '__main__':
    nonebot.run(host='127.0.0.1', port=8081)

    