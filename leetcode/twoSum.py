"""
@FileName：leetcode.py
@Description：
@Author：zhoujing
@contact：121531845@qq.com
@Time：2025/3/21 23:34
@Department：红石扩大小区
@Website：www.zhoujing.com
@Copyright：©2019-2025 GX信息科技有限公司
"""
class Solution(object):
    def twoSum(self, nums, target):
        """
        :type nums: List[int]
        :type target: int
        :rtype: List[int]
        """
        v2idx = {}
        for idx, v in enumerate(nums):
            v2idx[v] = idx
        for idx, v in enumerate(nums):
            if v in v2idx:
                return v2idx[v], idx

