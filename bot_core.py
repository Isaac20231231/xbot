import asyncio
import aiohttp
import json
import os
import sys
import time
import tomllib
from pathlib import Path
from datetime import datetime, timedelta
import logging

from loguru import logger

import WechatAPI
from database.XYBotDB import XYBotDB
from database.keyvalDB import KeyvalDB
from database.messsagDB import MessageDB
from database.message_counter import get_instance as get_message_counter  # 导入消息计数器
from utils.decorators import scheduler
from utils.plugin_manager import plugin_manager
from utils.xybot import XYBot
from utils.notification_service import init_notification_service, get_notification_service
import websockets  # 如果未导入，确保添加这行
import redis.asyncio as aioredis  # 新增

# 创建消息计数器实例
message_counter = get_message_counter()

# 导入管理后台模块
try:
    # 正确设置导入路径
    admin_path = str(Path(__file__).resolve().parent)
    if admin_path not in sys.path:
        sys.path.append(admin_path)

    # 导入管理后台服务器模块
    try:
        from admin.server import set_bot_instance as admin_set_bot_instance
        logger.debug("成功导入admin.server.set_bot_instance")
    except ImportError as e:
        logger.error(f"导入admin.server.set_bot_instance失败: {e}")
        # 创建一个空函数
        def admin_set_bot_instance(bot):
            logger.warning("admin.server.set_bot_instance未导入，调用被忽略")
            return None

    # 直接定义状态更新函数，不依赖导入
    def update_bot_status(status, details=None, extra_data=None):
        """更新bot状态，供管理后台读取"""
        try:
            # 使用统一的路径写入状态文件 - 修复路径问题
            status_file = Path(admin_path) / "admin" / "bot_status.json"
            root_status_file = Path(admin_path) / "bot_status.json"

            # 读取当前状态
            current_status = {}
            if status_file.exists():
                with open(status_file, "r", encoding="utf-8") as f:
                    current_status = json.load(f)

            # 更新状态
            current_status["status"] = status
            current_status["timestamp"] = time.time()
            if details:
                current_status["details"] = details

            # 添加额外数据
            if extra_data and isinstance(extra_data, dict):
                for key, value in extra_data.items():
                    current_status[key] = value

            # 确保目录存在
            status_file.parent.mkdir(parents=True, exist_ok=True)

            # 写入status_file
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(current_status, f)

            # 写入root_status_file
            with open(root_status_file, "w", encoding="utf-8") as f:
                json.dump(current_status, f)

            logger.debug(f"成功更新bot状态: {status}, 路径: {status_file} 和 {root_status_file}")

            # 输出更多调试信息
            if "nickname" in current_status:
                logger.debug(f"状态文件包含昵称: {current_status['nickname']}")
            if "wxid" in current_status:
                logger.debug(f"状态文件包含微信ID: {current_status['wxid']}")
            if "alias" in current_status:
                logger.debug(f"状态文件包含微信号: {current_status['alias']}")

        except Exception as e:
            logger.error(f"更新bot状态失败: {e}")

    # 定义设置bot实例的函数
    def set_bot_instance(bot):
        """设置bot实例到管理后台"""
        # 先调用admin模块的设置函数
        admin_set_bot_instance(bot)

        # 更新状态
        update_bot_status("initialized", "机器人实例已设置")
        logger.success("成功设置bot实例并更新状态")

        return bot

except ImportError as e:
    logger.error(f"导入管理后台模块失败: {e}")
    # 创建空函数，防止程序崩溃
    def set_bot_instance(bot):
        logger.warning("管理后台模块未正确导入，set_bot_instance调用被忽略")
        return None

    # 创建一个空的状态更新函数
    def update_bot_status(status, details=None):
        logger.debug(f"管理后台模块未正确导入，状态更新被忽略: {status}")


NUM_CONSUMERS = 1  # 可根据需要调整并发消费者数量
QUEUE_NAME = 'xbot'  # 自定义队列名

async def message_consumer(xybot, redis, message_db):
    while True:
        _, msg_json = await redis.blpop(QUEUE_NAME)
        message = json.loads(msg_json)
        logger.info(f"消息已出队并开始处理，队列: {QUEUE_NAME}，消息ID: {message.get('MsgId') or message.get('msgId')}")
        try:
            await xybot.process_message(message)
        except Exception as e:
            logger.error(f"消息处理异常: {e}")

