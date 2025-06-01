"""
@FileName：big.py
@Description：
@Author：zhoujing
@contact：121531845@qq.com
@Time：2025/3/22 10:11
@Department：红石扩大小区
@Website：www.zhoujing.com
@Copyright：©2019-2025 GX信息科技有限公司
"""
def find(data: list, target: int):
    """
    样例:
        输入：data=[1, 2, 5, 7, 11, 44] target=11 输出 44
    """
    left = 0
    right = len(data)
    while left <= right:
        mid = (left + right) // 2
        if data[mid] == target:
            return mid
        if data[mid] > target:
            right = mid - 1
        elif data[mid] < target:
            left = mid + 1



if __name__ == '__main__':
    my_data = [1, 2, 3]
    t = 67
    for d in my_data:
        print(my_data.index(d))
        print(find(my_data, d))
        print('*' *  10)
