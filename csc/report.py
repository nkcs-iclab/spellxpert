from __future__ import annotations

import abc
import enum
import pathlib

import csc


class Filter(enum.IntFlag):
    HAS_FN = enum.auto()
    HAS_FP = enum.auto()
    HAS_TP = enum.auto()
    HAS_TN = enum.auto()


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
                self.config.report_path / f'html-report-{self.config.html_report.filter}.html',
                filter_=self.config.html_report.filter,
            )
        if self.config.json_report.enabled:
            self.reports['json_report'] = JSONReport(self.config.report_path / 'json-report.json')

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
        status = (
                (Filter.HAS_TP if tp > 0 else 0) |
                (Filter.HAS_FP if fp > 0 else 0) |
                (Filter.HAS_FN if fn > 0 else 0) |
                (Filter.HAS_TN if tp + fn + fp < length else 0)
        )
        return status & (self.filter or 0) == (self.filter or 0)


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

    def write_entry(self, prompt: str, label_array: list[bool], predict_array: list[bool], **_):
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
