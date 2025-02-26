import tqdm

import csc

from csc.datasets.base import DetectionDataset


class CSCDNSDataset(DetectionDataset):

    def load_data(self, template: int):
        self.current_template = template
        self._load_data(csc.datasets.utils.load_data_from_file(self.get_file_path(csc.TRAIN)), csc.TRAIN)
        self._load_data(csc.datasets.utils.load_data_from_file(self.get_file_path(csc.TEST)), csc.TEST)

    def _load_data(self, data: list, key: str):
        self.data[key] = []
        for line in tqdm.tqdm(data, desc=f'Loading {key} data'):
            has_error, text_with_errors, text_corrected = line.split('\t')
            if not csc.datasets.utils.compare_string_length_and_warn(text_with_errors, text_corrected):
                continue
            errors = csc.datasets.utils.extract_errors_from_strings(text_with_errors, text_corrected)
            template = csc.datasets.base.templates[self.current_template]
            item = template.process_string(text_with_errors, errors)
            item.corrected = text_corrected
            item.has_error = len(errors) > 0
            self.data[key].append(item)
