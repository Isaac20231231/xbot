#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速性能监控测试
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from utils.config_manager import ConfigManager
from utils.performance_monitor import init_performance_monitor, performance_monitor
from loguru import logger

print("🚀 快速性能监控测试")
print("=" * 50)

try:
    # 1. 初始化配置
    print("🔧 初始化配置管理器...")
    config_manager = ConfigManager()
    app_config = config_manager.config
    
    # 2. 初始化性能监控
    print("📊 初始化性能监控器...")
    performance_config = {
        "enabled": True,
        "monitoring_interval": 5,  # 5秒间隔，快速测试
        "max_history_size": 100,
        "cpu_alert_threshold": 80,
        "memory_alert_threshold": 85,
        "memory_low_threshold_mb": 500,
    }
    monitor = init_performance_monitor(performance_config)
    
    # 3. 定义测试函数
    @performance_monitor("test_function")
    def test_cpu_task():
        """测试CPU任务"""
        print("🔄 执行CPU密集型任务...")
        total = sum(i * i for i in range(500000))
        time.sleep(0.1)
        print(f"✅ CPU任务完成，结果: {total}")
        return total
    
    @performance_monitor("test_memory_task")
    def test_memory_task():
        """测试内存任务"""
        print("🔄 执行内存密集型任务...")
        data = [f"data_{i}" * 100 for i in range(50000)]
        time.sleep(0.1)
        print(f"✅ 内存任务完成，数据量: {len(data)}")
        return len(data)
    
    # 4. 执行测试任务
    print("🎯 执行测试任务...")
    for i in range(3):
        print(f"  任务轮次 {i+1}")
        test_cpu_task()
        test_memory_task()
        time.sleep(0.5)
    
    # 5. 显示性能统计
    print("\n📊 === 性能统计结果 ===")
    
    # 函数性能统计
    func_stats = monitor.get_function_performance_summary()
    if func_stats:
        print("⚡ 函数性能统计:")
        for func_name, stats in func_stats.items():
            print(f"  🔧 {func_name}:")
            print(f"    - 调用次数: {stats['call_count']}")
            print(f"    - 平均耗时: {stats['avg_time_ms']}ms")
            print(f"    - 最短耗时: {stats['min_time_ms']}ms")
            print(f"    - 最长耗时: {stats['max_time_ms']}ms")
    
    # 记录自定义指标
    monitor.record_custom_metric("test_completed", 1, "test")
    monitor.record_custom_metric("test_duration", time.time(), "test")
    
    # 性能报告
    report = monitor.get_performance_report()
    print(f"\n📋 监控状态: {'启用' if report['monitor_status']['enabled'] else '禁用'}")
    print(f"📈 自定义指标数量: {report['custom_metrics_count']}")
    
    # 性能建议
    suggestions = monitor.get_performance_suggestions()
    if suggestions:
        print("\n💡 性能建议:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
    else:
        print("\n✅ 性能表现良好")
    
    print("\n✅ 测试完成！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("📝 说明：")
print("- 性能监控装饰器自动记录函数执行时间")
print("- 可以通过日志查看详细的性能数据")
print("- 支持自定义性能指标记录")
print("- 提供性能优化建议") 