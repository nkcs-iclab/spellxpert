import re
import pathlib
import deepmerge

import csc


def compare_string_length_and_warn(a: str, b: str) -> bool:
    if len(a) != len(b):
        print(f'Length not match: {len(a)} vs {len(b)} (a: {a}, b: {b})')
        return False
    return True


def extract_errors_from_strings(text_with_errors: str, text_corrected: str) -> list[tuple[int, str, str]]:
    errors = []
    for i in range(len(text_with_errors)):
        if text_with_errors[i] != text_corrected[i]:
            errors.append((i + 1, text_with_errors[i], text_corrected[i]))
    return errors


def split_sentences(text: str) -> list[str]:
    text = re.sub(r'([。！？?])([^”’])', r'\1\n\2', text)  # 单字符断句符
    text = re.sub(r'(\.{6})([^”’])', r'\1\n\2', text)  # 英文省略号
    text = re.sub(r'(…{2})([^”’])', r'\1\n\2', text)  # 中文省略号

    # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
    text = re.sub(r'([。！？?][”’])([^，。！？?])', r'\1\n\2', text)

    text = text.rstrip()  # 段尾如果有多余的\n就去掉它
    # 很多规则中会考虑分号;，但是这里把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可
    return text.split('\n')


def load_dataset_config(path: str | pathlib.Path, root: str | pathlib.Path = '', variant: str | None = None) -> dict:
    dataset_config = csc.load_file(path)
    if 'variants' in dataset_config:
        if 'main' in dataset_config['variants']:
            dataset_config = deepmerge.always_merger.merge(dataset_config, dataset_config['variants']['main'])
        if variant is not None and variant in dataset_config['variants']:
            dataset_config = deepmerge.always_merger.merge(dataset_config, dataset_config['variants'][variant])
    dataset_config['root'] = pathlib.Path(root) / dataset_config['root']
    dataset_config.pop('variants', None)
    return dataset_config
