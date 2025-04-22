import os
from multiprocessing import Process
import signal
import time
import requests
from logging import getLogger
import subprocess
import collections
import json

import gradio as gr

from channel import channel_factory
from common import const
from config import load_config, conf
from plugins import *

logger = getLogger(__name__)
current_process_instance = None

# --- 配置常量 ---
CONFIG_FILE_PATH = 'config.json'

def check_gewechat_online():
    """检查gewechat用户是否在线
    Returns:
        tuple: (是否在线, 错误信息)
    """
    try:
        if conf().get("channel_type") != "gewechat":
            return False, "非gewechat，无需检查"
        
        base_url = conf().get("gewechat_base_url")
        token = conf().get("gewechat_token")
        app_id = conf().get("gewechat_app_id")
        if not all([base_url, token, app_id]):
            return False, "gewechat配置不完整"

        from lib.gewechat.client import GewechatClient
        client = GewechatClient(base_url, token)
        online_status = client.check_online(app_id)
        
        if not online_status:
            return False, "获取在线状态失败"
            
        if not online_status.get('data', False):
            logger.info("Gewechat用户未在线")
            return False, "用户未登录"
            
        return True, None
        
    except Exception as e:
        logger.error(f"检查gewechat在线状态失败: {str(e)}")
        return False, f"检查在线状态出错: {str(e)}"

def get_gewechat_profile():
    """获取gewechat用户信息并下载头像，仅在用户在线时返回信息"""
    try:
        is_online, error_msg = check_gewechat_online()
        if not is_online:
            logger.info(f"Gewechat状态检查: {error_msg}")
            return None, None
            
        from lib.gewechat.client import GewechatClient
        base_url = conf().get("gewechat_base_url")
        token = conf().get("gewechat_token")
        app_id = conf().get("gewechat_app_id")
        
        client = GewechatClient(base_url, token)
        profile = client.get_profile(app_id)
        
        if not profile or 'data' not in profile:
            return None, None
            
        user_info = profile['data']
        nickname = user_info.get('nickName', '未知')
        
        # 下载头像
        avatar_url = user_info.get('bigHeadImgUrl')
        avatar_path = None
        
        if avatar_url:
            try:
                avatar_path = 'tmp/avatar.png'
                os.makedirs('tmp', exist_ok=True)
                response = requests.get(avatar_url)
                if response.status_code == 200:
                    with open(avatar_path, 'wb') as f:
                        f.write(response.content)
            except Exception as e:
                logger.error(f"下载头像失败: {str(e)}")
                avatar_path = None
                
        return nickname, avatar_path
    except Exception as e:
        logger.error(f"获取Gewechat用户信息失败: {str(e)}")
        return None, None

def start_channel(channel_name: str):
    channel = channel_factory.create_channel(channel_name)
    available_channels = [
        "wx",
        "terminal",
        "wechatmp",
        "wechatmp_service",
        "wechatcom_app",
        "wework",
        "wechatcom_service",
        "gewechat",
        const.FEISHU,
        const.DINGTALK
    ]
    if channel_name in available_channels:
        PluginManager().load_plugins()
    channel.startup()

def run():
    try:
        # load config
        load_config()
        # create channel
        channel_name = conf().get("channel_type", "wx")
        
        # 获取gewechat用户信息
        if channel_name == "gewechat":
            get_gewechat_profile()

        start_channel(channel_name)
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)

