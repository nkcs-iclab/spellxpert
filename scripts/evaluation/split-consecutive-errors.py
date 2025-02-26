import re
import json
import pathlib

import csc

opening_tag = '<csc>'
closing_tag = '</csc>'


def separate_tagged_string(string: str) -> str:
    def expand_tags(match: re.Match) -> str:
        content = match.group(1)
        return ''.join(f'{opening_tag}{char}{closing_tag}' for char in content)

    pattern = rf'{opening_tag}(.*?){closing_tag}'
    output_string = re.sub(pattern, expand_tags, string)
    return output_string


def main(
        path: str,
        report_root: str = '../../../reports/evaluation',
):
    path = pathlib.Path(path)
    report_path = pathlib.Path(report_root) / path.parent.stem
    report_path.mkdir(parents=True, exist_ok=True)
    data = csc.datasets.utils.load_data_from_file(path)
    with (report_path / 'split-generated-predictions.jsonl').open('w') as f:
        for item in data:
            f.write(json.dumps({
                'prompt': item['prompt'],
                'label': item['label'],
                'predict': separate_tagged_string(item['predict']),
            }, ensure_ascii=False) + '\n')
