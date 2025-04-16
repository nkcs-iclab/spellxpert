import tqdm
import pathlib

import csc

from csc.data.base import Dataset


blacklist = [
    ('f', '通讯员'),
    ('f', '本报'),
    ('f', '本版'),
    ('b', '电'),
]


def should_output(text: str) -> bool:
    if not text:
        return False
    for rule in blacklist:
        match rule[0]:
            case 'f':
                if text.startswith(rule[1]):
                    return False
            case 'b':
                if text.endswith(rule[1]):
                    return False
            case 'a':
                if rule[1] in text:
                    return False
    if len(text) < 10:
        return False
    return True


def clean_text(text: str) -> str:
    text = text.strip()
    if text.startswith('“') and text.endswith('”'):
        text = text[1:-1]
    return text


class STCNDataset(Dataset):

    def load_data(self):
        self.data[csc.TEST] = []
        if self.variant in {'g3'}:
            for file in tqdm.tqdm(list(pathlib.Path(self.config['root']).rglob('*.txt'))):
                data = csc.load_file(file)
                for line in tqdm.tqdm(data, desc=f'Loading data'):
                    text_with_errors, _ = line.split('\t\t\t')
                    template = csc.data.base.templates[self.template]
                    item = template.process_string(text_with_errors, [])
                    item.output = None
                    self.data[csc.TEST].append(item)
        else:
            for file in tqdm.tqdm(list(pathlib.Path(self.config['root']).rglob('article.json'))):
                data = csc.load_file(file)
                sentences = csc.data.utils.split_sentences(data['content'])
                for sentence in sentences:
                    sentence = clean_text(sentence)
                    if should_output(sentence):
                        template = csc.data.base.templates[self.template]
                        item = template.process_string(sentence, [])
                        item.output = None
                        self.data[csc.TEST].append(item)
