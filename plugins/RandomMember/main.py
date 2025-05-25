import random
import tomllib

from WechatAPI import WechatAPIClient
from utils.decorators import *
from utils.plugin_base import PluginBase


class RandomMember(PluginBase):
    description = "随机群成员"
    author = "HenryXiaoYang"
    version = "1.0.0"

    def __init__(self):
        super().__init__()

        with open("plugins/RandomMember/config.toml", "rb") as f:
            plugin_config = tomllib.load(f)

        config = plugin_config["RandomMember"]

        self.enable = config["enable"]
        self.command = config["command"]
        self.count = config["count"]

    @on_text_message
    async def handle_text(self, bot: WechatAPIClient, message: dict):
        from loguru import logger
        logger.info(f"RandomMember 插件收到消息: {message.get('Content')}")

        if not self.enable:
            logger.info("RandomMember 插件未启用")
            return

        content = str(message["Content"]).strip()
        command = content.split(" ")

        logger.info(f"RandomMember 解析命令: {command[0]}, 配置的命令: {self.command}")

        if command[0] not in self.command:
            logger.info(f"RandomMember 命令不匹配: {command[0]} 不在 {self.command} 中")
            return

        logger.info(f"RandomMember 命令匹配成功: {command[0]}")

        if not message["IsGroup"]:
            logger.info("RandomMember 不是群聊消息，拒绝处理")
            await bot.send_text_message(message["FromWxid"], "-----XYBot-----\n😠只能在群里使用！")
            return

        logger.info(f"RandomMember 开始获取群成员列表: {message['FromWxid']}")
        try:
            # 尝试直接使用API调用获取群成员列表
            import aiohttp
            import json

            # 构造请求参数
            json_param = {"QID": message["FromWxid"], "Wxid": bot.wxid}

            # 确定API基础路径
            api_base = f"http://{bot.ip}:{bot.port}"

            # 根据协议版本选择正确的API前缀
            # 849协议使用/VXAPI前缀，其他协议使用/api前缀
            # 从日志中看到使用的是849协议
            api_prefix = "/VXAPI"

            logger.info(f"RandomMember 使用API {api_base}{api_prefix}/Group/GetChatRoomMemberDetail 获取群成员")

            async with aiohttp.ClientSession() as session:
                response = await session.post(
                    f"{api_base}{api_prefix}/Group/GetChatRoomMemberDetail",
                    json=json_param,
                    headers={"Content-Type": "application/json"}
                )

                # 检查响应状态
                if response.status != 200:
                    logger.error(f"RandomMember API请求失败: HTTP状态码 {response.status}")
                    await bot.send_at_message(message["FromWxid"], "\n-----XYBot-----\n😢获取群成员列表失败，请联系管理员", [message["SenderWxid"]])
                    return False

                # 解析响应数据
                json_resp = await response.json()
                logger.info(f"RandomMember 收到API响应: {json.dumps(json_resp)[:200]}...")

                if not json_resp.get("Success"):
                    logger.error(f"RandomMember API请求失败: {json_resp.get('Message', '未知错误')}")
                    await bot.send_at_message(message["FromWxid"], "\n-----XYBot-----\n😢获取群成员列表失败，请联系管理员", [message["SenderWxid"]])
                    return False

                # 提取群成员列表
                data = json_resp.get("Data", {})
                new_chatroom_data = data.get("NewChatroomData", {})
                memlist = new_chatroom_data.get("ChatRoomMember", [])

                logger.info(f"RandomMember 获取到 {len(memlist)} 个群成员")

                # 检查返回的数据结构
                if not memlist or len(memlist) == 0:
                    logger.error(f"RandomMember 获取群成员列表为空")
                    await bot.send_at_message(message["FromWxid"], "\n-----XYBot-----\n😢获取群成员列表为空，请联系管理员", [message["SenderWxid"]])
                    return False

                # 检查第一个成员的数据结构
                first_member = memlist[0]
                logger.info(f"RandomMember 第一个成员数据结构: {first_member}")

                # 确保每个成员都有NickName字段
                for i, member in enumerate(memlist):
                    if 'NickName' not in member and 'DisplayName' in member:
                        member['NickName'] = member['DisplayName']
                    elif 'NickName' not in member and 'UserName' in member:
                        member['NickName'] = member['UserName']
                    elif 'NickName' not in member:
                        member['NickName'] = f"群成员{i+1}"

        except Exception as e:
            logger.error(f"RandomMember 获取群成员失败: {e}")
            # 发送错误消息
            await bot.send_at_message(message["FromWxid"], "\n-----XYBot-----\n😢获取群成员列表失败，请联系管理员", [message["SenderWxid"]])
            return False

        if len(memlist) < self.count:
            logger.warning(f"RandomMember 群成员数量 {len(memlist)} 小于配置的随机数量 {self.count}，调整为群成员数量")
            random_count = len(memlist)
        else:
            random_count = self.count

        random_members = random.sample(memlist, random_count)
        logger.info(f"RandomMember 随机选择了 {len(random_members)} 个成员")

        output = "\n-----xxxbot-----\n👋嘿嘿，我随机选到了这几位："
        for member in random_members:
            output += f"\n✨{member['NickName']}"

        logger.info(f"RandomMember 发送结果消息: {output}")
        await bot.send_at_message(message["FromWxid"], output, [message["SenderWxid"]])
        logger.info("RandomMember 处理完成")

        # 返回 False 表示已处理消息，阻止其他插件处理
        return False
