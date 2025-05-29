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

            # 在simplified中找长度匹配的改正词
            simplified = info.get('simplified', [])
            matching_corrections = [corr for corr in simplified if len(corr) == len(phrase)]

            if matching_corrections:
                final_correction = matching_corrections[0]
                info['final_correction'] = final_correction

                # 构造带标签的原始错字序列
                tagged_phrase = ''.join([f'<csc>{char}</csc>' for char in phrase])

                # 替换整个错字序列
                output = output.replace(tagged_phrase, final_correction)
            else:
                info['final_correction'] = "No matching correction"
                output = output.replace(tagged_phrase, phrase)

    return output


def process_single_chars(output, wrong_chars):
    """处理单个错字（长度=1）"""
    for char, info in wrong_chars.items():
        if len(char) == 1:  # 单个错字
            # 初始化final_correction
            info['final_correction'] = None

            # 处理需要删除的错字
            if info.get('remove', 0) == 1:
                info['final_correction'] = 'removed'
                output = output.replace(f'<csc>{char}</csc>', '')
                continue

            # 处理需要改正的错字
            simplified = info.get('simplified', [])
            single_chars = [c for c in simplified if len(c) == 1]
            corrections = info.get('corrections', [])
            domain_phrase = info.get('domain_phrase', '')

            # 找出最佳改正字
            final_correction = None
            if not single_chars:
                final_correction = "No single char correction"
                output = re.sub(r'</?csc>', '', output)
            else:
                # 找被所有改正字包含的单字符
                common_substrings = [sc for sc in single_chars if all(sc in c for c in corrections)]
                if common_substrings:
                    final_correction = common_substrings[0]
                else:
                    # 找不属于邻域词组的单字符
                    non_domain_chars = [c for c in single_chars if c not in domain_phrase]
                    final_correction = non_domain_chars[0] if non_domain_chars else single_chars[0]

            # 更新final_correction字段
            info['final_correction'] = final_correction

            # 执行替换（如果有效改正字）
            if isinstance(final_correction, str) and len(final_correction) == 1:
                output = output.replace(f'<csc>{char}</csc>', final_correction)

    return output