def start_run():
    global current_process_instance

    if current_process_instance is not None and current_process_instance.is_alive():
        os.kill(current_process_instance.pid, signal.SIGTERM)  # 杀掉当前进程
        current_process_instance.join()  # 等待当前进程结束
    
    current_process_instance = Process(target=run)
    current_process_instance.start()
    time.sleep(15)  # 等待进程启动
    load_config()
    # 重启后获取用户状态
    if not current_process_instance.is_alive():
        return (
            gr.update(value="重启失败❌ 请重试"), # 状态
            gr.update(visible=False), # 刷新按钮
            gr.update(visible=False), # 刷新状态按钮
            gr.update(visible=True, variant="secondary"), # 重启按钮
            gr.update(visible=False), # 退出按钮
            gr.update(visible=False), # 二维码
            gr.update(visible=False)  # 头像
        )
        
    if conf().get("channel_type") == "gewechat":
        nickname, _ = get_gewechat_profile()
        if nickname:
            return (
                gr.update(value=f"重启成功😀 [{nickname}]🤖  已在线✅"), # 状态
                gr.update(visible=False), # 刷新二维码按钮
                gr.update(visible=True), # 刷新状态按钮
                gr.update(visible=True, variant="secondary"), # 重启按钮
                gr.update(visible=True), # 退出按钮
                gr.update(visible=False), # 二维码
                gr.update(visible=True, value=get_avatar_image()) # 头像
            )
        else:
            return (
                gr.update(value="重启成功😀 但用户未登录❗"), # 状态
                gr.update(visible=True), # 刷新二维码按钮
                gr.update(visible=True), # 刷新状态按钮
                gr.update(visible=True, variant="secondary"), # 重启按钮
                gr.update(visible=False),# 退出按钮
                gr.update(visible=True, value=get_qrcode_image()), # 二维码
                gr.update(visible=False) # 头像
            )
    return (
        gr.update(value="重启成功😀"), # 状态
        gr.update(visible=True), # 刷新二维码按钮
        gr.update(visible=False), # 刷新状态按钮
        gr.update(visible=True, variant="secondary"), # 重启按钮
        gr.update(visible=False), # 退出按钮
        gr.update(visible=True, value=get_qrcode_image()), # 二维码
        gr.update(visible=False) # 头像
    )
    
def get_qrcode_image():
    image_path = 'tmp/login.png'
    if os.path.exists(image_path):
        return image_path
    else:
        return None

def get_avatar_image():
    image_path = 'tmp/avatar.png'
    if os.path.exists(image_path):
        return image_path
    else:
        return None

def verify_login(username, password):
    correct_username = conf().get("web_ui_username", "dow")
    correct_password = conf().get("web_ui_password", "dify-on-wechat")
    if username == correct_username and password == correct_password:
        return True
    return False

def login(username, password):
    if verify_login(username, password):
        # 获取用户信息
        nickname, avatar_path = None, None
        is_gewechat = conf().get("channel_type") == "gewechat"
        if is_gewechat:
            nickname, avatar_path = get_gewechat_profile()
        show_qrcode = not (is_gewechat and avatar_path)
        status_text = "启动成功😀 " + (f"[{nickname}]🤖  已在线✅" if nickname else "")
            
        return (
            gr.update(visible=True, value=status_text),  # login_status
            gr.update(visible=show_qrcode),             # qrcode_image visibility
            gr.update(visible=True),                    # restart_button visibility
            gr.update(visible=show_qrcode),             # refresh_qrcode_button visibility
            gr.update(visible=False),                   # username_input
            gr.update(visible=False),                   # password_input
            gr.update(visible=False),                   # login_button
            gr.update(value=avatar_path, visible=bool(avatar_path)), # user_avatar
            gr.update(visible=False),                   # login_form
            gr.update(visible=True),                    # control_group
            gr.update(visible=True)                     # <<-- protected_content_area
        )
    else:
        # 登录失败时，确保受保护区域也是隐藏的
        return (
            gr.update(visible=True, value="用户名或密码错误"), # login_status
            gr.update(visible=False),                   # qrcode_image
            gr.update(visible=False),                   # restart_button
            gr.update(visible=False),                   # refresh_qrcode_button
            gr.update(visible=True),                    # username_input
            gr.update(visible=True),                    # password_input
            gr.update(visible=True),                    # login_button
            gr.update(visible=False),                   # user_avatar
            gr.update(visible=True),                    # login_form
            gr.update(visible=False),                   # control_group
            gr.update(visible=False)                    # <<-- protected_content_area
        )

