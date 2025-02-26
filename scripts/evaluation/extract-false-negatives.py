import fire
import json
import pathlib

import csc


def main(
        path: str,
        template: int,
        report_root: str = '../../reports/evaluation',
):
    path = pathlib.Path(path)
    report_path = pathlib.Path(report_root) / path.parent.stem
    report_path.mkdir(parents=True, exist_ok=True)
    data = csc.datasets.utils.load_data_from_file(path)
    report_path /= 'false-negatives.jsonl'
    template = csc.evaluation.templates[template]
    with report_path.open('w') as f:
        for item in data:
            label, predict = item['label'], item['predict']
            tp, fp, fn, label_array, predict_array = template.eval_one(label, predict)
            if fn > 0:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    fire.Fire(main)
