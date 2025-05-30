import re
from get_domain import get_domain

def get_corrections(think, wrong_chars, output):
    """为每个错字匹配改正字、原始文本、判断是否需要删除"""
    # 定义关键词（删除关键字优先检查）
    remove_keywords = ["是多余的", "应去掉", "应该去掉", "需要去掉", "应删除"]
    modify_keywords = ["应该是", "应该为", "应该用", "应该改为", "应改为", "应为"]

    # 处理think文本：删除</think>标签往前数第二个句号后的所有内容
    think = process_think_text(think)

    # 查找所有中文引号对（支持中文和英文引号）
    quote_matches = list(re.finditer(r'["“](.*?)[”"]', think))

    # 为每个错字查找可能的改正字
    for char in wrong_chars:
        corrections = []
        texts = []
        seen_corrections = set()  # 用于记录已经见过的改正字
        remove = 0

        # 遍历所有引号对
        for i in range(len(quote_matches) - 1):
            first_quote = quote_matches[i].group(1)  # 前引号内容
            second_quote = quote_matches[i + 1].group(1)  # 后引号内容

            # 检查前引号是否包含当前错字且两引号间字数<=30
            if char in first_quote and (quote_matches[i + 1].start() - quote_matches[i].end()) <= 30:
                between_text = think[quote_matches[i].end():quote_matches[i + 1].start()]

                # 优先检查删除关键字
                if any(keyword in between_text for keyword in remove_keywords):
                    remove = 1
                    corrections = []
                    texts = [f'“{first_quote}”{between_text}“{second_quote}”']
                    break  # 发现删除标记，立即终止当前错字的处理

                # 然后检查修改关键字（只有没有删除标记时才检查）
                if not remove and any(keyword in between_text for keyword in modify_keywords):
                    # 获取改正字
                    correction = second_quote
                    # 如果改正字未出现过，则添加到结果中
                    if correction not in seen_corrections:
                        seen_corrections.add(correction)
                        corrections.append(correction)

                        texts.append(f'“{first_quote}”{between_text}“{second_quote}”')

        # 更新错字字典
        wrong_chars[char]['corrections'] = corrections
        current_domain = get_domain(output, char, corrections)
        simplified = ["".join([c for c in correction if c not in current_domain]) for correction in corrections]
        wrong_chars[char]['simplified'] = simplified
        wrong_chars[char]['domain'] = current_domain
        wrong_chars[char]['text'] = texts
        wrong_chars[char]['remove'] = remove

    return wrong_chars


def process_think_text(think):
    """处理think文本，删除</think>前第二个句号后的内容"""
    end_tag_pos = think.find('</think>')
    if end_tag_pos == -1:
        return think

    # 查找倒数第二个句号
    periods = [m.start() for m in re.finditer(r'[。.]', think[:end_tag_pos])]
    if len(periods) >= 2:
        return think[:periods[-2] + 1]
    return think