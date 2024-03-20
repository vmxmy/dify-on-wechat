<div align="center">
<h1>Dify on WeChat</h1>

本项目为 [chatgpt-on-wechat](https://github.com/zhayujie/chatgpt-on-wechat)下游分支
额外对接了LLMOps平台 [Dify](https://github.com/langgenius/dify)，支持Dify智能助手模型，调用工具和知识库。

</div>



![image-1](./docs/images/image1.jpg)

![image-2](./docs/images/image2.jpg)

目前Dify已经测试过的通道如下：

- [x] **个人微信**
- [x] **企业微信应用** 
- [ ] **公众号** 待测试
- [ ] **钉钉** 待测试
- [ ] **飞书** 待测试



# Dify on WeChat 交流群

添加我的微信拉你进群

<img width="240" src="./docs/images/image3.png">



# 快速开始

接入非Dify机器人可参考原项目文档 [chatgpt-on-wechat](https://github.com/zhayujie/chatgpt-on-wechat)、[项目搭建文档](https://docs.link-ai.tech/cow/quick-start)

下文介绍如何快速接入Dify

## 准备

### 1. 账号注册

进入[Dify App](https://cloud.dify.ai) 官网注册账号，创建一个应用并发布，然后在概览页面创建保存api密钥，同时记录api url，一般为https://api.dify.ai/v1

### 2.运行环境

支持 Linux、MacOS、Windows 系统（可在Linux服务器上长期运行)，同时需安装 `Python`。

python推荐3.8以上版本，已在ubuntu测试过3.11.6版本可以成功运行。

**(1) 克隆项目代码：**

```bash
git clone https://github.com/hanfangyuan4396/dify-on-wechat
cd dify-on-wechat/
```

**(2) 安装核心依赖 (必选)：**
> 能够使用`itchat`创建机器人，并具有文字交流功能所需的最小依赖集合。
```bash
pip3 install -r requirements.txt  # 国内可以在该命令末尾添加 "-i https://mirrors.aliyun.com/pypi/simple" 参数，使用阿里云镜像源安装依赖
```

**(3) 拓展依赖 (可选，建议安装)：**

```bash
pip3 install -r requirements-optional.txt # 国内可以在该命令末尾添加 "-i https://mirrors.aliyun.com/pypi/simple" 参数，使用阿里云镜像源安装依赖
```
> 如果某项依赖安装失败可注释掉对应的行再继续

## 配置

配置文件的模板在根目录的`config-template.json`中，需复制该模板创建最终生效的 `config.json` 文件：

```bash
  cp config-template.json config.json
```

然后在`config.json`中填入配置，以下是对默认配置的说明，可根据需要进行自定义修改（**如果复制下方的示例内容，请去掉注释**）：

```bash
# config.json文件内容示例
{
  "dify_api_base": "https://api.dify.ai/v1",    # dify base url
  "dify_api_key": "app-xxx",                    # dify api key
  "dify_agent": true,                          # dify助手类型，如果是基础助手请设置为false，智能助手请设置为true, 当前为true
  "dify_convsersation_max_messages": 5,         # dify目前不支持设置历史消息长度，暂时使用超过最大消息数清空会话的策略，缺点是没有滑动窗口，会突然丢失历史消息, 当前为5
  "channel_type": "wx",                         # 通道类型，当前为个人微信
  "model": "dify",                              # 模型名称，当前对应dify平台
  "single_chat_prefix": [""],                   # 私聊时文本需要包含该前缀才能触发机器人回复
  "single_chat_reply_prefix": "",               # 私聊时自动回复的前缀，用于区分真人
  "group_chat_prefix": ["@bot"],                # 群聊时包含该前缀则会触发机器人回复
  "group_name_white_list": ["ALL_GROUP"],       # 机器人回复的群名称列表
}

```
上述示例文件是个人微信对接dify的极简配置，详细配置说明需要查看config.py，注意**不要修改config.py中的值**，config.py只是校验是否是有效的key，最终**生效的配置请在config.json修改**。

## 运行

### 1.本地运行

如果是开发机 **本地运行**，直接在项目根目录下执行：

```bash
python3 app.py                                    # windows环境下该命令通常为 python app.py
```

终端输出二维码后，使用微信进行扫码，当输出 "Start auto replying" 时表示自动回复程序已经成功运行了（注意：用于登录的微信需要在支付处已完成实名认证）。扫码登录后你的账号就成为机器人了，可以在微信手机端通过配置的关键词触发自动回复 (任意好友发送消息给你，或是自己发消息给好友)，参考[#142](https://github.com/zhayujie/chatgpt-on-wechat/issues/142)。

### 2.服务器部署

使用nohup命令在后台运行程序：

```bash
nohup python3 app.py & tail -f nohup.out          # 在后台运行程序并通过日志输出二维码
```
扫码登录后程序即可运行于服务器后台，此时可通过 `ctrl+c` 关闭日志，不会影响后台程序的运行。使用 `ps -ef | grep app.py | grep -v grep` 命令可查看运行于后台的进程，如果想要重新启动程序可以先 `kill` 掉对应的进程。日志关闭后如果想要再次打开只需输入 `tail -f nohup.out`。此外，`scripts` 目录下有一键运行、关闭程序的脚本供使用。

> **多账号支持：** 将项目复制多份，分别启动程序，用不同账号扫码登录即可实现同时运行。

> **特殊指令：** 用户向机器人发送 **#reset** 即可清空该用户的上下文记忆。

### 3.Docker部署

暂是没有构建镜像，待更新~



# 开发计划

- [ ] **完善文档：** README文档下班抽空写的，写的比较简单，之后写详细一些
- [ ] **Docker镜像构建：** 目前只支持源码部署
- [ ] **企业微信客服通道：** 支持企业微信客服
- [ ] **测试合并原项目PR：** 原项目有很多比较好的PR没有通过，之后会把一些比较好的feature测试合并进这个仓库
- [ ] **优化对接Dify：** 目前对接dify的很多代码写的还很潦草，以后逐步优化

也请各位大佬多多提PR，我社畜打工人，精力实在有限~

