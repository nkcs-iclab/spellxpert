import re


def get_output(output, wrong_chars):

    # 首先处理连续错字（长度>1的错字词组）
    output = process_continuous_phrases(output, wrong_chars)
    # 然后处理单个错字（长度=1的错字）
    output = process_single_chars(output, wrong_chars)

    return output, wrong_chars  # 返回改正后的句子和更新后的wrong_chars


def process_continuous_phrases(output, wrong_chars):
    """处理连续错字词组（长度>1）"""
    for phrase, info in wrong_chars.items():
        if len(phrase) > 1:  # 连续错字词组
            # 初始化final_correction
            info['final_correction'] = None
            simplified = info.get('simplified', [])
            # 构造带标签的原始错字序列
            tagged_phrase = ''.join([f'<csc>{char}</csc>' for char in phrase])

            if info.get('remove', 0) == 1:
                output = output.replace(tagged_phrase, '')
            elif simplified:
                final_correction = simplified[0]
                info['final_correction'] = simplified[0]
                # 替换整个错字序列
                output = output.replace(tagged_phrase, final_correction)
            else:
                info['final_correction'] = "No matching correction"
                output = output.replace(tagged_phrase, phrase)

    return output

def get_multi_correction(corrections, char, output):
    """获取备选多字改正词"""
    multi_chars = [c for c in corrections if len(c) > 1]
    if multi_chars:
        multi_correction = next((mc for mc in multi_chars if char in mc), multi_chars[0])
        start_index = output.find(f'<csc>{char}</csc>')
        left_char = output[start_index - 1] if start_index > 0 else ''  # 左边界字符，若越界则为空
        right_char = output[start_index + len(f'<csc>{char}</csc>') + 1] if start_index + len(f'<csc>{char}</csc>') + 1 < len(output) else ''  # 右边界字符，若越界则为空
        if multi_correction[0] == left_char:
            multi_correction = multi_correction[1:]  # 删除最左边的字符
        if multi_correction[-1] == right_char:
            multi_correction = multi_correction[:-1]  # 删除最右边的字符
    else:
        multi_correction = "No matching correction"
    return multi_correction

def process_single_chars(output, wrong_chars):
    """处理单个错字（长度=1）"""
    for char, info in wrong_chars.items():
        if len(char) == 1:  # 单个错字
            # 初始化final_correction
            info['final_correction'] = "No matching correction"

            # 处理需要删除的错字
            if info.get('remove', 0) == 1:
                info['final_correction'] = 'removed'
                output = output.replace(f'<csc>{char}</csc>', '')
                continue

            # 处理需要改正的错字
            corrections = info.get('corrections', [])
            simplified = info.get('simplified', [])
            domain_phrase = info.get('domain_phrase', '')
            # single_chars = [c for c in simplified if len(c) == 1]
            # multi_correction = get_multi_correction(simplified, char, output)

            # 合并单字和单字组合词
            merged_simplified = [
                elem for i, elem in enumerate(simplified)
                if not any(
                    elem in other and elem != other
                    for j, other in enumerate(simplified)
                    if i != j
                )
            ]
            single_chars = [c for c in merged_simplified if len(c) == 1]
            multi_correction = get_multi_correction(simplified, char, output)

            # 找出最佳改正字
            if simplified and all(s == '' for s in simplified):
                final_correction = ''
            elif not single_chars:
                final_correction = multi_correction
            else:
                filtered_chars = [c for c in single_chars if c != char]
                if filtered_chars:
                    # 找被所有改正字包含的单字符
                    common_substrings = [sc for sc in filtered_chars if all(sc in c for c in simplified)]
                    if common_substrings:
                        final_correction = common_substrings[0]
                    else:
                        # 找不属于邻域词组的单字符
                        non_domain_chars = [c for c in filtered_chars if c not in domain_phrase]
                        final_correction = non_domain_chars[0] if non_domain_chars else filtered_chars[0]
                else:
                    final_correction = char

            # 如果出现自己改成自己的情况且有多字候选词
            if final_correction == char and len(multi_correction)<5:
                final_correction = multi_correction

            # 更新final_correction字段
            info['final_correction'] = final_correction

            # 替换output
            if final_correction == "No matching correction":
                output = output.replace(f'<csc>{char}</csc>', char)
            else:
                output = output.replace(f'<csc>{char}</csc>', final_correction)

    return output
