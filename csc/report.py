from __future__ import annotations

import abc
import enum
import pathlib

import csc


class Filter(enum.IntFlag):
    FN = enum.auto()
    FP = enum.auto()
    TP = enum.auto()
    TN = enum.auto()

    def to_string(self) -> str:
        return '-'.join([name for name, member in self.__class__.__members__.items() if member & self])


class OutputMode(enum.IntFlag):
    JSONL = enum.auto()
    HUMAN_READABLE = enum.auto()
    PLAIN_TEXT = enum.auto()


class ReportManager:

    def __init__(self, config: csc.evaluation.EvaluationConfig):
        self.config = config
        self.reports = {}

    def init(self):
        if self.config.report_path.exists():
            print(f'Report path {self.config.report_path} already exists. Overwrite? (y/[n])')
            if input().lower() != 'y':
                return False
        self.config.report_path.mkdir(parents=True, exist_ok=True)

        if self.config.html_report.enabled:
            self.reports['html_report'] = HTMLReport(
                self.config.report_path / f'html-report-{self.config.html_report.filter.to_string()}.html',
                filter_=self.config.html_report.filter,
            )
        if self.config.json_report.enabled:
            self.reports['json_report'] = JSONReport(self.config.report_path / 'json-report.json')
        if self.config.extract_output.enabled:
            self.reports['extract_output'] = ExtractReport(
                self.config.report_path,
                filter_=self.config.extract_output.filter,
                mode=self.config.extract_output.mode,
            )

        return True

    def write_head(self):
        for report in self.reports.values():
            report.write_head()

    def write_tail(self, result: csc.evaluation.EvaluationResult):
        for report in self.reports.values():
            report.write_tail(result)

    def write_entry(self, tp: int, fp: int, fn: int, length: int, *args, **kwargs):
        for report in self.reports.values():
            if report.should_pick(tp, fp, fn, length):
                report.write_entry(*args, **kwargs)


class Report(abc.ABC):

    def __init__(self, path: pathlib.Path, filter_: Filter | None = None):
        self.path = path
        self.filter = filter_

    def write_head(self):
        pass

    def write_tail(self, result: csc.evaluation.EvaluationResult):
        pass

    def write_entry(self, *args, **kwargs):
        pass

    def should_pick(self, tp: int, fp: int, fn: int, length: int) -> bool:
        if self.filter is None:
            return True
        if Filter.FN in self.filter and fn > 0:
            return True
        if Filter.FP in self.filter and fp > 0:
            return True
        if Filter.TP in self.filter and tp > 0:
            return True
        if Filter.TN in self.filter and tp + fp + fn < length:
            return True
        return False


class HTMLReport(Report):
    html_head = '''
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <title>CSC Evaluation</title>
        <style>
            .tp {
                color: green;
            }
            .fp {
                color: blue;
            }
            .fn {
                color: red;
            }
            .csc-pair {
                margin: 5px;
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 10px;
            }
        </style>
    </head>
    <body>
    '''
    html_tail = '''
    </body>
    </html>
    '''

    def write_head(self):
        self.path.write_text(self.html_head)

    def write_tail(self, _):
        with self.path.open('a') as f:
            f.write(self.html_tail)

    def write_entry(
            self,
            item: dict,
            template: csc.evaluation.Template,
            label_array: list[bool],
            predict_array: list[bool],
            *_,
            **__,
    ):
        prompt = template.clean_prompt(item['prompt'])
        if len(prompt) == len(label_array) == len(predict_array):
            output_string = []
            for c_text, b_label, b_predict in zip(prompt, label_array, predict_array):
                if b_label == 1 and b_predict == 1:
                    output_string.append(f'<span class="tp">{c_text}</span>')
                elif b_label == 0 and b_predict == 1:
                    output_string.append(f'<span class="fp">{c_text}</span>')
                elif b_label == 1 and b_predict == 0:
                    output_string.append(f'<span class="fn">{c_text}</span>')
                else:
                    output_string.append(c_text)
            entry = f'<div class="csc-pair">{''.join(output_string)}</div>\n'
        else:
            entry = ''
        with self.path.open('a') as f:
            f.write(entry)


class JSONReport(Report):

    def write_tail(self, result: csc.evaluation.EvaluationResult):
        result_string = csc.prettify(csc.dataclass_to_cleaned_dict(result))
        self.path.write_text(result_string)


class ExtractReport(Report):

    def __init__(self, path: pathlib.Path, filter_: Filter | None = None, mode: OutputMode = OutputMode.JSONL):
        super().__init__(path, filter_)
        self.mode = mode
        self.index = 1
        self.jsonl_path = self.path / f'extract-output-{self.filter.to_string()}.jsonl'
        self.human_readable_path = self.path / f'extract-output-{self.filter.to_string()}.jsonl.txt'
        self.plain_text_path = self.path / f'extract-output-{self.filter.to_string()}.plain.txt'

    def write_head(self):
        if OutputMode.JSONL in self.mode:
            self.jsonl_path.write_text('')
        if OutputMode.HUMAN_READABLE in self.mode:
            self.human_readable_path.write_text('')
        if OutputMode.PLAIN_TEXT in self.mode:
            self.plain_text_path.write_text('')

    def write_entry(self, item: dict, template: csc.evaluation.Template, *_, **__):
        if OutputMode.JSONL in self.mode:
            with self.jsonl_path.open('a') as f:
                f.write(csc.prettify(item, indent=None) + '\n')
        if OutputMode.HUMAN_READABLE in self.mode:
            with self.human_readable_path.open('a') as f:
                prompt = template.clean_prompt(item['prompt'])
                label = template.clean_label(item['label'])
                predict = template.clean_predict(item['predict'])
                if hasattr(template, 'clean_reasoning') and callable(template.clean_reasoning):
                    new_item = {
                        'id': self.index,
                        'input': prompt,
                        'reasoning': template.clean_reasoning(item['predict']),
                        'predict': predict,
                        'label': label,
                    }
                else:
                    new_item = {
                        'id': self.index,
                        'input': prompt,
                        'predict': predict,
                        'label': label,
                    }
                f.write(csc.prettify(new_item) + '\n')
        if OutputMode.PLAIN_TEXT in self.mode:
            with self.plain_text_path.open('a') as f:
                f.write(template.clean_predict(item['predict']) + '\n')
        self.index += 1
