<div align="center">
  <img src="https://github.com/lanol/dify-on-wechat/assets/5104827/ed26874b-87ca-4672-8b5d-410e70c8e0e7" alt="Dify on WeChat Logo" width="150"/>
  <h1>Dify on WeChat (增强版 Fork)</h1>
  <p>
    本项目是 <a href="https://github.com/hanfangyuan4396/dify-on-wechat">dify-on-wechat</a> 的一个增强版分支，集成了多项实用的修改。
  </p>
  <p>
    <a href="https://github.com/lanol/dify-on-wechat/stargazers"><img src="https://img.shields.io/github/stars/lanol/dify-on-wechat?style=social" alt="GitHub stars"></a>
  </p>
</div>

---

## ✨ 主要修改内容

本分支主要包含以下增强功能：

1.  **增强型 Web UI (`web_ui.py`)** 🖥️
    *   **实时日志输出:** 直接在 Web UI 中监控机器人活动。
    *   **配置编辑器:** 通过界面方便地修改 `config.json` 设置。
        *   _[图片占位符: 配置编辑器截图]_*
    *   **安全访问:** 直接在 `config.json` 中为 Web UI 设置用户名和密码。
        *   _[图片占位符: 登录配置截图]_*
    *   **访问端口:** 默认本机端口 7860, 可以通过 `--public` 参数使用 Gradio 提供的临时域名地址。

2.  **与自己对话进行调试** 💬
    *   增加了允许机器人回复自己发送的私聊消息的选项。
    *   **启用方法:** 在项目根目录的 `config.json` 文件中设置 `"trigger_by_self": true`。
    *   *此功能便于在只有一个微信号时调试机器人。*

3.  **升级版 `sum4all` 插件** 💡
    *   **扩展 LLM 支持:** 集成了 **阿里百炼 (Aliyun Tongyi)** 和 **硅基流动 (SiliconFlow)** 的 API 接口。
    *   **灵活的模型选择:** 可以为总结任务（网页、文件）和视觉任务（图片分析）指定不同的大语言模型。
    *   **微信公众号文章优化:** 针对微信公众号文章增加了特殊处理，尝试使用 `requests` + `BeautifulSoup4` 直接请求和解析，以绕过部分反爬虫限制。（注：此方法经测试有效，若遇反爬警告可能与服务器 IP 有关）。
    *   *详细配置说明请参考 `sum4all` 插件目录下的 `config.json.template` 文件。*

4.  **改进的进程管理脚本** ⚙️
    *   **`run.sh` (启动脚本):**
        *   检测并终止任何已存在的 `web_ui.py` 进程，防止重复运行。
        *   激活指定的 Conda 环境 (需要在脚本中预先定义环境名称)。
        *   使用 `nohup` 在后台启动 `web_ui.py`。
        *   通过 `tail` 输出日志以便实时监控。
    *   **`stop.sh` (停止脚本):**
        *   查找与当前项目目录关联的特定 `python web_ui.py` 进程。
        *   平稳地终止该进程。

## ⚠️ 重要提示

*   `run.sh` 和 `stop.sh` 脚本**仅适用于通过 `web_ui.py` 启动应用的情况**。如果您使用 `app.py` 启动，这些脚本**不适用**。

## ⭐ 支持与反馈

*   如果您觉得这些改进有用，请考虑给本仓库点一个 **Star**！🌟
*   如果您希望 `sum4all` 插件支持其他大模型，欢迎提交 **Issue**。

