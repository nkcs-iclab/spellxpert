import pathlib

import csc

from csc.datasets.base import DetectionDataset


class STCNDataset(DetectionDataset):

    def load_data(self, template: int):
        self.current_template = template
        self.data['test'] = []
        for file in pathlib.Path(self.config['files']['root']).rglob('article.json'):
            data = csc.datasets.utils.load_data_from_file(file)
            sentences = csc.datasets.utils.split_sentences(data['content'])
            for text_with_errors in sentences:
                if text_with_errors:
                    template = csc.datasets.base.templates[self.current_template]
                    item = template.process_string(text_with_errors, [])
                    item.output = None
                    self.data['test'].append(item)
