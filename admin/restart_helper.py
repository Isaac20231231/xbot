#!/usr/bin/env python
import os
import sys
import time
import subprocess

# �ȴ�ԭ���̽���
time.sleep(2)

# ����������
cmd = ["C:\Program Files\Python311\python.exe", "G:\xxxbot\849xxxbot\�±��ݣ�\xxxbot\main.py"]
print("ִ����������:", " ".join(cmd))
subprocess.Popen(cmd, cwd="G:\xxxbot\849xxxbot\�±��ݣ�\xxxbot", shell=False)

# ɾ������
try:
    os.remove(__file__)
except:
    pass
