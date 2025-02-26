from __future__ import annotations

import abc
import json
import pathlib
import dataclasses

import csc


@dataclasses.dataclass
class DatasetItem:
    system: str
    instruction: str
    input: str
    output: str
    corrected: str | None = None
    has_error: bool | None = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class Template:

    @classmethod
    def process_string(cls, string: str) -> DatasetItem:
        raise NotImplementedError


def add_error_tags(string: str, errors: list, opening_tag: str, closing_tag: str) -> str:
    errors = {error[0] for error in errors}
    output_string = ''
    for index, char in enumerate(string):
        if index + 1 in errors:
            output_string += f'{opening_tag}{char}{closing_tag}'
        else:
            output_string += char
    return output_string


class DetectionDataset(abc.ABC):

    def __init__(self, config: dict):
        self.config = config
        self.data = {}
        self.current_template = None

    @abc.abstractmethod
    def load_data(self, template: int):
        raise NotImplementedError

    def get_file_path(self, key: str) -> pathlib.Path:
        return pathlib.Path(self.config['files']['root']) / self.config['files'][key]

    def split_data(self, train_test_split: float | None):
        if train_test_split is None:
            return
        all_data = self.data[csc.ALL]
        self.data[csc.TRAIN] = all_data[:int(len(all_data) * train_test_split)]
        self.data[csc.TEST] = all_data[int(len(all_data) * train_test_split):]

    def save_data(self, root_path: str, variant: str | None = None):
        path = pathlib.Path(root_path) / self.config['name']
        for key, data in self.data.items():
            self._save_data(data, path, variant, key)

    def _save_data(self, data: list, path: pathlib.Path, variant: str | None, key: str):
        path /= f'template-{self.current_template}'
        path.mkdir(parents=True, exist_ok=True)
        max_input_length, max_full_length = 0, 0
        if variant:
            path = path / f'{variant}-{key}.jsonl'
        else:
            path = path / f'{key}.jsonl'
        if path.exists():
            print(f'File {path} already exists. Overwrite? (y/[n])')
            if input().lower() != 'y':
                return
        with path.open('w') as file:
            for item in data:
                text = json.dumps(item.to_dict(), ensure_ascii=False) + '\n'
                input_length, full_length = count_data_length(item)
                max_input_length = max(max_input_length, input_length)
                max_full_length = max(max_full_length, full_length)
                file.write(text)
        csc.datasets.utils.print_save_log(data, max_input_length, max_full_length, path)


class Template0(Template):
    opening_tag = '<csc>'
    closing_tag = '</csc>'
    system = ''
    instruction = (
        f'指出句子中的错别字（可能有0、1或多个错别字），不需改正。如果发现错字，将文中错字用{opening_tag}{closing_tag}标签包裹，'
        f'其他字符照常输出。不要输出指定输出格式之外的内容。'
    )

    @classmethod
    def process_string(cls, string: str, errors: list | None = None) -> DatasetItem:
        errors = errors or []
        output = add_error_tags(string, errors=errors, opening_tag=cls.opening_tag, closing_tag=cls.closing_tag)
        return DatasetItem(
            system=cls.system,
            instruction=cls.instruction,
            input=string,
            output=output,
        )


class Template1(Template0):

    @classmethod
    def process_string(cls, string: str, errors: list | None = None) -> DatasetItem:
        errors = errors or []
        output = add_error_tags(string, errors=errors, opening_tag=cls.opening_tag, closing_tag=cls.closing_tag)
        return DatasetItem(
            system=cls.instruction,
            instruction=string,
            input='',
            output=output,
        )


class Template2(Template):
    opening_tag = '<csc>'
    closing_tag = '</csc>'
    system = (
        '你是一个专业的中文错别字检测器。你的任务是识别给定句子中的错别字。请特别注意同音字和形近字（包含中文繁体近形字）的误用。\n\n'
        '规则：\n'
        '1. 仔细分析整个句子的上下文来判断是否存在错别字。\n'
        '2. 注意考虑原文的时代背景和文字风格，特别关注可能出错的人名、地名。\n'
        f'3. 将发现的错别字用{opening_tag}{closing_tag}标签包裹，其他字符照常输出。\n'
        '4. 如果有多个连续的错别字，每个错别字都需要单独标记。\n'
        '5. 不要过度标记，确保只标记真正的错别字。\n'
        '6. 如果没有发现错别字,原样输出句子。\n'
        '7. 仅输出带标签的句子，不需额外解释。\n\n'
        '示例：\n'
        '输入：邱吉羽首相在下议院就克利涌斯使印一事发表之演说亦在其内\n'
        f'输出：邱吉{opening_tag}羽{closing_tag}首相在下议院就克利{opening_tag}涌{closing_tag}斯使印一事发表之演说亦在其内'
    )

    @classmethod
    def process_string(cls, string: str, errors: list | None = None) -> DatasetItem:
        errors = errors or []
        output = add_error_tags(string, errors=errors, opening_tag=cls.opening_tag, closing_tag=cls.closing_tag)
        return DatasetItem(
            system=cls.system,
            instruction=string,
            input='',
            output=output,
        )


class Template3(Template0):
    instruction = (
        f'指出句子中的错别字（可能有0、1或多个错别字），不需改正。具体要求如下：\n'
        f'1. 如果发现错字，将文中错字逐个用<csc></csc>标签包裹。连续的错别字请分别使用标签包裹。例如AB为错字，应标记为<csc>A</csc><csc>B</csc>，而不是<csc>AB</csc>。\n'
        f'2. 非错误字符照常输出。\n'
        f'3. 同一个词里如果只有一个字为错字，标记一个错的那个字即可，不要将正确的字包含进标记中。例如“竟争”应该标记为<csc>竟</csc>争而不是<csc>竟争</csc>。\n'
        f'4. 不要试图修改句子中的错别字，只需标记错别字。\n'
        f'5. 无需给出解释和备注（即使你对某个输出不确定），仅输出带标签的句子。严禁输出指定输出格式之外的内容。\n'
        f'6. 严禁新增任何原文中没有的内容。例如无需添加原句中遗漏或不存在的句末标点。\n\n'
        f'待检查的句子：\n\n'
    )


templates = [
    Template0,
    Template1,
    Template2,
    Template3,
]


def count_data_length(data: DatasetItem) -> tuple[int, int]:
    input_length = len(data.system) + len(data.instruction) + len(data.input)
    return input_length, input_length + (len(data.output) if data.output else 0)