async def http_poll_messages(xybot, api_host, api_port, wxid, redis, message_db):
    """通过HTTP API轮询拉取消息"""
    import time
    url = f"http://{api_host}:{api_port}/api/Msg/Sync"
    synckey = ""
    while True:
        try:
            payload = {"Scene": 0, "Synckey": synckey, "Wxid": wxid}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        addmsgs = data.get("Data", {}).get("AddMsgs", [])
                        for message in addmsgs:
                            await message_db.save_message(
                                msg_id=message.get("MsgId") or message.get("msgId") or 0,
                                new_msg_id=message.get("NewMsgId") or message.get("newMsgId") or 0,
                                sender_wxid=message.get("FromUserName", {}).get("string", ""),
                                from_wxid=message.get("ToUserName", {}).get("string", ""),
                                msg_type=message.get("MsgType") or message.get("category") or 0,
                                content=message.get("Content", {}).get("string", ""),
                                is_group=False
                            )
                            await redis.rpush(QUEUE_NAME, json.dumps(message, ensure_ascii=False))
                            logger.info(f"[HTTP] 消息已入队到队列 {QUEUE_NAME}，消息ID: {message.get('MsgId') or message.get('msgId')}")
                        # 更新synckey
                        if "Synckey" in data:
                            synckey = data["Synckey"]
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"HTTP拉取消息异常: {e}")
            await asyncio.sleep(1)

