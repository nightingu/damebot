[![Gitpod ready-to-code](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/nightingu/damebot)
![Deliver on Nightingu](https://github.com/nightingu/damebot/workflows/Deliver%20on%20host/badge.svg)
[![Updates](https://pyup.io/repos/github/nightingu/damebot/shield.svg)](https://pyup.io/repos/github/nightingu/damebot/)
[![Python 3](https://pyup.io/repos/github/nightingu/damebot/python-3-shield.svg)](https://pyup.io/repos/github/nightingu/damebot/)

# damebot

bot (framework) for nightingu.

Aimed at easy deploy and development.

## DISCLIMER

仅供学习和交流使用。

## 安装和部署

基于 [nonebot](https://nonebot.netlify.app/)(one bot). 

1. 首先安装[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)，按其教程安装，输入QQ号等并确保其能正常启动（即，向该QQ发送消息可以在cqhttp控制台上收到消息）。
2. 然后安装docker和docker-compose
3. 在项目根目录下执行`docker-compose up --build`。
4. 你应该能看到一些提示，得到一个地址栏，在装有go-cqhttp的机器上，输入浏览器后能显示一些东西出来（通常是method not allowed的错误提示页面）。
4. 记录你在浏览器地址中的`http://<主机名>:<端口>/`，这两个部分
3. 此时修改go-cqhttp产生的config.hjson，修改reverse_url项，改为`ws://<主机名>:<端口>/cqhttp/ws`
4. 重新启动go-cqhttp，然后向你的QQ发送`.echo hello world`。如果你的QQ回复你了，那么部署就完成了。

## 自动部署配置

项目提供github actions来在项目Release的时候连接特定的远程主机，在当前用户目录下建立app-damebot目录，并使用Release的代码执行步骤3，以后便不再需要手动部署。

### 部署机器注意事项
- 需要安装docker、docker-compose、rsync。
- 需要能够从github访问。
- 请保证能够使用secret中的USER和PASSWORD，使用ssh登录远程主机。
- > 主机需要支持密码登录。请确认并修改`/etc/ssh/sshd_config`中`PasswordAuthentication yes`选项，然后重启sshd服务`service sshd restart`。
- 你需要生成一对公私钥，私钥放入本仓库secret的KEY字段，公钥放入目标机器的`~/.ssh/authorized_keys`，来保证rsync命令授权复制到app-damebot目录。
- 请保证硬盘空间和内存足够。目前大概需要10G硬盘基础空间以及1.5G内存（深度学习模型存储暂时由docker管理，请注意扩容`/var`分区）。
- 如果是旧数据迁移的情况，请使用tar cvpzf <备份的文件名>.tar.gz damebot_workspace --exclude=damebot_workspace/cache/logs备份damebot数据并解压到新的机器（用户目录下）。
- > 请注意解压时也要带权限，并且要使用sudo解压（`sudo tar xvpzf <备份的文件名>.tar.gz`）。damebot依赖真实文件权限管理组间访问性。

## 在线云开发

有疑问可以加入测试群 726525232

![temp_qrcode_share](https://user-images.githubusercontent.com/14890194/128171280-07441de8-c952-47ad-98cb-bf65d3c9a42c.png)

请先Fork本项目。将Pull Request提交到本项目后，你（应当）可以在测试群收到提示信息。

你可以参考 [Github 贡献指南](https://docs.github.com/cn/github/collaborating-with-pull-requests/getting-started/about-collaborative-development-models) 
来了解如何在Github上进行协作，使用git进行commit、push以及基于Fork和Pull Request贡献代码。

使用连接 `https://gitpod.io/#https://github.com/<你的用户名>/damebot` 进入IDE。

当bot加载好时，下方terminal会提示open xxx to test damebot，在浏览器中打开即可测试damebot。

> 当你修改代码并保存时，bot会自动重新加载。这时候请重新等待url出现后，才说明bot已经加载好，再进行测试。

需要查看调试信息时，切换IDE右下角的Terminal即可看到bot所输出的调试信息。在开发中默认的日志级别为DEBUG。
