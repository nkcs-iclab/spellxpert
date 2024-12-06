from __future__ import annotations

import re
import json
import pathlib
import dataclasses

from csc.evaluation.template import Template

html_head = '''
<!DOCTYPE html>
<html>
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


def mark_errors(string: str, opening_tag: str, closing_tag: str) -> list[bool]:
    is_error = []
    pattern = re.compile(rf'{opening_tag}(.?){closing_tag}')
    current_index = 0
    for match in pattern.finditer(string):
        start, end = match.span()
        while current_index < start:
            is_error.append(False)
            current_index += 1
        is_error.append(True)
        current_index = end
    while current_index < len(string):
        is_error.append(False)
        current_index += 1
    return is_error


@dataclasses.dataclass
class DetectionMetricResult:
    recall: float = 0
    precision: float = 0
    f1: float = 0
    n_chars: int = 0
    n_label_error_chars: int = 0
    label_error_rate: float = 0
    n_predict_error_chars: int = 0
    predict_error_rate: float = 0
    n_samples: int = 0
    n_label_error_samples: int = 0
    n_predict_error_samples: int = 0

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class Template0(Template):
    opening_tag = '<csc>'
    closing_tag = '</csc>'

    @classmethod
    def eval_one(cls, label: str, predict: str) -> tuple[int, int, int, list[bool], list[bool]]:
        tp, fp, fn = 0, 0, 0
        label_array = mark_errors(label, cls.opening_tag, cls.closing_tag)
        predict_array = mark_errors(predict, cls.opening_tag, cls.closing_tag)
        if len(label_array) != len(predict_array):
            return 0, 0, sum(label_array), label_array, predict_array
        for i in range(len(label_array)):
            if label_array[i] == 1 and predict_array[i] == 1:
                tp += 1
            elif label_array[i] == 0 and predict_array[i] == 1:
                fp += 1
            elif label_array[i] == 1 and predict_array[i] == 0:
                fn += 1
        return tp, fp, fn, label_array, predict_array

    @classmethod
    def html_csc_pair(cls, label: str, predict: str, label_array: list[bool], predict_array: list[bool]) -> str:
        label_chars = label.replace(cls.opening_tag, '').replace(cls.closing_tag, '')
        predict_chars = predict.replace(cls.opening_tag, '').replace(cls.closing_tag, '')
        if not (len(label_chars) == len(predict_chars) == len(label_array) == len(predict_array)):
            return ''
        label, predict = '', ''
        for b_label, b_predict, c_label, c_predict in zip(label_array, predict_array, label_chars, predict_chars):
            if b_label == 1 and b_predict == 1:
                label += f'<span class="tp">{c_label}</span>'
                predict += f'<span class="tp">{c_predict}</span>'
            elif b_label == 0 and b_predict == 1:
                label += f'<span class="fp">{c_label}</span>'
                predict += f'<span class="fp">{c_predict}</span>'
            elif b_label == 1 and b_predict == 0:
                label += f'<span class="fn">{c_label}</span>'
                predict += f'<span class="fn">{c_predict}</span>'
            else:
                label += c_label
                predict += c_predict
        # return f'<div class="csc-pair">\n    <div>{label}</div>\n    <div>{predict}</div>\n</div>\n'
        return f'<div class="csc-pair">\n    <div>{predict}</div>\n</div>\n'

templates = [
    Template0,
]


class DetectionMetric:

    def __init__(self, template: int, report_path: str | pathlib.Path):
        self.template = templates[template]
        self.result = DetectionMetricResult()
        self.report_path = pathlib.Path(report_path)

    def write_html_report_head(self):
        self.report_path.mkdir(parents=True, exist_ok=True)
        with open(self.report_path / 'index.html', 'w') as f:
            f.write(html_head)

    def write_html_report_tail(self):
        with open(self.report_path / 'index.html', 'a') as f:
            f.write(html_tail)

    def write_html_report_entry(self, label: str, predict: str, label_array: list[bool], predict_array: list[bool]):
        with open(self.report_path / 'index.html', 'a') as f:
            f.write(self.template.html_csc_pair(label, predict, label_array, predict_array))

    def print_and_write_json_report(self):
        result = json.dumps(self.result.to_dict(), indent=2)
        print(result)
        (self.report_path / 'result.json').write_text(result)

    def eval(self, data: list[dict], report_fn_only: bool = False) -> DetectionMetricResult:
        self.write_html_report_head()
        total_tp, total_fp, total_fn = 0, 0, 0
        for item in data:
            label, predict = item['label'], item['predict']
            predict = predict.split('（使用包裹每一个错别字）：')[-1]
            tp, fp, fn, label_array, predict_array = self.template.eval_one(label, predict)
            total_tp += tp
            total_fp += fp
            total_fn += fn
            self.result.n_chars += len(label_array)
            if (n_label_error_chars := tp + fn) > 0:
                self.result.n_label_error_samples += 1
                self.result.n_label_error_chars += n_label_error_chars
            if (n_predict_error_chars := tp + fp) > 0:
                self.result.n_predict_error_samples += 1
                self.result.n_predict_error_chars += n_predict_error_chars
            if label != predict and (fn > 0 or not report_fn_only):
                self.write_html_report_entry(label, predict, label_array, predict_array)
            self.result.n_samples += 1
        precision = total_tp / (total_tp + total_fp + 1e-8)
        recall = total_tp / (total_tp + total_fn + 1e-8)
        f1 = 2 * precision * recall / (precision + recall + 1e-8)
        self.result.precision = precision
        self.result.recall = recall
        self.result.f1 = f1
        self.result.label_error_rate = self.result.n_label_error_chars / self.result.n_chars
        self.result.predict_error_rate = self.result.n_predict_error_chars / self.result.n_chars
        self.print_and_write_json_report()
        self.write_html_report_tail()
        return self.result
