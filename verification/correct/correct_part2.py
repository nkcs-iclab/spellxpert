import json
import re

file_path = "extract.json"

# 读取json文件
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 匹配连续两个及以上<csc>...</csc>的错字段
pattern = re.compile(r"((<csc>.{1}</csc>){2,})")

def extract_csc_words(tagged_text):
    """提取连续<csc>标签内的错字，返回列表"""
    return re.findall(r"<csc>(.*?)</csc>", tagged_text)

for idx, item in enumerate(data):
    output_text = item.get("output", "")
    final_corrections = item.get("final_corrections", {})
    correct_characters = item.get("correct_characters", {})

    matches = list(pattern.finditer(output_text))
    if not matches:
        continue  # 无连续错字，跳过

    replacement_map = {}

    for match in matches:
        full_tagged_str = match.group(1)
        wrong_words = extract_csc_words(full_tagged_str)
        n = len(wrong_words)
        if n < 2:
            continue  # 不处理少于2个连续错字

        correction_lists = []
        for w in wrong_words:
            corrs = correct_characters.get(w)
            correction_lists.append(set(corrs))

        # print(f"idx={idx}, 连续错字词组='{''.join(wrong_words)}', common_phrases='{correction_lists}'")

        # 交集筛选长度为n的改正词组
        common_phrases = set.intersection(*correction_lists)
        common_phrases = {p for p in common_phrases if len(p) == n}

        if common_phrases:
            correct_phrase = list(common_phrases)[0]

            print(f"idx={idx+1}, 连续错字词组='{''.join(wrong_words)}', 最终改正词组='{correct_phrase}'")

            # 更新final_corrections中相关错字改正字为共同改正词组
            for w in wrong_words:
                final_corrections[w] = [correct_phrase]

            replacement_map[full_tagged_str] = correct_phrase

    # 替换连续错字标签为共同改正词组
    new_correct = output_text
    for wrong_phrase_tagged, correct_phrase in replacement_map.items():
        new_correct = new_correct.replace(wrong_phrase_tagged, correct_phrase)

    # 替换剩余非连续单个错字<csc>...</csc>
    single_wrong_pattern = re.compile(r"<csc>(.*?)</csc>")
    singles = single_wrong_pattern.findall(new_correct)

    for single_wrong in singles:
        corr_list = final_corrections.get(single_wrong)

        if corr_list is None:
            # 无改正字，去标签保留原错字
            replacement = single_wrong
        elif isinstance(corr_list, list):
            if not corr_list or corr_list[0] == "No corrections":
                replacement = single_wrong
            else:
                replacement = corr_list[0]
        else:
            # 如果是字符串类型
            if corr_list == "No corrections":
                replacement = single_wrong
            else:
                replacement = corr_list

        new_correct = new_correct.replace(f"<csc>{single_wrong}</csc>", replacement)

    # 更新json字段
    item["final_corrections"] = final_corrections
    item["correct"] = new_correct

# 保存修改结果
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("连续错字处理完成，文件已保存。")
