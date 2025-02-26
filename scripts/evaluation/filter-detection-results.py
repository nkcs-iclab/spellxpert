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

opening_tag = '<csc>'
closing_tag = '</csc>'


def main(
        path: str,
        remove_black_list: bool = True,
        report_root: str = '../../reports/evaluation',
):
    path = pathlib.Path(path)
    report_path = pathlib.Path(report_root) / path.parent.stem
    report_path.mkdir(parents=True, exist_ok=True)
    data = csc.datasets.utils.load_data_from_file(path)
    with (
        (report_path / 'filtered-output.txt').open('w') as filtered_output,
        (report_path / 'filtered-generated-predictions.jsonl').open('w') as filtered_generated_predictions,
    ):
        for item in data:
            label, predict = item['label'], item['predict']
            if remove_black_list:
                for char in black_list:
                    label = label.replace(f'{opening_tag}{char}{closing_tag}', char)
                    predict = predict.replace(f'{opening_tag}{char}{closing_tag}', char)
            predict = predict.split('</think>\n\n')[-1]
            label = label.split('<｜end▁of▁sentence｜>')[0]
            filtered_generated_predictions.write(json.dumps({
                'prompt': item['prompt'],
                'label': label,
                'predict': predict,
            }, ensure_ascii=False) + '\n')
            if opening_tag in predict:
                filtered_output.write(f'{predict}\n')


if __name__ == '__main__':
    fire.Fire(main)