async def bot_core():
    # 设置工作目录
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)

    # 更新初始化状态
    update_bot_status("initializing", "系统初始化中")

    # 读取配置文件（使用新的配置管理器）
    try:
        from utils.config_manager import ConfigManager
        from utils.exceptions import ConfigurationException, WechatAPIException
        
        logger.info("🔧 bot_core使用新的配置管理器加载配置...")
        config_manager = ConfigManager()
        app_config = config_manager.config
        
        # 向后兼容：创建传统的config字典格式
        config = {
            "Protocol": {"version": app_config.protocol.version},
            "WechatAPIServer": {
                "host": app_config.wechat_api.host,
                "port": app_config.wechat_api.port,
                "mode": app_config.wechat_api.mode,
                "redis-host": app_config.wechat_api.redis_host,
                "redis-port": app_config.wechat_api.redis_port,
                "redis-password": app_config.wechat_api.redis_password,
                "redis-db": app_config.wechat_api.redis_db
            },
            "XYBot": {
                "version": app_config.xybot.version,
                "ignore-protection": app_config.xybot.ignore_protection,
                "enable-group-wakeup": app_config.xybot.enable_group_wakeup,
                "group-wakeup-words": app_config.xybot.group_wakeup_words,
                "robot-names": app_config.xybot.robot_names,
                "robot-wxids": app_config.xybot.robot_wxids,
                "github-proxy": app_config.xybot.github_proxy,
                "admins": app_config.xybot.admins,
                "disabled-plugins": app_config.xybot.disabled_plugins,
                "timezone": app_config.xybot.timezone,
                "auto-restart": app_config.xybot.auto_restart,
                "files-cleanup-days": app_config.xybot.files_cleanup_days,
                "ignore-mode": app_config.xybot.ignore_mode,
                "whitelist": app_config.xybot.whitelist,
                "blacklist": app_config.xybot.blacklist
            },
            "AutoRestart": {
                "enabled": app_config.auto_restart.enabled,
                "check-interval": app_config.auto_restart.check_interval,
                "offline-threshold": app_config.auto_restart.offline_threshold,
                "max-restart-attempts": app_config.auto_restart.max_restart_attempts,
                "restart-cooldown": app_config.auto_restart.restart_cooldown,
                "check-offline-trace": app_config.auto_restart.check_offline_trace,
                "failure-count-threshold": app_config.auto_restart.failure_count_threshold,
                "reset-threshold-multiplier": app_config.auto_restart.reset_threshold_multiplier
            },
            "Notification": {
                "enabled": app_config.notification.enabled,
                "token": app_config.notification.token,
                "channel": app_config.notification.channel,
                "template": app_config.notification.template,
                "topic": app_config.notification.topic,
                "heartbeatThreshold": app_config.notification.heartbeat_threshold
            }
        }
        
        logger.success("✅ bot_core配置加载成功（使用优化后的配置管理器）")
        
    except ConfigurationException as e:
        logger.error(f"❌ bot_core配置错误: {e.message}")
        if hasattr(e, 'details') and e.details.get('config_key'):
            logger.error(f"错误的配置项: {e.details['config_key']}")
        update_bot_status("error", f"配置错误: {e.message}")
        return
    except ImportError as e:
        logger.warning(f"⚠️ bot_core无法导入新的配置管理器，回退到传统方式: {e}")
        # 回退到原来的配置读取方式
        config_path = script_dir / "main_config.toml"
        try:
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
            logger.success("读取主设置成功（传统方式）")
            
            # 确保 WechatAPIServer 中的 ws-url 配置可以正确读取
            if "WechatAPIServer" in config:
                # 调试输出所有键，帮助诊断
                logger.debug(f"WechatAPIServer 中的所有键: {list(config['WechatAPIServer'].keys())}")
        except Exception as e2:
            logger.error(f"读取主设置失败: {e2}")
            update_bot_status("error", f"配置加载失败: {e2}")
            return
    except Exception as e:
        logger.error(f"❌ bot_core配置系统发生未知错误: {e}")
        logger.error("详细错误信息:", exc_info=True)
        update_bot_status("error", f"配置系统错误: {e}")
        return

    # 启动WechatAPI服务
    # server = WechatAPI.WechatAPIServer()
    api_config = config.get("WechatAPIServer", {})
    api_host = api_config.get("host", "127.0.0.1")  # 获取自定义的API主机地址
    redis_host = api_config.get("redis-host", "127.0.0.1")
    redis_port = api_config.get("redis-port", 6379)
    logger.debug("WechatAPI 服务器地址: {}", api_host)
    logger.debug("Redis 主机地址: {}:{}", redis_host, redis_port)
    # server.start(port=api_config.get("port", 9000),
    #              mode=api_config.get("mode", "release"),
    #              redis_host=redis_host,
    #              redis_port=redis_port,
    #              redis_password=api_config.get("redis-password", ""),
    #              redis_db=api_config.get("redis-db", 0))

    # 读取协议版本设置
    protocol_version = config.get("Protocol", {}).get("version", "ipad").lower()
    logger.info(f"使用协议版本: {protocol_version}")

    # 统一实例化 WechatAPIClient
    from WechatAPI.Client import WechatAPIClient
    bot = WechatAPIClient(api_host, api_config.get("port", 9000), protocol_version=protocol_version)
    logger.success(f"✅ 成功加载统一 WechatAPIClient 客户端，protocol_version={getattr(bot, 'protocol_version', None)}")

    # 设置客户端属性
    bot.ignore_protect = config.get("XYBot", {}).get("ignore-protection", False)

    # 等待WechatAPI服务启动
    # time_out = 30  # 增加超时时间
    # while not await bot.is_running() and time_out > 0:
    #     logger.info("等待WechatAPI启动中")
    #     await asyncio.sleep(2)
    #     time_out -= 2

    # if time_out <= 0:
    #     logger.error("WechatAPI服务启动超时")
    #     # 更新状态
    #     update_bot_status("error", "WechatAPI服务启动超时")
    #     return None

    # if not await bot.check_database():
    #     logger.error("Redis连接失败，请检查Redis是否在运行中，Redis的配置")
    #     # 更新状态
    #     update_bot_status("error", "Redis连接失败")
    #     return None

    logger.success("WechatAPI服务已启动")

    # 更新状态
    update_bot_status("waiting_login", "等待微信登录")

    # 检查并创建robot_stat.json文件
    robot_stat_path = script_dir / "resource" / "robot_stat.json"
    if not os.path.exists(robot_stat_path):
        default_config = {
            "wxid": "",
            "device_name": "",
            "device_id": ""
        }
        os.makedirs(os.path.dirname(robot_stat_path), exist_ok=True)
        with open(robot_stat_path, "w") as f:
            json.dump(default_config, f)
        robot_stat = default_config
    else:
        with open(robot_stat_path, "r") as f:
            robot_stat = json.load(f)

    wxid = robot_stat.get("wxid", None)
    device_name = robot_stat.get("device_name", None)
    device_id = robot_stat.get("device_id", None)

    if not await bot.is_logged_in(wxid):
        while not await bot.is_logged_in(wxid):
            # 需要登录
            try:
                get_cached_info = await bot.get_cached_info(wxid)
                # logger.info("获取缓存登录信息:{}",get_cached_info)
                if get_cached_info:
                    #二次登录
                    twice = await bot.twice_login(wxid)
                    logger.info("二次登录:{}",twice)
                    if not twice:
                        logger.error("二次登录失败，请检查微信是否在运行中，或重新启动机器人")
                        # 尝试唤醒登录
                        logger.info("尝试唤醒登录...")
                        try:
                            # 准备唤醒登录
                            # 注意：awaken_login 方法只接受 wxid 参数
                            # 实际的 API 调用会将其作为 JSON 请求体中的 Wxid 字段发送

                            # 直接使用 aiohttp 调用 API，而不是使用 awaken_login 方法
                            # 这样我们可以更好地控制错误处理
                            async with aiohttp.ClientSession() as session:
                                # 根据协议版本选择不同的 API 路径
                                api_base = "/api"
                                api_url = f'http://{api_host}:{api_config.get("port", 9000)}{api_base}/Login/LoginTwiceAutoAuth'

                                # 准备请求参数
                                json_param = {
                                    "OS": device_name if device_name else "iPad",
                                    "Proxy": {
                                        "ProxyIp": "",
                                        "ProxyPassword": "",
                                        "ProxyUser": ""
                                    },
                                    "Url": "",
                                    "Wxid": wxid
                                }

                                logger.debug(f"发送唤醒登录请求到 {api_url} 参数: {json_param}")

                                try:
                                    # 发送请求
                                    response = await session.post(api_url, json=json_param)

                                    # 检查响应状态码
                                    if response.status != 200:
                                        logger.error(f"唤醒登录请求失败，状态码: {response.status}")
                                        raise Exception(f"服务器返回状态码 {response.status}")

                                    # 解析响应内容
                                    json_resp = await response.json()
                                    logger.debug(f"唤醒登录响应: {json_resp}")

                                    # 检查是否成功
                                    if json_resp and json_resp.get("Success"):
                                        # 尝试获取 UUID
                                        data = json_resp.get("Data", {})
                                        qr_response = data.get("QrCodeResponse", {}) if data else {}
                                        uuid = qr_response.get("Uuid", "") if qr_response else ""

                                        if uuid:
                                            logger.success(f"唤醒登录成功，获取到登录uuid: {uuid}")
                                            # 更新状态，记录UUID但没有二维码
                                            update_bot_status("waiting_login", f"等待微信登录 (UUID: {uuid})")
                                        else:
                                            logger.error("唤醒登录响应中没有有效的UUID")
                                            raise Exception("响应中没有有效的UUID")
                                    else:
                                        # 如果请求不成功，获取错误信息
                                        error_msg = json_resp.get("Message", "未知错误") if json_resp else "未知错误"
                                        logger.error(f"唤醒登录失败: {error_msg}")
                                        raise Exception(error_msg)

                                except Exception as e:
                                    logger.error(f"唤醒登录过程中出错: {e}")
                                    logger.error("将尝试二维码登录")
                                # 如果唤醒登录失败，回退到二维码登录
                                if not device_name:
                                    device_name = bot.create_device_name()
                                if not device_id:
                                    device_id = bot.create_device_id()
                                uuid, url = await bot.get_qr_code(device_id=device_id, device_name=device_name, print_qr=True)
                                logger.success("获取到登录uuid: {}", uuid)
                                logger.success("获取到登录二维码: {}", url)
                                # 更新状态，记录二维码URL
                                update_bot_status("waiting_login", "等待微信扫码登录", {
                                    "qrcode_url": url,
                                    "uuid": uuid,
                                    "expires_in": 240, # 默认240秒过期
                                    "timestamp": time.time()
                                })
                        except Exception as e:
                            logger.error("唤醒登录失败: {}", e)
                            # 如果唤醒登录出错，回退到二维码登录
                            if not device_name:
                                device_name = bot.create_device_name()
                            if not device_id:
                                device_id = bot.create_device_id()
                            uuid, url = await bot.get_qr_code(device_id=device_id, device_name=device_name, print_qr=True)
                            logger.success("获取到登录uuid: {}", uuid)
                            logger.success("获取到登录二维码: {}", url)
                            # 更新状态，记录二维码URL
                            update_bot_status("waiting_login", "等待微信扫码登录", {
                                "qrcode_url": url,
                                "uuid": uuid,
                                "expires_in": 240, # 默认240秒过期
                                "timestamp": time.time()
                            })

                else:
                    # 二维码登录
                    if not device_name:
                        device_name = bot.create_device_name()
                    if not device_id:
                        device_id = bot.create_device_id()
                    uuid, url = await bot.get_qr_code(device_id=device_id, device_name=device_name, print_qr=True)
                    logger.success("获取到登录uuid: {}", uuid)
                    logger.success("获取到登录二维码: {}", url)
                    # 更新状态，记录二维码URL
                    update_bot_status("waiting_login", "等待微信扫码登录", {
                        "qrcode_url": url,
                        "uuid": uuid,
                        "expires_in": 240, # 默认240秒过期
                        "timestamp": time.time()
                    })

                    # 检查状态文件是否正确更新
                    try:
                        status_file = script_dir / "admin" / "bot_status.json"
                        if status_file.exists():
                            with open(status_file, "r", encoding="utf-8") as f:
                                current_status = json.load(f)
                                if current_status.get("qrcode_url") != url:
                                    logger.warning("状态文件中的二维码URL与实际不符，尝试重新更新状态")
                                    # 再次更新状态
                                    update_bot_status("waiting_login", "等待微信扫码登录", {
                                        "qrcode_url": url,
                                        "uuid": uuid,
                                        "expires_in": 240,
                                        "timestamp": time.time()
                                    })
                    except Exception as e:
                        logger.error(f"检查状态文件失败: {e}")

                # 显示倒计时
                logger.info("等待登录中，过期倒计时：240")

            except Exception as e:
                logger.error("发生错误: {}", e)
                # 出错时重新尝试二维码登录
                if not device_name:
                    device_name = bot.create_device_name()
                if not device_id:
                    device_id = bot.create_device_id()
                uuid, url = await bot.get_qr_code(device_id=device_id, device_name=device_name, print_qr=True)
                logger.success("获取到登录uuid: {}", uuid)
                logger.success("获取到登录二维码: {}", url)
                # 更新状态，记录二维码URL
                update_bot_status("waiting_login", "等待微信扫码登录", {
                    "qrcode_url": url,
                    "uuid": uuid,
                    "expires_in": 240, # 默认240秒过期
                    "timestamp": time.time()
                })

            while True:
                stat, data = await bot.check_login_uuid(uuid, device_id=device_id)
                if stat:
                    break
                # 计算剩余时间
                expires_in = data
                logger.info("等待登录中，过期倒计时：{}", expires_in)
                # 更新状态，包含倒计时
                update_bot_status("waiting_login", f"等待微信扫码登录 (剩余{expires_in}秒)", {
                    "qrcode_url": url if 'url' in locals() else None,
                    "uuid": uuid,
                    "expires_in": expires_in,
                    "timestamp": time.time()
                })
                await asyncio.sleep(2)

        # 保存登录信息
        robot_stat["wxid"] = bot.wxid
        robot_stat["device_name"] = device_name
        robot_stat["device_id"] = device_id
        with open("resource/robot_stat.json", "w") as f:
            json.dump(robot_stat, f)

        # 获取登录账号信息
        bot.wxid = data.get("acctSectResp").get("userName")
        bot.nickname = data.get("acctSectResp").get("NickName")
        bot.alias = data.get("acctSectResp").get("Alais")
        bot.phone = data.get("acctSectResp").get("Mobile")
        # update_worker_success = await db.update_worker_db(bot.wxid, bot.nickname, bot.phone)
        logger.info("登录账号信息: wxid: {}  昵称: {}  微信号: {}  手机号: {}", bot.wxid, bot.nickname, bot.alias,
                    bot.phone)

        # 登录微信
        try:
            # 等待登录，获取个人信息
            # await bot.login() - 这个方法不存在
            # 直接使用之前获取的个人信息即可，因为在 check_login_uuid 成功后已经设置了 wxid
            # 登录成功后更新状态
            update_bot_status("online", f"已登录：{bot.nickname}", {
                "nickname": bot.nickname,
                "wxid": bot.wxid,
                "alias": bot.alias
            })
        except Exception as e:
            logger.error(f"登录失败: {e}")
            update_bot_status("error", f"登录失败: {str(e)}")
            return None

    else:  # 已登录
        bot.wxid = wxid
        profile = await bot.get_profile()

        bot.nickname = profile.get("userInfo").get("NickName").get("string")
        bot.alias = profile.get("userInfo").get("Alias")
        bot.phone = profile.get("userInfo").get("BindMobile").get("string")
        # 不需要使用头像图片URL

        logger.info("profile登录账号信息: wxid: {}  昵称: {}  微信号: {}  手机号: {}", bot.wxid, bot.nickname, bot.alias,
                    bot.phone)

    logger.info("登录设备信息: device_name: {}  device_id: {}", device_name, device_id)

    logger.success("登录成功")

    # 更新状态为在线
    update_bot_status("online", f"已登录：{bot.nickname}", {
        "nickname": bot.nickname,
        "wxid": bot.wxid,
        "alias": bot.alias
    })

    # 先初始化通知服务，再发送重连通知
    # 初始化通知服务
    notification_config = config.get("Notification", {})
    notification_service = init_notification_service(notification_config)
    logger.info(f"通知服务初始化完成，启用状态: {notification_service.enabled}")

    # 发送微信重连通知
    if notification_service and notification_service.enabled and notification_service.triggers.get("reconnect", False):
        if notification_service.token:
            logger.info(f"发送微信重连通知，微信ID: {bot.wxid}")
            asyncio.create_task(notification_service.send_reconnect_notification(bot.wxid))
        else:
            logger.warning("PushPlus Token未设置，无法发送重连通知")

    # ========== 登录完毕 开始初始化 ========== #

    # 开启自动心跳
    try:
        success = await bot.start_auto_heartbeat()
        if success:
            logger.success("已开启自动心跳")
        else:
            logger.warning("开启自动心跳失败")
    except ValueError:
        logger.warning("自动心跳已在运行")
    except Exception as e:
        logger.warning("自动心跳已在运行:{}",e)

    # 初始化机器人
    xybot = XYBot(bot)
    await xybot.update_profile(bot.wxid, bot.nickname, bot.alias, bot.phone)

    # 设置机器人实例到管理后台
    set_bot_instance(xybot)

    # 初始化数据库
    XYBotDB()

    message_db = MessageDB()
    await message_db.initialize()

    keyval_db = KeyvalDB()
    await keyval_db.initialize()

    # 通知服务已在前面初始化完成

    # 启动调度器
    scheduler.start()
    logger.success("定时任务已启动")

    # 添加图片文件自动清理任务
    try:
        from utils.files_cleanup import FilesCleanup

        # 获取清理天数配置
        cleanup_days = config.get("XYBot", {}).get("files-cleanup-days", 7)

        if cleanup_days > 0:
            # 创建清理任务
            cleanup_task = FilesCleanup.schedule_cleanup(config)

            # 添加到定时任务，每天执行一次
            scheduler.add_job(
                cleanup_task,
                'interval',
                hours=24,
                id='files_cleanup',
                next_run_time=datetime.now() + timedelta(minutes=5)  # 系统启动5分钟后执行第一次清理
            )
            logger.success(f"已添加图片文件自动清理任务，清理天数: {cleanup_days}天，每24小时执行一次")
        else:
            logger.info("图片文件自动清理功能已禁用 (files-cleanup-days = 0)")
    except Exception as e:
        logger.error(f"添加图片文件自动清理任务失败: {e}")

    # 加载插件目录下的所有插件
    loaded_plugins = await plugin_manager.load_plugins_from_directory(bot, load_disabled_plugin=False)
    logger.success(f"已加载插件: {loaded_plugins}")

    # ========== 开始接受消息 ========== #

    # （可选）如需处理堆积消息，可保留一次性拉取，否则可删除
    # logger.info("处理堆积消息中")
    # count = 0
    # while True:
    #     ok,data = await bot.sync_message()
    #     data = data.get("AddMsgs")
    #     if not data:
    #         if count > 2:
    #             break
    #         else:
    #             count += 1
    #             continue
    #     logger.debug("接受到 {} 条消息", len(data))
    #     logger.debug(f"sync_message返回: ok={ok}, data={data}")
    #     await asyncio.sleep(0.05)
    # logger.success("处理堆积消息完毕")

    # 更新状态为就绪
    update_bot_status("ready", "机器人已准备就绪")

    # 启动自动重启监控器
    try:
        from utils.auto_restart import start_auto_restart_monitor
        start_auto_restart_monitor()
        logger.success("自动重启监控器已启动")
    except Exception as e:
        logger.error(f"启动自动重启监控器失败: {e}")

    logger.success("开始处理消息")

    # 启动 WebSocket 消息监听
    # 添加详细调试输出
    logger.debug(f"配置文件路径: {script_dir / 'main_config.toml'}")
    logger.debug(f"WechatAPIServer 区块: {config.get('WechatAPIServer', {})}")

    # 尝试多种可能的键名格式获取 ws-url
    ws_url = None
    wechat_api_config = config.get('WechatAPIServer', {})
    
    # 检查各种可能的键名
    for key in ['ws-url', 'ws_url', 'wsUrl', 'ws_uri', 'ws-uri']:
        if key in wechat_api_config:
            ws_url = wechat_api_config[key]
            logger.debug(f"从配置中找到 {key}: {ws_url}")
            break
    
    # 检查 dataclass 配置对象
    if not ws_url and hasattr(app_config, 'wechat_api') and hasattr(app_config.wechat_api, 'ws_url'):
        ws_url = app_config.wechat_api.ws_url
        logger.debug(f"从 app_config.wechat_api.ws_url 读取: {ws_url}")

    # 仍未找到则设置默认值
    if not ws_url or not isinstance(ws_url, str):
        # 使用服务器地址和端口构造默认地址
        server_host = wechat_api_config.get('host')  # 从配置中获取主机地址
        # 尝试获取ws专用端口，如没有则使用普通API端口
        server_port = wechat_api_config.get('ws-port')
        if not server_port:
            server_port = wechat_api_config.get('port')
        ws_url = f"ws://{server_host}:{server_port}/ws"
        logger.warning(f"未在配置中找到有效的 ws-url，使用构造值: {ws_url}")

    # 获取 wxid 并拼接到 URL
    wxid = bot.wxid
    if not ws_url.rstrip("/").endswith(wxid):
        ws_url = ws_url.rstrip("/") + f"/{wxid}"
    
    logger.info(f"WebSocket 消息推送地址: {ws_url}")

    # 初始化 Redis 连接
    redis_url = f"redis://{api_config.get('redis-host', '127.0.0.1')}:{api_config.get('redis-port', 6379)}"
    redis = aioredis.from_url(redis_url, decode_responses=True)

    # 启动消息消费者
    for _ in range(NUM_CONSUMERS):
        asyncio.create_task(message_consumer(xybot, redis, message_db))

    # 选择消息读取方式
    message_mode = getattr(app_config.wechat_api, "message_mode", None) \
        or getattr(app_config.wechat_api, "messageMode", None) \
        or config.get("WechatAPIServer", {}).get("message-mode", "ws")
    logger.info(f"消息读取模式: {message_mode}")

    if message_mode and message_mode.lower() == "http":
        api_host = config.get("WechatAPIServer", {}).get("host", "127.0.0.1")
        api_port = config.get("WechatAPIServer", {}).get("port", 9011)
        wxid = bot.wxid
        await http_poll_messages(xybot, api_host, api_port, wxid, redis, message_db)
    else:
        await listen_ws_messages(xybot, ws_url, redis, message_db)

    # 返回机器人实例（此处不会执行到，因为上面的无限循环）
    return xybot

