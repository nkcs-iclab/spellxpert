import tqdm
import pathlib

import csc

from csc.data.base import Dataset


class STCNDataset(Dataset):

    def load_data(self):
        self.data[csc.TEST] = []
        if self.variant in ('g3'):
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
                    if sentence:
                        template = csc.data.base.templates[self.template]
                        item = template.process_string(sentence, [])
                        item.output = None
                        self.data[csc.TEST].append(item)
