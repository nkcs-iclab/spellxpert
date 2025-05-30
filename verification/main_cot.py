import json
from typing import Dict, Any


def generate_reasoning_chain(wrong_chars: Dict, record: Dict) -> str:
    """生成结构化的推理过程"""
    # 1. 开头部分
    wrong_words = list(wrong_chars.keys())
    reasoning = [
        f'首先根据"csc_output"提取错字，句中通过<csc>标签标记的错字是{"、".join(f"“{w}”" for w in wrong_words)}。',
        f'可以发现这句话有{len(wrong_words)}个错字。'
    ]

    # 2. 为每个错字生成详细推理
    for i, (char, info) in enumerate(wrong_chars.items(), 1):
        # 基础信息
        char_type = "连续错字组" if len(char) > 1 else "单个错字"
        domain_phrase = info.get('domain', '')
        corrections = info.get('corrections', [])
        simplified = info.get('simplified', [])
        final_correction = info.get('final_correction', '')
        remove_flag = info.get('remove', 0)

        # 当前错字的推理
        char_reasoning = [
            f'\n第{i}个错字是“{char}”（{char_type}）:'
        ]

        if remove_flag == 1:
            remove_text = info.get('text', [])
            remove_text = ', '.join(f'"{text}"' for text in remove_text)
            remove_desc = f'在"csc_think"字段中定位被引号包裹的错字，在其附近发现{remove_text}等包含删除关键词的表述，因此判断该错字在原句中应被删去'
            char_reasoning.append(f'1.删除判断：在"csc_think"字段中{remove_desc}')
        else:
            # 候选改正字部分
            corr_text = info.get('text', [])
            corr_text = '、 '.join(f'"{text}"' for text in corr_text)
            corr_desc = f'发现{corr_text}等表述。因为这些表述都包含了“应该是”、“应该为”、 “应该用”、“应该改为”等关键词之一，所以认为这些表述中后一个引号包裹的内容为错字的改正字，得到集合{corrections}作为候选改正词组'

            if len(char) > 1:  # 连续错字
                if not corrections:
                    char_reasoning.append(f'1.候选改正词：在"csc_think"字段中定位被引号包裹的错字，在其附近没找到提示需要修改的语句，因此未能找到该错字的改正词')
                    char_reasoning.append('2.未找到匹配的改正词，保留原词')
                else:
                    char_reasoning.append(f'1.候选改正词：在"csc_think"字段中定位被引号包裹的错字，在其附近{corr_desc}')
                    if final_correction and final_correction != "No matching correction":
                        char_reasoning.append(f'2.选择“{final_correction}”：“{final_correction}”长度为{len(char)}，与连续错字长度相同，因此选择“{final_correction}”作为最终的改正词')
                    else:
                        char_reasoning.append(f'2.候选改正词中没有长度为{len(char)}的改正词，即未找到长度匹配的改正词，保留原词')
            else:  # 单个错字
                if not corrections:
                    char_reasoning.append(f'1.候选改正字：在"csc_think"字段中定位被引号包裹的错字，在其附近没找到提示需要修改的语句，因此未能找到该错字的改正字')
                else:
                    char_reasoning.append(f'1.候选改正字：在"csc_think"字段中定位被引号包裹的错字，在其附近{corr_desc}')
                    char_reasoning.append(f'2.上下文分析：基于错字所在位置的上下文，确定邻域词组为“{domain_phrase}”')
                    char_reasoning.append(f'3.精简改正字：去除邻域词组已有字后得到精简的候选改正词集合{simplified}')
                    if len(final_correction) > 1:
                        char_reasoning.append(f'4.选用多字改正字：精简改正字中无可用的单字改正字或单子改正字与错字本身相同，因此选择候选改正字中的多字改正字“{final_correction}”对错字进行修改')
                    else:
                        if final_correction == "No matching correction":
                            char_reasoning.append('4.无有效精简改正字：精简改正字中无单字改正字，无法自动改正，因此直接输出原句')
                        else:
                            # 解释选择逻辑
                            if all(final_correction in c for c in corrections):
                                logic = f'“{final_correction}”出现在所有改正词组中，大概率是正确的改正字'
                            elif final_correction not in domain_phrase:
                                logic = f'虽然单字改正字“{final_correction}”不是其余候选改正字的子集，但“{final_correction}”没有出现在错字的领域词组中，因此可以选择其作为最终改正字'
                            else:
                                logic = f'没有找到所有候选改正字的公共子集或没出现在领域词组中的单字改正字，因此随机选择单字改正字“{final_correction}”作为最终改正字'

                            char_reasoning.append(f'4.选择“{final_correction}”：{logic}')

        reasoning.extend(char_reasoning)

    # 3. 最终结论
    corrections_desc = []
    for char, info in wrong_chars.items():
        if info.get('remove', 0) == 1:
            corrections_desc.append(f'“{char}”被删除')
        else:
            final = info.get('final_correction', 'No matching correction')
            if final == "No matching correction":
                corrections_desc.append(f'“{char}”无改正')
            else:
                corrections_desc.append(f'“{char}”改为“{final}”')

    reasoning.extend([
        '\n因此，最终确定：' + '，'.join(corrections_desc),
        '应用所有改正和删除操作后得到最终输出。'
    ])

    return "\n".join(reasoning)


def transform_to_chain_format(csc_mes_file: str, output_file: str):
    """将csc_mes.json转换为思维链格式"""
    with open(csc_mes_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chain_data = []
    for index, record in enumerate(data, start=1):
        cot = generate_reasoning_chain(record["wrong_chars"], record)
        chain_record = {
            "index": index,
            "input": {
                "csc_input": record["csc_input"],
                "csc_output": record["csc_output"],
                "csc_think": record["csc_think"]
            },
            "think": cot,
            "output": record["correct"]
        }
        chain_data.append(chain_record)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chain_data, f, ensure_ascii=False, indent=2)


# cot数据生成
csc_mes_file = "csc_mes.json"
output_chain_file = "cot.json"
transform_to_chain_format(csc_mes_file, output_chain_file)