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


def main(
        path: str,
        report_root: str = '../../../reports/evaluation/detection',
):
    path = pathlib.Path(path)
    if path.is_dir():
        path /= 'generated_predictions.jsonl'
    report_path = pathlib.Path(report_root) / path.parent.stem
    report_path.mkdir(parents=True, exist_ok=True)
    data = csc.datasets.utils.load_data_from_file(path)
    with (
        (report_path / 'filtered_output.txt').open('w') as filtered_output,
        (report_path / 'filtered_generated_predictions.jsonl').open('w') as filtered_generated_predictions,
    ):
        for item in data:
            label, predict = item['label'], item['predict']
            for char in black_list:
                label = label.replace(f'<csc>{char}</csc>', char)
                predict = predict.replace(f'<csc>{char}</csc>', char)
            filtered_generated_predictions.write(json.dumps({
                'prompt': item['prompt'],
                'label': label,
                'predict': predict,
            }, ensure_ascii=False) + '\n')
            if '<csc>' in predict:
                filtered_output.write(f'{predict}\n')


if __name__ == '__main__':
    fire.Fire(main)
