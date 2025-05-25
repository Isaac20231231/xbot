#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控集成示例
展示如何在主程序中集成性能监控并在日志中显示数据
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from utils.config_manager import ConfigManager
from utils.performance_monitor import (
    init_performance_monitor, 
    start_performance_monitoring,
    get_performance_monitor,
    performance_monitor
)
from utils.logger_manager import init_logger_manager
from loguru import logger


class PerformanceReporter:
    """性能报告器 - 定期在日志中显示性能数据"""
    
    def __init__(self, interval: int = 60):
        self.interval = interval
        self.is_running = False
        self._task = None
    
    async def start(self):
        """启动性能报告"""
        if self.is_running:
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._report_loop())
        logger.info(f"📊 性能报告器已启动，报告间隔: {self.interval}秒")
    
    async def stop(self):
        """停止性能报告"""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("📊 性能报告器已停止")
    
    async def _report_loop(self):
        """报告循环"""
        while self.is_running:
            try:
                await asyncio.sleep(self.interval)
                await self.generate_performance_report()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"性能报告生成失败: {e}")
    
    async def generate_performance_report(self):
        """生成性能报告"""
        monitor = get_performance_monitor()
        if not monitor:
            return
        
        logger.info("📊 === 定期性能报告 ===")
        
        # 系统性能摘要
        system_summary = monitor.get_system_metrics_summary(minutes=10)
        if system_summary:
            logger.info("🖥️ 系统性能 (最近10分钟):")
            logger.info(f"  📈 CPU: 平均 {system_summary['cpu']['avg']:.1f}%, 峰值 {system_summary['cpu']['max']:.1f}%")
            logger.info(f"  🧠 内存: 平均 {system_summary['memory']['avg_percent']:.1f}%, 峰值 {system_summary['memory']['max_percent']:.1f}%")
            logger.info(f"  💾 内存使用: {system_summary['memory']['avg_used_mb']:.1f}MB")
        
        # 函数性能TOP5
        func_summary = monitor.get_function_performance_summary()
        if func_summary:
            # 按平均执行时间排序，取前5个
            sorted_funcs = sorted(
                func_summary.items(), 
                key=lambda x: x[1]['avg_time_ms'], 
                reverse=True
            )[:5]
            
            if sorted_funcs:
                logger.info("⚡ 函数性能TOP5 (按平均耗时):")
                for i, (func_name, stats) in enumerate(sorted_funcs, 1):
                    logger.info(f"  {i}. {func_name}: {stats['avg_time_ms']}ms (调用{stats['call_count']}次)")
        
        # 性能警告和建议
        suggestions = monitor.get_performance_suggestions()
        if suggestions:
            logger.warning("⚠️ 性能优化建议:")
            for suggestion in suggestions:
                logger.warning(f"  💡 {suggestion}")


# 模拟一些业务函数，添加性能监控
@performance_monitor("message_processor")
async def process_message(message_id: str, content: str):
    """模拟消息处理"""
    logger.info(f"处理消息 {message_id}: {content[:50]}...")
    
    # 模拟处理时间
    await asyncio.sleep(0.1 + len(content) * 0.001)
    
    # 模拟一些计算
    result = len(content) * 2
    
    logger.info(f"消息 {message_id} 处理完成")
    return result


@performance_monitor("database_query")
def query_database(query: str):
    """模拟数据库查询"""
    logger.debug(f"执行数据库查询: {query}")
    
    # 模拟查询时间
    time.sleep(0.05 + len(query) * 0.002)
    
    # 模拟返回结果
    result = [f"result_{i}" for i in range(10)]
    logger.debug(f"查询返回 {len(result)} 条记录")
    return result


@performance_monitor("api_request")
async def handle_api_request(endpoint: str, data: dict):
    """模拟API请求处理"""
    logger.info(f"处理API请求: {endpoint}")
    
    # 模拟处理
    await asyncio.sleep(0.2)
    
    # 模拟数据库查询
    query_result = await asyncio.to_thread(query_database, f"SELECT * FROM {endpoint}")
    
    logger.info(f"API请求 {endpoint} 处理完成")
    return {"status": "success", "data": query_result}


