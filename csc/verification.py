import pathlib

import csc


def deduplicate_results(results: list[dict]) -> list[dict]:
    new_results = []
    temp_output = None
    for result in results:
        if result['output'] != temp_output:
            new_results.append(result)
            temp_output = result['output']
    return new_results


class Dataset:

    def __init__(self, path: str, run_name: str | None = None):
        self.path = pathlib.Path(path)
        self.run_name = run_name or self.path.parent.stem
        self.csc_outputs = []
        self.corrected_samples = []
        self.data = []

    def load_data(self, deduplicate: bool = True):
        self.csc_outputs = csc.load_file(self.path)
        if deduplicate:
            self.csc_outputs = deduplicate_results(self.csc_outputs)

    def get_corrected_samples(self, save: bool = True):
        if not self.csc_outputs:
            raise RuntimeError('No CSC outputs found!')
        # TODO: 添加对csc_outputs到修改后句子的处理逻辑

    def convert_samples_to_dataset_items(self):
        if not self.corrected_samples:
            raise RuntimeError('No corrected samples found!')
        for item in self.corrected_samples:
            self.data.append({
                'instruction': '请判断下列句子A和句子B哪一句更好，更通顺。直接输出A或者B单个字母即可，'
                               '不要输出其他任何内容。若两句都好都通顺，则输出A。',
                'input': f'句子A：{item['input']}\n句子B：{item['corrected']}',
                'output': None,
            })

    def save_data(self, output_root: str):
        if not self.data:
            raise RuntimeError('No data to save!')
        output_path = pathlib.Path(output_root)
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / f'{self.run_name}.jsonl'
        with output_file.open('w', encoding='utf-8') as f:
            for item in self.data:
                f.write(csc.prettify(item, indent=None) + '\n')
        if (dataset_info_file := output_path / 'dataset_info.json').exists():
            dataset_info = csc.load_file(dataset_info_file)
        else:
            dataset_info = {}
        dataset_info[self.run_name] = {
            'file_name': f'{self.run_name}.jsonl',
            'columns': {
                'prompt': 'instruction',
                'query': 'input',
                'response': None,
            },
        }
        with dataset_info_file.open('w', encoding='utf-8') as f:
            f.write(csc.prettify(dataset_info) + '\n')
        print('Data saved to:', output_file.resolve().absolute())
