import fire
import json
import pathlib

import csc


def main(
        path: str,
        report_root: str = '../../../reports/evaluation/detection',
):
    path = pathlib.Path(path)
    report_path = pathlib.Path(report_root) / path.parent.stem
    report_path.mkdir(parents=True, exist_ok=True)
    data = csc.datasets.utils.load_data_from_file(path)
    report_path /= f'extracted-dataset-from-{path.stem}.jsonl'
    with report_path.open('w') as f:
        for item in data:
            prompt = item['prompt']
            system = prompt.split('system\n')[1].split('\nuser\n')[0]
            instruction = prompt.split('\nuser\n')[-1].split('\nassistant\n')[0]
            output = item['label']
            new_item = {
                'system': system,
                'instruction': instruction,
                'output': output,
            }
            f.write(json.dumps(new_item, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    fire.Fire(main)