async def simulate_bot_workload():
    """模拟机器人工作负载"""
    logger.info("🤖 开始模拟机器人工作负载...")
    
    tasks = []
    
    # 模拟消息处理
    for i in range(5):
        message_content = f"这是第{i+1}条测试消息，包含一些内容用于测试性能监控功能。" * (i + 1)
        task = asyncio.create_task(process_message(f"msg_{i+1}", message_content))
        tasks.append(task)
    
    # 模拟API请求
    for endpoint in ["users", "groups", "messages"]:
        task = asyncio.create_task(handle_api_request(endpoint, {"test": "data"}))
        tasks.append(task)
    
    # 等待所有任务完成
    await asyncio.gather(*tasks)
    logger.info("🤖 工作负载模拟完成")


async def main():
    """主函数"""
    logger.info("🚀 性能监控集成演示")
    logger.info("=" * 60)
    
    try:
        # 1. 初始化配置
        logger.info("🔧 初始化系统...")
        config_manager = ConfigManager()
        app_config = config_manager.config
        
        # 2. 初始化日志管理器
        logger_config = {
            "log_level": app_config.admin.log_level,
            "enable_file_log": app_config.logging.enable_file_log,
            "enable_console_log": app_config.logging.enable_console_log,
            "enable_json_format": False,  # 演示时使用普通格式
            "max_log_files": app_config.logging.max_log_files,
            "log_rotation": app_config.logging.log_rotation,
        }
        logger_manager = init_logger_manager(logger_config)
        
        # 3. 初始化性能监控
        performance_config = {
            "enabled": app_config.performance.enabled,
            "monitoring_interval": 10,  # 10秒间隔，便于演示
            "max_history_size": app_config.performance.max_history_size,
            "cpu_alert_threshold": app_config.performance.cpu_alert_threshold,
            "memory_alert_threshold": app_config.performance.memory_alert_threshold,
            "memory_low_threshold_mb": app_config.performance.memory_low_threshold_mb,
        }
        performance_monitor = init_performance_monitor(performance_config)
        
        # 4. 启动性能监控
        await start_performance_monitoring()
        
        # 5. 启动性能报告器
        reporter = PerformanceReporter(interval=30)  # 30秒报告一次
        await reporter.start()
        
        logger.info("✅ 系统初始化完成")
        
        # 6. 模拟工作负载
        logger.info("🎯 开始模拟工作负载...")
        
        # 执行多轮工作负载
        for round_num in range(3):
            logger.info(f"📋 执行第 {round_num + 1} 轮工作负载")
            await simulate_bot_workload()
            
            # 每轮之间等待一段时间
            await asyncio.sleep(5)
        
        # 7. 等待一段时间让性能监控收集数据
        logger.info("⏳ 等待性能数据收集...")
        await asyncio.sleep(15)
        
        # 8. 生成最终性能报告
        logger.info("📊 === 最终性能报告 ===")
        await reporter.generate_performance_report()
        
        # 9. 显示详细统计
        monitor = get_performance_monitor()
        if monitor:
            report = monitor.get_performance_report()
            logger.info("📈 监控统计:")
            logger.info(f"  - 系统指标记录: {report['history_size']['system_metrics']} 条")
            logger.info(f"  - 自定义指标: {report['custom_metrics_count']} 条")
            logger.info(f"  - 监控状态: {'运行中' if report['monitor_status']['is_monitoring'] else '已停止'}")
        
        logger.info("✅ 演示完成！")
        
        # 10. 清理
        await reporter.stop()
        if monitor:
            await monitor.stop_monitoring()
        
    except Exception as e:
        logger.error(f"❌ 演示过程中出现错误: {e}")
        logger.exception("详细错误信息:")


if __name__ == "__main__":
    print("🚀 性能监控集成演示")
    print("这个演示将展示：")
    print("1. 如何在程序中集成性能监控")
    print("2. 如何在日志中显示性能数据")
    print("3. 如何使用性能监控装饰器")
    print("4. 如何生成定期性能报告")
    print("=" * 60)
    
    asyncio.run(main()) 