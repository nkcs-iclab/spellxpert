import json
from get_wrong_chars import get_wrong_characters
from get_corrections import get_corrections
from get_domain import get_domain
from get_output import get_output
from get_cleared_data import process_jsonl


def process_json_file(input_file, output_file, correct_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    results = []
    correct = []
    for index, record in enumerate(data, start=1):
        # 获取当前记录的input、output和think字段
        csc_input = record['input']
        csc_output = record['output']
        csc_think = record.get('think', '')

        # 1. 提取错字及其邻错字数
        wrong_chars = get_wrong_characters(csc_output)
        # 2. 提取改正字与删除标识
        wrong_chars = get_corrections(csc_think, wrong_chars, csc_output)
        # 3. 获取最终改正字和改正后的句子
        corrected_output, wrong_chars = get_output(csc_output, wrong_chars)

        # 构建结果记录csc_mes（记录细节，用于生成思维链数据集）
        result_record = {
            'index': index,
            'csc_input': csc_input,
            'csc_output': csc_output,
            'csc_think': csc_think,
            'correct': corrected_output,
            'wrong_chars': wrong_chars
        }
        results.append(result_record)

        # 构建结果记录correct（仅记录改正后的句子）
        correct_record = {
            'index': index,
            'input': csc_input,
            'output': csc_output,
            'think': csc_think,
            'correct': corrected_output,
        }
        correct.append(correct_record)

    # 保存细节结果到新的JSON文件
    with open(output_file, 'w', encoding='utf-8') as out_file:
        json.dump(results, out_file, ensure_ascii=False, indent=2)

    # 保存提取结果到新的JSON文件
    with open(correct_file, 'w', encoding='utf-8') as correct_out_file:
        json.dump(correct, correct_out_file, ensure_ascii=False, indent=2)

    return results


# 文件路径
jsonl_file_path = 'extract-output-FP-TP.jsonl'
cleared_json_file_path = 'extract.json'
correct_file_path = 'correct.json'
output_file_path = 'csc_mes.json'

# 处理JSONL文件并保存为JSON
process_jsonl(jsonl_file_path, cleared_json_file_path)

# 处理文件并保存结果
results = process_json_file(cleared_json_file_path, output_file_path, correct_file_path)

'''
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
'''