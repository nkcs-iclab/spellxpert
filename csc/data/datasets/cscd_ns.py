import tqdm

import csc

from csc.data.base import Dataset


class CSCDNSDataset(Dataset):

    def load_data(self):
        if self.variant == 'reasoning':
            self._load_data(csc.load_file(self.get_file_path(csc.TEST)), csc.TEST)
        else:
            self._load_data(csc.load_file(self.get_file_path(csc.TRAIN)), csc.TRAIN)
            self._load_data(csc.load_file(self.get_file_path(csc.TEST)), csc.TEST)

    def _load_data(self, data: list, key: str):
        self.data[key] = []
        for line in tqdm.tqdm(data, desc=f'Loading {key} data'):
            has_error, text_with_errors, text_corrected = line.split('\t')
            if not csc.data.utils.compare_string_length_and_warn(text_with_errors, text_corrected):
                continue
            errors = csc.data.utils.extract_errors_from_strings(text_with_errors, text_corrected)
            template = csc.data.base.templates[self.template]
            item = template.process_string(text_with_errors, errors)
            item.extra_info.corrected = text_corrected
            item.extra_info.has_error = len(errors) > 0
            self.data[key].append(item)
