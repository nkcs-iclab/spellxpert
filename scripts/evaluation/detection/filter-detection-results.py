import fire
import json
import pathlib

import csc

black_list = [
    '',  # 空白
    '。', '，', '、', '；', '：', ',', ';',  # 分割
    '？', '！',  # 语气
    '“', '”', '‘', '’', '"',  # 引用
    '『', '』', '《', '》', '<', '>',  # 书名
    '（', '）', '【', '】', '(', ')', '[', ']',  # 括号
    '＋', '+', '-', '*', '×', '/', '=', '%',  # 运算
    '…', '—', '－', '•', '·', '—>', '～', '~', '@', '——', '&', '#'  # 其他
]


def main(path: str):
    path = pathlib.Path(path)
    data = csc.datasets.utils.load_data_from_file(path)
    with path.with_suffix('.txt').open('w') as text_file, path.with_suffix('.filtered.jsonl').open('w') as jsonl_file:
        for item in data:
            label, predict = item['label'], item['predict']
            for char in black_list:
                label = label.replace(f'<csc>{char}</csc>', char)
                predict = predict.replace(f'<csc>{char}</csc>', char)
            jsonl_file.write(json.dumps({
                'prompt': item['prompt'],
                'label': label,
                'predict': predict,
            }, ensure_ascii=False) + '\n')
            if '<csc>' in predict:
                text_file.write(f'{predict}\n')


if __name__ == '__main__':
    fire.Fire(main)