def logout():
    """退出登录
    Returns:
        tuple: (状态文本, 刷新按钮, 刷新状态按钮, 重启按钮, 退出按钮, 二维码, 头像)
    """
    try:
        # 检查是否是 gewechat 且在线
        if conf().get("channel_type") != "gewechat" or not check_gewechat_online()[0]:
            return (
                gr.update(value="非gewechat或不在线，无需退出登录"), # login_status
                gr.update(visible=True), # refresh_qrcode_button
                gr.update(visible=True), # refresh_login_status_button
                gr.update(visible=True), # restart_button
                gr.update(visible=False),# logout_button
                gr.update(visible=True, value=get_qrcode_image()), # qrcode_image
                gr.update(visible=False), # user_avatar
                gr.update(visible=True),  # login_form
                gr.update(visible=False), # control_group
                gr.update(visible=False) # <<-- protected_content_area
            )

        # 调用 gewechat 退出接口
        from lib.gewechat.client import GewechatClient
        base_url = conf().get("gewechat_base_url")
        token = conf().get("gewechat_token")
        app_id = conf().get("gewechat_app_id")
        if not all([base_url, token, app_id]):
            return (
                gr.update(value="gewechat配置不完整，无法退出登录😭"), # login_status
                gr.update(visible=False), # refresh_qrcode_button
                gr.update(visible=True), # refresh_login_status_button
                gr.update(visible=True), # restart_button
                gr.update(visible=True), # logout_button
                gr.update(visible=False), # qrcode_image
                gr.update(visible=True), # user_avatar
                gr.update(visible=False), # login_form
                gr.update(visible=True),  # control_group
                gr.update(visible=False), # logout_button
                gr.update(visible=False), # qrcode_image
                gr.update(visible=True),  # user_avatar
                gr.update(visible=False), # login_form
                gr.update(visible=True),  # control_group
                gr.update(visible=False) # <<-- protected_content_area
            )
        
        client = GewechatClient(base_url, token)
        result = client.logout(app_id)
        
        if not result or result.get('ret') != 200:
            logger.error(f"退出登录失败 {result}")
            return (
                gr.update(value=f"退出登录失败 {result}, 请重试"), # login_status
                gr.update(visible=False), # refresh_qrcode_button
                gr.update(visible=True), # refresh_login_status_button
                gr.update(visible=True), # restart_button
                gr.update(visible=True), # logout_button
                gr.update(visible=False), # qrcode_image
                gr.update(visible=True), # user_avatar
                gr.update(visible=False), # login_form
                gr.update(visible=True),  # control_group
                gr.update(visible=True),  # logout_button
                gr.update(visible=False), # qrcode_image
                gr.update(visible=True),  # user_avatar
                gr.update(visible=False), # login_form
                gr.update(visible=True),  # control_group
                gr.update(visible=False) # <<-- protected_content_area
            )

        return (
            gr.update(value="退出登录成功😀 点击重启服务按钮可重新登录"), # login_status
            gr.update(visible=False), # refresh_qrcode_button
            gr.update(visible=False), # refresh_login_status_button
            gr.update(visible=True, variant="primary"), # restart_button
            gr.update(visible=False), # logout_button
            gr.update(visible=False), # qrcode_image
            gr.update(visible=False), # user_avatar
            gr.update(visible=True),  # login_form
            gr.update(visible=False), # control_group
            gr.update(visible=False) # <<-- protected_content_area
        )
        
    except Exception as e:
        logger.error(f"退出登录出错: {str(e)}")
        return (
            gr.update(value=f"退出登录失败😭 {str(e)}"), # login_status
            gr.update(visible=False), # refresh_qrcode_button
            gr.update(visible=True), # refresh_login_status_button
            gr.update(visible=True), # restart_button
            gr.update(visible=True), # logout_button
            gr.update(visible=False), # qrcode_image
            gr.update(visible=True), # user_avatar
            gr.update(visible=False), # login_form
            gr.update(visible=True),  # control_group
            gr.update(visible=False) # <<-- protected_content_area
        )

def show_logout_confirm():
    """显示退出确认对话框"""
    return (
        gr.update(visible=True),  # 显示确认对话框
        gr.update(visible=False)  # 隐藏控制按钮组
    )

