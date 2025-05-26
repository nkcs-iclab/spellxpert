import json

# 读取原始JSONL文件
input_file_path = "extract-output-FP-TP.jsonl"
output_file_path = "extract.json"

# 初始化一个空列表用于存储最终结果
result = []

# 读取JSONL文件并处理每一行
with open(input_file_path, "r", encoding="utf-8") as file:
    '''
    # 跳过前100行
    for _ in range(100):
        next(file)
    

    # 处理从第101行开始的300行
    for idx, line in enumerate(file, start=101):  # 从第101行开始，保持连续的 idx 编号
        if idx > 400:
            break  # 只处理第101到第400行的数据
    '''

    for idx, line in enumerate(file, start=1):
        # 解析JSON行
        record = json.loads(line)
        # 提取待检查的句子
        prompt = record.get("prompt", "")
        input_start = prompt.find("待检查的句子：") + len("待检查的句子：")
        input_end = prompt.find("<｜Assistant｜>")
        input_text = prompt[input_start:input_end].strip()

        # 提取think (即predict字段的全部内容)
        think_text = record.get("predict", "")

        # 提取output (即predict字段中"\n</think>\n\n"后面的部分)
        output_start = think_text.find("\n</think>\n\n")
        if output_start != -1:
            output_text = think_text[output_start + len("\n</think>\n\n"):].strip()
        else:
            output_text = ""  # 如果没有找到"\n</think>\n\n"，则output为空

        # 创建记录
        result.append({
            "idx": idx,
            "input": input_text,
            "output": output_text,
            "think": think_text
        })

# 将结果保存为新的JSON文件
with open(output_file_path, "w", encoding="utf-8") as output_file:
    json.dump(result, output_file, ensure_ascii=False, indent=4)

print(f"数据已成功提取并保存为 {output_file_path}")
