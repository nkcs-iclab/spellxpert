import re


def get_wrong_characters(output):
    """提取错字及其近邻错字数"""
    wrong_chars = {}

    # 第一步：查找连续的错字
    pattern = re.compile(r"((<csc>.{1}</csc>){2,})")
    matches = list(pattern.finditer(output))

    for match in matches:
        # 获取整个连续匹配的文本
        continuous_part = match.group(1)
        words = re.sub(r'</?csc>', '', continuous_part)
        # 提取所有错字
        chars = re.findall(r'<csc>(.{1})</csc>', continuous_part)

        continuity = len(chars)

        # 添加到字典
        for char in chars:
            # wrong_chars[words] = {'continuity': continuity}
            wrong_chars[words] = {}

    # 第二步：从原始输出中移除已处理的连续错字部分
    modified_output = pattern.sub('', output)

    # 第三步：查找独立的错字
    single_matches = re.findall(r'<csc>(.{1})</csc>', modified_output)
    for char in single_matches:
        # wrong_chars[char] = {'continuity': 1}
        wrong_chars[char] = {}

    return wrong_chars