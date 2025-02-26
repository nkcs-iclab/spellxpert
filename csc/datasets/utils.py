from __future__ import annotations

import re
import json
import yaml
import pathlib

import csc


def select_data_by_step(data: list, step: int) -> list:
    return [item for index, item in enumerate(data) if index % step == 0]


def load_data_from_file(path: str | pathlib.Path, file_type: str | None = None):
    path = pathlib.Path(path)
    if file_type is None:
        file_type = path.suffix[1:]
    if file_type == 'json':
        return json.loads(path.read_text())
    if file_type == 'jsonl':
        return [json.loads(line) for line in path.read_text().split('\n') if line]
    if file_type == 'yaml':
        return yaml.safe_load(path.read_text())
    if file_type in ('txt', 'tsv', 'csv'):
        return [line for line in path.read_text().split('\n') if line]
    raise ValueError(f'Unsupported file type: {file_type}')


def compare_string_length_and_warn(a: str, b: str) -> bool:
    if len(a) != len(b):
        print(f'Length not match: {len(a)} vs {len(b)} (a: {a}, b: {b})')
        return False
    return True


def extract_errors_from_strings(text_with_errors: str, text_corrected: str) -> list:
    errors = []
    for i in range(len(text_with_errors)):
        if text_with_errors[i] != text_corrected[i]:
            errors.append([i + 1, text_with_errors[i], text_corrected[i]])
    return errors


def print_save_log(
        data: list[csc.datasets.base.DatasetItem],
        max_input_length: int,
        max_full_length: int,
        path: pathlib.Path,
):
    print(f'Saved {len(data)} items to {path}')
    print('Max input length:', max_input_length)
    print('Max full length:', max_full_length)


def split_sentences(text: str) -> list[str]:
    text = re.sub(r'([。！？?])([^”’])', r'\1\n\2', text)  # 单字符断句符
    text = re.sub(r'(\.{6})([^”’])', r'\1\n\2', text)  # 英文省略号
    text = re.sub(r'(…{2})([^”’])', r'\1\n\2', text)  # 中文省略号

    # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
    text = re.sub(r'([。！？?][”’])([^，。！？?])', r'\1\n\2', text)

    text = text.rstrip()  # 段尾如果有多余的\n就去掉它
    # 很多规则中会考虑分号;，但是这里把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可
    return text.split('\n')
