[![Gitpod ready-to-code](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/nightingu/damebot)
[![Updates](https://pyup.io/repos/github/nightingu/damebot/shield.svg)](https://pyup.io/repos/github/nightingu/damebot/)
[![Python 3](https://pyup.io/repos/github/nightingu/damebot/python-3-shield.svg)](https://pyup.io/repos/github/nightingu/damebot/)

# damebot

bot (framework) for nightingu.

Aimed at easy deploy and development.

## DISCLIMER

仅供学习和交流使用。

## 安装和部署

基于 (https://nonebot.netlify.app/)[nonebot] (one bot). 

1. 首先安装(https://github.com/Mrs4s/go-cqhttp)[go-cqhttp]，按其教程安装，输入QQ号等并确保其能正常启动（即，向该QQ发送消息可以在cqhttp控制台上收到消息）。
2. 然后安装docker和docker-compose
3. 在项目根目录下执行`docker-compose up --build`。
4. 你应该能看到一些提示，得到一个地址栏，在装有go-cqhttp的机器上，输入浏览器后能显示一些东西出来（通常是method not allowed的错误提示页面）。
4. 记录你在浏览器地址中的`http://<主机名>:<端口>/`，这两个部分
3. 此时修改go-cqhttp产生的config.hjson，修改reverse_url项，改为`ws://<主机名>:<端口>/ws/`
4. 重新启动go-cqhttp，然后向你的QQ发送`.echo hello world`。如果你的QQ回复你了，那么部署就完成了。

项目提供github actions来在项目Release的时候连接特定的远程主机，在当前用户目录下建立app-damebot目录，并使用Release的代码执行步骤3，以后便不再需要手动部署。