def cancel_logout():
    """取消退出"""
    return (
        gr.update(visible=False),  # 隐藏确认对话框
        gr.update(visible=True)    # 显示控制按钮组
    )

def show_restart_confirm():
    """显示重启确认对话框"""
    return (
        gr.update(visible=True),  # 显示确认对话框
        gr.update(visible=False)  # 隐藏控制按钮组
    )

def cancel_restart():
    """取消重启"""
    return (
        gr.update(visible=False),  # 隐藏确认对话框
        gr.update(visible=True)    # 显示控制按钮组
    )

def refresh_qrcode():
    """刷新二维码"""
    return (
        gr.update(value="二维码刷新成功😀"),
        gr.update(value=get_qrcode_image()),
    )

def refresh_login_status():
    """检查登录状态并返回更新信息
    Returns:
        tuple: (状态文本, 是否显示二维码, 头像)
    """
    is_gewechat = conf().get("channel_type") == "gewechat"
    if not is_gewechat:
        return (
            gr.update(value="登录状态刷新成功😀 非gewechat，无需检查登录状态"),
            gr.update(visible=True),
            gr.update(visible=False)
        )
        
    nickname, avatar_path = get_gewechat_profile()
    if nickname:
        return (
            gr.update(value=f"登录状态刷新成功😀 [{nickname}]🤖  已在线✅"),
            gr.update(visible=False),
            gr.update(value=avatar_path, visible=True)
        )
    else:
        return (
            gr.update(value="登录状态刷新成功😀 用户未登录❗"),
            gr.update(visible=True),
            gr.update(visible=False)
        )

def get_log_tail(log_file='run.log', lines=50):
    """获取日志文件末尾指定行数的内容"""
    try:
        # 检查文件是否存在
        if not os.path.exists(log_file):
            return f"错误：日志文件 '{log_file}' 未找到。"
        
        # 使用 tail 命令获取日志
        # 注意：这在 Windows 上可能无效，需要替代方案（如读取文件）
        # 确保 tail 命令存在
        result = subprocess.run(['which', 'tail'], capture_output=True, text=True)
        if result.returncode != 0:
             # Windows 或无 tail 命令的替代方案：读取文件最后 N 行
             try:
                 with open(log_file, 'r', encoding='utf-8') as f:
                     # 使用 deque 高效获取末尾行
                     log_lines = collections.deque(f, maxlen=lines)
                     return "\n".join(log_lines)
             except Exception as e:
                 logger.error(f"读取日志文件失败: {e}")
                 return f"错误：无法读取日志文件 '{log_file}'。错误: {e}"

        # 使用 tail 命令 (Linux/macOS)
        result = subprocess.run(['tail', '-n', str(lines), log_file],
                                capture_output=True, text=True, check=False)
                                
        if result.returncode == 0:
            return result.stdout
        else:
            # 即使 tail 失败，也尝试读取文件
             try:
                 with open(log_file, 'r', encoding='utf-8') as f:
                     log_lines = collections.deque(f, maxlen=lines)
                     return "\n".join(log_lines)
             except Exception as e:
                 logger.error(f"tail命令失败后读取日志文件也失败: {e}")
                 return f"错误: tail命令执行失败({result.returncode}) 且无法读取日志文件。错误: {result.stderr}"
            
    except Exception as e:
        logger.error(f"获取日志时发生意外错误: {str(e)}")
        return f"获取日志时发生意外错误: {str(e)}"

def get_config_content():
    """读取 config.json 文件内容"""
    try:
        if not os.path.exists(CONFIG_FILE_PATH):
            return f"错误: 配置文件 '{CONFIG_FILE_PATH}' 未找到。"
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            # 直接返回原始文本，让 gr.Code 处理
            return f.read()
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        return f"读取配置文件时出错: {str(e)}"

