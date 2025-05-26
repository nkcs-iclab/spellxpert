import json
import re

# 文件路径
file_path = "extract.json"

# 正则表达式：匹配output中被<csc>标签包裹的错别字（单个字符）
csc_pattern = re.compile(r"<csc>(.*?)</csc>")

# 用于定位改正字的关键词列表
keywords = ["应该是", "应该为", "应该用", "应该改为", "应改为", "应为"]

# 判断错字是否“需要删除”的关键词列表
remove_keywords = ["是多余的", "应去掉", "应该去掉", "需要去掉", "应删除"]


def check_remove(think_text, pos):
    """
    判断错字在think文本中某位置后10个字符内
    是否包含删除关键词，若包含则返回True（需要删除）
    """
    check_range = think_text[pos:pos + 20]
    return any(kw in check_range for kw in remove_keywords)


def refine_correction(output_text, error_char, correction_list):
    """
    对提取的改正字做精简：
    - 如果改正字长度 > 1，取output中<csc>错字</csc>左右各n-1字符为邻域词组
    - 剔除改正字中包含的邻域词组字符，避免替换时重复内容
    - 返回去重后的精简改正字列表
    """
    refined = []
    neighborhoods = set()

    for corr in correction_list:
        if len(corr) == 1:
            # 单字符不处理，直接加入
            refined.append(corr)
        else:
            n = len(corr)
            idx = output_text.find(f"<csc>{error_char}</csc>")
            if idx == -1:
                # 找不到错字标签位置，直接加入
                refined.append(corr)
                continue
            left = max(0, idx - (n - 1))
            right = idx + len(f"<csc>{error_char}</csc>") + (n - 1)
            # 邻域词组，错字左右各n-1字符组成
            neighborhood = output_text[left:idx] + output_text[idx + len(f"<csc>{error_char}</csc>"):right]
            neighborhoods.update(neighborhood)  # 收集领域词组字符
            # 剔除改正字中邻域词组字符
            new_corr = ''.join(ch for ch in corr if ch not in neighborhood)
            refined.append(new_corr if new_corr else corr)
    return list(set(refined)), neighborhoods  # 去重返回


# 读取JSON数据
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 逐条处理数据记录
for record in data:
    output = record.get("output", "")
    think_raw = record.get("think", "")

    # 提取所有被<csc>包裹的错字（单字）
    errors = csc_pattern.findall(output)

    # 处理think文本，截断</think>标签及其后最后一句话及之后的内容
    cut_pos = think_raw.find("</think>")
    if cut_pos != -1:
        pre_think = think_raw[:cut_pos]
        period_positions = [m.start() for m in re.finditer(r"。", pre_think)]
        if len(period_positions) >= 2:
            trim_start = period_positions[-2] + 1
            think = think_raw[:trim_start]
        elif len(period_positions) == 1:
            think = think_raw[:period_positions[0] + 1]
        else:
            think = pre_think
    else:
        think = think_raw

    corrections = {}  # 存放错字对应改正字集合
    corrections_original = {} # 存放原始改正字
    remove_flags = {}  # 存放错字是否需要删除标志
    final_corrections = {} #存放最终确定的改正字
    neighborhoods = {} #存放领域词组

    # 找出think中所有成对的中文引号“...”
    quote_matches = list(re.finditer(r'“(.*?)”', think))

    for error in errors:
        remove_flags[error] = 0  # 默认不删除
        # 找错字引号位置，判断是否需要删除
        for m in quote_matches:
            if error in m.group(1):
                pos = m.end()
                if check_remove(think, pos):
                    remove_flags[error] = 1  # 标记删除

        correction_set = set()
        # 遍历成对引号，判断错字改正字关系
        for i in range(len(quote_matches) - 1):
            current_text = quote_matches[i].group(1)
            if error in current_text:
                start = quote_matches[i].end()
                end = quote_matches[i + 1].start()
                in_between = think[start:end]
                next_text = quote_matches[i + 1].group(1)
                # 判断两个引号间文本是否含关键词且不长于30字符
                if len(in_between) <= 30 and any(kw in in_between for kw in keywords):
                    correction_set.add(next_text)

        # 精简改正字（去重并剔除邻域重复字）
        corrections_original[error] = list(correction_set)
        correction_set, neighborhood_set = refine_correction(output, error, correction_set)
        neighborhoods[error] = neighborhood_set
        correction_set = set(correction_set)
        corrections[error] = list(correction_set)

    # 基于remove_flags处理output，先删除标记删除的错字标签
    correct_text = output
    for err in errors:
        final_corrections[err] = "No corrections"

        if remove_flags.get(err, 0) == 1:
            final_corrections[err] = "remove"
            correct_text = re.sub(f"<csc>{re.escape(err)}</csc>", "", correct_text)
            continue

        # 精简后的改正字集合
        corrs = corrections.get(err, [])
        # 领域词组字符集合
        neighborhood_chars = neighborhoods.get(err, set())

        # 单字符改正字
        single_chars = [c for c in corrs if len(c) == 1]

        selected_char = None
        for sc in single_chars:
            # 判断单字符是否被所有其他改正字包含
            if all((sc in w) for w in corrs if w != sc):
                selected_char = sc
                break

        if selected_char:
            final_corrections[err] = selected_char
            correct_text = re.sub(f"<csc>{re.escape(err)}</csc>", selected_char, correct_text)
        else:
            # 不满足包含条件，选非领域词单字随机一个
            non_domain_chars = [c for c in single_chars if c not in neighborhood_chars]
            if non_domain_chars:
                selected_char = non_domain_chars[0]
                final_corrections[err] = selected_char
                correct_text = re.sub(f"<csc>{re.escape(err)}</csc>", selected_char, correct_text)
            elif single_chars:
                selected_char = single_chars[0]
                final_corrections[err] = selected_char
                correct_text = re.sub(f"<csc>{re.escape(err)}</csc>", selected_char, correct_text)
            else:
                selected_char = "No corrections"


    # 保存结果
    record["correct"] = correct_text  # 最终修改后的句子
    record["final_corrections"] = final_corrections  # 最终改正字
    record["correct_characters"] = corrections_original  # 错字对应改正字集合
    record["remove_flags"] = remove_flags  # 错字是否删除标志


# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
