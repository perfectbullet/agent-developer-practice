"""
@FileName：fib.py
@Description：
@Author：zhoujing
@contact：121531845@qq.com
@Time：2025/3/22 0:19
@Department：红石扩大小区
@Website：www.zhoujing.com
@Copyright：©2019-2025 GX信息科技有限公司
"""

n = 10
nums = [1]
def fib(n):
    a, b = 1,  1
    for i in range(n - 1):
        a, b = b, a + b
        nums.append(a)
    return nums

print(fib(n))
