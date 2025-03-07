import tqdm

import csc

from csc.data.base import Dataset


class LemonV2Dataset(Dataset):

    def load_data(self):
        keys = self.config['files'].keys()
        for key in keys:
            self.data[key] = []
            data = csc.load_file(self.get_file_path(key))
            for line in tqdm.tqdm(data, desc=f'Loading {key} data'):
                text_with_errors, text_corrected = line.split('\t')
                text_with_errors, text_corrected = text_with_errors.replace(' ', ''), text_corrected.replace(' ', '')
                if not csc.data.utils.compare_string_length_and_warn(text_with_errors, text_corrected):
                    continue
                errors = csc.data.utils.extract_errors_from_strings(text_with_errors, text_corrected)
                template = csc.data.base.templates[self.template]
                item = template.process_string(text_with_errors, errors)
                item.extra_info.corrected = text_corrected
                item.extra_info.has_error = len(errors) > 0
                self.data[key].append(item)
