import nonebot
from nonebot import drivers
import subprocess
drivers.BaseWebSocket = drivers.WebSocket
from os import path
from fastapi.middleware.cors import CORSMiddleware
from nonebot.adapters.cqhttp import Bot as CQHTTPBot

nonebot.init(command_start = {',', '，'})
driver = nonebot.get_driver()
app = nonebot.get_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

driver.register_adapter("cqhttp", CQHTTPBot)
nonebot.load_builtin_plugins()
nonebot.load_plugin("nonebot_plugin_test")
nonebot.load_plugin("plugins.xdice")
import nonebot_plugin_test
nonebot_plugin_test.sio.eio.cors_allowed_origins = "*"

if __name__ == '__main__':
    nonebot.run(host='0.0.0.0', port=8081)

    
