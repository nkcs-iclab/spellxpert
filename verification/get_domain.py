import re


def get_domain(csc_output, char, corrections):
    """提取错字周围的领域词组"""
    # 领域词组长度
    if not corrections:
        n = 2
    elif max(len(element) for element in corrections) == 1:
        n = 1
    else:
        n = max(len(element) for element in corrections) - 1

    # 构建当前错字的标签部分正则表达式
    if len(char) > 1:
        wrong_tag = ''.join([f"<csc>{re.escape(c)}</csc>" for c in char])
    else:
        # 如果是单个字符，直接加上 <csc> 标签
        wrong_tag = f"<csc>{re.escape(char)}</csc>"

    # 过滤 csc_output，去掉除当前错字标签外的内容
    filtered_output = re.sub(
        r'(<csc>.*?</csc>)',
        lambda match: match.group(0) if any(f"<csc>{re.escape(c)}</csc>" == match.group(0) for c in char) else '',
        csc_output
    )
    # 找到错字标签的位置
    matches = re.finditer(wrong_tag, filtered_output)

    #  domain 默认值为空
    domain = ""

    for match in matches:
        # 获取错字标签的左右边界
        left_pos = match.start()
        right_pos = match.end()

        # 从左边界向左取n个字符
        left_context = filtered_output[max(0, left_pos - n):left_pos]

        # 从右边界向右取n个字符
        right_context = filtered_output[right_pos:right_pos + n]

        # 结合左侧和右侧字符，形成领域词组
        domain += left_context + right_context

    return domain