async def listen_ws_messages(xybot, ws_url, redis, message_db):
    """WebSocket 客户端，实时接收消息并处理，自动重连，依赖官方ping/pong心跳机制"""
    import traceback
    import websockets
    import asyncio
    import time
    reconnect_interval = 5  # 断开后重连间隔秒数
    reconnect_count = 0
    while True:
        try:
            if not ws_url.startswith("ws://") and not ws_url.startswith("wss://"):
                ws_url = "ws://" + ws_url
            logger.info(f"正在连接到 WebSocket 服务器: {ws_url}")
            async with websockets.connect(ws_url, ping_interval=30, ping_timeout=10) as websocket:
                logger.success(f"已连接到 WebSocket 消息服务器: {ws_url}")
                reconnect_count = 0  # 成功连接后重置重连计数
                while True:
                    try:
                        msg = await websocket.recv()
                        # 检查服务端主动关闭连接的业务消息
                        if isinstance(msg, str) and ("已关闭连接" in msg or "connection closed" in msg.lower()):
                            logger.warning("检测到服务端主动关闭连接消息，主动关闭本地ws，准备重连...")
                            await websocket.close()
                            break
                        try:
                            data = json.loads(msg)
                            if isinstance(data, dict) and "AddMsgs" in data:
                                messages = data["AddMsgs"]
                                for message in messages:
                                    # 本地存储
                                    await message_db.save_message(
                                        msg_id=message.get("MsgId") or message.get("msgId") or 0,
                                        new_msg_id=message.get("NewMsgId") or message.get("newMsgId") or 0,
                                        sender_wxid=message.get("FromUserName", {}).get("string", ""),
                                        from_wxid=message.get("ToUserName", {}).get("string", ""),
                                        msg_type=message.get("MsgType") or message.get("category") or 0,
                                        content=message.get("Content", {}).get("string", ""),
                                        is_group=False
                                    )
                                    # 入队
                                    await redis.rpush(QUEUE_NAME, json.dumps(message, ensure_ascii=False))
                                    logger.info(f"消息已入队到队列 {QUEUE_NAME}，消息ID: {message.get('MsgId') or message.get('msgId')}")
                            else:
                                ws_msg = data
                                ws_msgs = [ws_msg] if isinstance(ws_msg, dict) else ws_msg
                                for msg in ws_msgs:
                                    addmsg = {
                                        "MsgId": msg.get("msgId"),
                                        "FromUserName": {"string": msg.get("sender", {}).get("id", "")},
                                        "ToUserName": {"string": getattr(xybot.bot, "wxid", "")},
                                        "MsgType": msg.get("category", 1),
                                        "Content": {"string": msg.get("content", "")},
                                        "Status": 3,
                                        "ImgStatus": 1,
                                        "ImgBuf": {"iLen": 0},
                                        "CreateTime": int(time.mktime(time.strptime(msg.get("timestamp", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S"))) if msg.get("timestamp") else int(time.time()),
                                        "MsgSource": msg.get("msgSource", ""),
                                        "PushContent": msg.get("pushContent", ""),
                                        "NewMsgId": msg.get("newMsgId", msg.get("msgId")),
                                        "MsgSeq": msg.get("msgSeq", 0)
                                    }
                                    logger.info(f"ws消息适配为AddMsgs: {json.dumps(addmsg, ensure_ascii=False)}")
                                    # 本地存储
                                    await message_db.save_message(
                                        msg_id=addmsg.get("MsgId") or 0,
                                        new_msg_id=addmsg.get("NewMsgId") or 0,
                                        sender_wxid=addmsg.get("FromUserName", {}).get("string", ""),
                                        from_wxid=addmsg.get("ToUserName", {}).get("string", ""),
                                        msg_type=addmsg.get("MsgType") or 0,
                                        content=addmsg.get("Content", {}).get("string", ""),
                                        is_group=False
                                    )
                                    # 入队
                                    await redis.rpush(QUEUE_NAME, json.dumps(addmsg, ensure_ascii=False))
                                    logger.info(f"消息已入队到队列 {QUEUE_NAME}，消息ID: {addmsg.get('MsgId') or addmsg.get('msgId')}")
                        except json.JSONDecodeError:
                            msg_preview = msg[:100] + "..." if len(msg) > 100 else msg
                            if not msg.strip():
                                logger.debug("收到WebSocket心跳包或空消息")
                            else:
                                logger.info(f"收到非JSON格式的WebSocket消息: {msg_preview}")
                        except Exception as e:
                            logger.error(f"处理ws消息出错: {e}, 原始内容: {msg[:100]}...")
                    except websockets.exceptions.ConnectionClosed as e:
                        logger.error(f"WebSocket 连接已关闭: {e} (code={getattr(e, 'code', None)}, reason={getattr(e, 'reason', None)})，检测到断链，{reconnect_interval}秒后重连...")
                        break
                    except Exception as e:
                        logger.error(f"WebSocket消息主循环异常: {e}\n{traceback.format_exc()}，{reconnect_interval}秒后重连...")
                        break
        except Exception as e:
            reconnect_count += 1
            logger.error(f"WebSocket 连接失败: {type(e).__name__}: {e}，第{reconnect_count}次重连，{reconnect_interval}秒后重试...\n{traceback.format_exc()}")
            await asyncio.sleep(reconnect_interval)