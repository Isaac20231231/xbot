#!/usr/bin/env python
import os
import sys
import time
import subprocess

# 等待原进程结束
time.sleep(2)

# 重启主程序
cmd = ["C:\Program Files\Python311\python.exe", "G:\xxxbot\849xxxbot\新备份！\xxxbot\main.py"]
print("执行重启命令:", " ".join(cmd))
subprocess.Popen(cmd, cwd="G:\xxxbot\849xxxbot\新备份！\xxxbot", shell=False)

# 删除自身
try:
    os.remove(__file__)
except:
    pass
