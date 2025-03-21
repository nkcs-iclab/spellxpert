import fire
import json
import pathlib

import csc


def template_qwen(prompt: str) -> tuple[str, str]:
    system = prompt.split('system\n')[-1].split('\nuser\n')[0] if 'system\n' in prompt else ''
    instruction = prompt.split('\nuser\n')[-1].split('\nassistant\n')[0]
    return system, instruction


def template_deepseek3(prompt: str) -> tuple[str, str]:
    system = prompt.split('<｜System｜>')[-1].split('<｜User｜>')[0] if '<｜System｜>' in prompt else ''
    instruction = prompt.split('<｜User｜>')[-1].split('<｜Assistant｜>')[0]
    return system, instruction


templates = {
    'qwen': template_qwen,
    'deepseek3': template_deepseek3,
}


def main(
        path: str,
        template: str,
        report_root: str = '../../../reports/evaluation',
):
    path = pathlib.Path(path)
    report_path = pathlib.Path(report_root) / path.parent.stem
    report_path.mkdir(parents=True, exist_ok=True)
    data = csc.load_file(path)
    report_path /= f'extracted-dataset-from-{path.stem}.jsonl'
    with report_path.open('w') as f:
        for item in data:
            prompt = item['prompt']
            system, instruction = templates[template](prompt)
            output = item['label']
            new_item = {
                'system': system,
                'instruction': instruction,
                'output': output,
            }
            f.write(json.dumps(new_item, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    fire.Fire(main)