def save_config_content(new_content_str):
    """验证 JSON 格式并保存到 config.json"""
    try:
        # 1. 验证 JSON 格式是否有效
        parsed_data = json.loads(new_content_str)
    except json.JSONDecodeError as e:
        logger.error(f"保存配置失败 - JSON 格式无效: {e}")
        return f"保存失败: JSON 格式无效 - {str(e)}"
    except Exception as e:
        logger.error(f"保存配置失败 - 解析 JSON 时发生意外错误: {e}")
        return f"保存失败: 解析 JSON 时发生意外错误 - {str(e)}"

    try:
        # 2. 格式化写入文件
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=4, ensure_ascii=False)
        logger.info("配置文件已成功保存。")
        return "配置已成功保存！请注意，部分更改可能需要重启主程序(app.py)才能生效。"
    except IOError as e:
        logger.error(f"保存配置文件到磁盘时失败: {e}")
        return f"保存失败: 写入文件时出错 - {str(e)}"
    except Exception as e:
        logger.error(f"保存配置文件时发生意外错误: {e}")
        return f"保存失败: 发生意外错误 - {str(e)}"

def update_timer():
    return time.time()

with gr.Blocks(title="Dify on WeChat", theme=gr.themes.Soft(radius_size=gr.themes.sizes.radius_lg)) as demo:
    # 顶部状态栏
    with gr.Row(equal_height=True):
        with gr.Column(scale=1):
            login_status = gr.Textbox(
                label="状态",
                value="",
                interactive=False,
                visible=True,
                container=True
            )
    
    # 主要内容区
    with gr.Row(equal_height=True):
        # 左侧图片区
        with gr.Column(scale=4):
            with gr.Column(variant="box"):
                qrcode_image = gr.Image(
                    value=get_qrcode_image(),
                    label="微信登录二维码",
                    show_label=True,
                    container=True,
                    visible=False,
                    height=450
                )
                user_avatar = gr.Image(
                    value=get_avatar_image(),
                    label="当前登录用户",
                    show_label=True,
                    container=True,
                    visible=False,
                    height=450
                )

        # 右侧控制区
        with gr.Column(scale=3, min_width=300):
            # 登录表单
            with gr.Column(visible=True) as login_form:
                with gr.Column(variant="box"):
                    gr.Markdown("### 登录")
                    username_input = gr.Textbox(
                        label="用户名",
                        placeholder="请输入用户名",
                        container=True
                    )
                    password_input = gr.Textbox(
                        label="密码",
                        type="password",
                        placeholder="请输入密码",
                        container=True
                    )
                    with gr.Row():
                        login_button = gr.Button(
                            "登录",
                            variant="primary",
                            scale=2
                        )
            
            # 控制按钮组
            with gr.Column(visible=False) as control_group:
                with gr.Row(equal_height=True, variant="panel"):
                    with gr.Column(scale=1):
                        refresh_qrcode_button = gr.Button(
                            "刷新二维码",
                            visible=False,
                            variant="primary",
                            size="lg",
                            min_width=120
                        )
                    with gr.Column(scale=1):
                        refresh_login_status_button = gr.Button(
                            "刷新登录状态",
                            visible=True,
                            variant="primary",
                            size="lg",
                            min_width=120
                        )
                    with gr.Column(scale=1):
                        restart_button = gr.Button(
                            "重启服务",
                            visible=False,
                            variant="secondary",
                            size="lg",
                            min_width=120
                        )
                    with gr.Column(scale=1):
                        logout_button = gr.Button(
                            "退出登录",
                            visible=True,
                            variant="secondary",
                            size="lg",
                            min_width=120
                        )

    # 退出确认对话框
    with gr.Column(visible=False) as logout_confirm:
        with gr.Column(variant="box"):
            gr.Markdown("### 确认退出")
            gr.Markdown("确定要退出登录吗？")
            with gr.Row():
                logout_confirm_button = gr.Button(
                    "确认退出",
                    variant="primary",
                    size="sm"
                )
                logout_cancel_button = gr.Button(
                    "取消",
                    variant="secondary",
                    size="sm"
                )

    # 重启确认对话框
    with gr.Column(visible=False) as restart_confirm:
        with gr.Column(variant="box"):
            gr.Markdown("### 确认重启")
            gr.Markdown("确定要重启服务吗？")
            with gr.Row():
                restart_confirm_button = gr.Button(
                    "确认重启",
                    variant="primary",
                    size="sm"
                )
                restart_cancel_button = gr.Button(
                    "取消",
                    variant="secondary",
                    size="sm"
                )

    # 1. 先显式创建 Column 对象
    protected_content_area = gr.Column(visible=False)
    # 2. 使用创建的对象作为上下文管理器
    with protected_content_area:
        # 日志显示区域
        with gr.Accordion("实时日志", open=False):
            log_output = gr.Textbox(
                label=f"日志内容 (run.log - 最后 50 行)",
                lines=20,
                interactive=False,
                max_lines=20
            )
            timer = gr.Timer(5)

        # 配置管理区域
        with gr.Accordion("配置管理 (config.json)", open=False):
            gr.Markdown(
                """**警告:** 
                直接修改 JSON 配置存在风险，可能导致程序无法启动。  
                保存前请确保 JSON 格式严格正确 (例如，所有字符串使用双引号, 末尾无多余逗号)。  
                修改后，通常需要**重启主程序 (app.py) 或通过 Web UI 重启服务**才能使所有更改生效。
                """
            )
            config_editor = gr.Code(
                label="config.json 内容 (可编辑)", 
                language="json", 
                interactive=True, 
                lines=25
            )
            with gr.Row():
                 save_config_button = gr.Button("保存配置", variant="primary")
            config_status = gr.Textbox(label="保存状态", interactive=False)

    # 事件处理
    login_button.click(
        login,
        inputs=[username_input, password_input],
        outputs=[
            login_status,
            qrcode_image,
            restart_button,
            refresh_qrcode_button,
            username_input,
            password_input,
            login_button,
            user_avatar,
            login_form,
            control_group,
            protected_content_area
        ]
    )

    restart_button.click(
        show_restart_confirm,
        outputs=[
            restart_confirm,
            control_group
        ]
    )
    
    restart_cancel_button.click(
        cancel_restart,
        outputs=[
            restart_confirm,
            control_group
        ]
    )
    
    restart_confirm_button.click(
        start_run,
        outputs=[
            login_status,
            refresh_qrcode_button,
            refresh_login_status_button,
            restart_button,
            logout_button,
            qrcode_image,
            user_avatar
        ]
    ).then(
        cancel_restart,  # 重启后关闭确认对话框
        outputs=[
            restart_confirm,
            control_group
        ]
    )

    refresh_qrcode_button.click(
        refresh_qrcode,
        outputs=[
            login_status,
            qrcode_image
        ]
    )
    
    logout_button.click(
        show_logout_confirm,
        outputs=[
            logout_confirm,
            control_group
        ]
    )
    
    logout_cancel_button.click(
        cancel_logout,
        outputs=[
            logout_confirm,
            control_group
        ]
    )
    
    logout_confirm_button.click(
        logout,
        outputs=[
            login_status,
            refresh_qrcode_button,
            refresh_login_status_button,
            restart_button,
            logout_button,
            qrcode_image,
            user_avatar,
            login_form,
            control_group,
            protected_content_area
        ]
    ).then(
        cancel_logout,  # 退出后关闭确认对话框
        outputs=[
            logout_confirm,
            control_group
        ]
    )

    # 添加刷新状态按钮事件
    refresh_login_status_button.click(
        refresh_login_status,
        outputs=[
            login_status,
            qrcode_image,
            user_avatar
        ]
    )

    # Timer 事件处理 (日志) 和 Config 事件处理 (引用保持不变)
    demo.load(get_log_tail, [], log_output) 
    timer.tick(get_log_tail, inputs=None, outputs=log_output)
    demo.load(get_config_content, [], config_editor)
    save_config_button.click(save_config_content, inputs=[config_editor], outputs=[config_status])

if __name__ == "__main__":
    start_run()
    demo.launch(server_name="0.0.0.0", server_port=conf().get("web_ui_port", 7860), share=True)
