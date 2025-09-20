#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import random

def simulate_training():
    total = 200
    for i in range(total + 1):
        # 模拟训练进度
        percent = (i / total) * 100
        
        # 创建进度条
        bar_length = 30
        filled_length = int(bar_length * i // total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # 创建其他训练信息
        elapsed_time = i // 2
        remaining_time = (total - i) // 2
        speed = random.uniform(1.8, 2.2)
        
        # 格式化输出
        output = f"{percent:3.0f}%|{bar}| {i}/{total} [{elapsed_time:02d}:{i%60:02d}<{remaining_time:02d}:{(remaining_time*60)%60:02d}, {speed:.2f}it/s]"
        
        # 输出到终端
        sys.stdout.write('\r' + output)
        sys.stdout.flush()
        
        # 模拟训练时间
        time.sleep(0.1)
        
        # 每10步输出一些日志信息
        if i % 10 == 0:
            print()  # 换行
            print(f"Step {i}: Training loss = {random.uniform(0.1, 1.0):.4f}")
            print(f"Step {i}: Validation accuracy = {random.uniform(0.8, 0.95):.4f}")

    print("\nTraining completed!")

if __name__ == "__main__":
    simulate_training()
