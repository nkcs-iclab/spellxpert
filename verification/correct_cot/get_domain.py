import re


def get_domain(csc_output, wrong_chars):
    """提取错字周围的领域词组"""
    domain_phrases = {}

    # 遍历错字字典
    for char, info in wrong_chars.items():

        # 领域词组长度
        n = 2

        # 构建当前错字的标签部分正则表达式
        if len(char) > 1:
            wrong_tag = ''.join([f"<csc>{re.escape(c)}</csc>" for c in char])
        else:
            # 如果是单个字符，直接加上 <csc> 标签
            wrong_tag = f"<csc>{re.escape(char)}</csc>"

        # 过滤 csc_output，去掉除当前错字标签外的内容
        filtered_output = re.sub(r'(<csc>.*?</csc>)', lambda match: match.group(0) if wrong_tag in match.group(0) else '', csc_output)

        # 找到错字标签的位置
        match = re.search(wrong_tag, filtered_output)

        if match:
            # 获取错字标签的左右边界
            left_pos = match.start()
            right_pos = match.end()

            # 从左边界向左取n个字符
            left_context = filtered_output[max(0, left_pos - n):left_pos]

            # 从右边界向右取n个字符
            right_context = filtered_output[right_pos:right_pos + n]

            # 结合左侧和右侧字符，形成领域词组
            domain = left_context + right_context

            # 将领域词组添加到字典中，更新'wrong_chars'中的'domain'字段
            domain_phrases[char] = domain

    return domain_phrases
