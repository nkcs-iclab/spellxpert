import json
import tqdm
import pathlib

import csc

from csc.data.base import Template, DatasetItem, count_data_length, print_save_log


class Template0(Template):
    opening_tag = '<csc>'
    closing_tag = '</csc>'
    instruction = (
        f'我在下列句子中使用{opening_tag}{closing_tag}标记出了疑似的错别字。'
        f'请帮我判断一下我标记出的错别字是否是真正的错别字。'
        f'如果你觉得某个字不是错别字，则将标记去掉，其他字符原封不动输出。'
        f'例如，输入：今天{opening_tag}添{closing_tag}气不{opening_tag}错{closing_tag}，'
        f'则应该输出：今天{opening_tag}添{closing_tag}气不错。'
        f'不要输出任何其他内容，不要给出解释。\n'
    )

    @classmethod
    def process_string(cls, string: str, label: str = '') -> DatasetItem:
        return DatasetItem(
            instruction=cls.instruction,
            input=string,
            output=label,
        )


class Template1(Template0):
    instruction = (
        f'我在下列句子中使用{Template0.opening_tag}{Template0.closing_tag}标记出了疑似的错别字。'
        f'请帮我判断一下我标记出的错别字是否是真正的错别字。要求如下：\n'
        f'1. 如果你觉得某个字不是错别字，则将标记去掉，其他字符原封不动输出。\n'
        f'2. 如果你觉得某个字是错别字但是我没有标记出来，你也不要新增标记。\n'
        f'3. 不要输出任何其他内容，不要给出解释。\n'
        f'例如，输入：今天{Template0.opening_tag}添{Template0.closing_tag}气不{Template0.opening_tag}错{Template0.closing_tag}，'
        f'则应该输出：今天{Template0.opening_tag}添{Template0.closing_tag}气不错。\n'
    )


templates = [
    Template0,
    Template1,
]


class VerificationDataset:

    def __init__(
            self,
            path: str | pathlib.Path,
            input_template: int,
            output_template: int,
            name: str,
            variant: str | None = None,
    ):
        self.path = pathlib.Path(path)
        self.input_template = input_template
        self.output_template = output_template
        self.name = name
        self.variant = variant
        self.data = {}

    def load_data(self):
        data = csc.load_file(self.path)
        input_template = csc.evaluation.templates[self.input_template]
        output_template = templates[self.output_template]
        self.data[csc.TEST] = []
        for item in tqdm.tqdm(data):
            self.data[csc.TEST].append(output_template.process_string(
                string=input_template.clean_predict(item['predict']),
                label=input_template.clean_label(item['label']),
            ))

    def save_data(self, root: str | pathlib.Path):
        path = pathlib.Path(root) / self.name
        for key, data in self.data.items():
            self._save_data(data, path, key)

    def _save_data(self, data: list[DatasetItem], path: pathlib.Path, key: str):
        path /= f'template-{self.output_template}'
        path.mkdir(parents=True, exist_ok=True)
        max_input_length, max_full_length = 0, 0
        if self.variant:
            path = path / f'{self.variant}-{key}.jsonl'
        else:
            path = path / f'{key}.jsonl'
        if path.exists():
            print(f'File {path} already exists. Overwrite? (y/[n])')
            if input().lower() != 'y':
                return
        with path.open('w') as file:
            for item in data:
                text = json.dumps(csc.dataclass_to_cleaned_dict(item), ensure_ascii=False) + '\n'
                input_length, full_length = count_data_length(item)
                max_input_length = max(max_input_length, input_length)
                max_full_length = max(max_full_length, full_length)
                file.write(text)
        print_save_log(data, max_input_length, max_full_length, path)
