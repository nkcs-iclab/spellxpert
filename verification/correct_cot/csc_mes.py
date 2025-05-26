import json
import re
from get_wrong_chars import get_wrong_characters
from get_corrections import get_corrections
from get_domain import get_domain
from get_output import get_output


def process_json_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    results = []
    for record in data:
        # 获取当前记录的input、output和think字段
        csc_input = record['input']
        csc_output = record['output']
        csc_think = record.get('think', '')

        # 1. 提取错字及其邻错字数
        wrong_chars = get_wrong_characters(csc_output)
        # 2. 提取领域词组
        domain_phrases = get_domain(csc_output, wrong_chars)
        # 3. 提取改正字与删除标识
        wrong_chars = get_corrections(csc_think, wrong_chars, domain_phrases)
        # 4. 获取最终改正字和改正后的句子
        corrected_output, wrong_chars = get_output(csc_output, wrong_chars)

        # 构建结果记录
        result_record = {
            'csc_input': csc_input,
            'csc_output': csc_output,
            'csc_think': csc_think,
            'correct': corrected_output,
            'wrong_chars': wrong_chars
        }
        results.append(result_record)

    # 保存结果到新的JSON文件
    with open(output_file, 'w', encoding='utf-8') as out_file:
        json.dump(results, out_file, ensure_ascii=False, indent=2)

    return results


# 文件路径
input_file_path = 'extract_test.json'
output_file_path = 'csc_mes.json'

# 处理文件并保存结果
results = process_json_file(input_file_path, output_file_path)

# 打印部分结果预览
print(f"处理完成，共处理 {len(results)} 条记录")
print("-" * 50)
for i, record in enumerate(results[:3]):
    print(f"\n记录 {i + 1}:")
    print(f"原始输入: {record['csc_input']}")
    print(f"原始输出: {record['csc_output']}")
    print(f"改正后输出: {record['correct']}")
    print("错字信息:")
    for char, info in record['wrong_chars'].items():
        print(f"  '{char}': {info}")
    print("-" * 50)