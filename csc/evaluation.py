import re
import enum
import pathlib
import dataclasses

import csc

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
class EvaluationResult:
    @dataclasses.dataclass
    class Metric:
        recall: float | None = None
        precision: float | None = None
        f1: float | None = None

    @dataclasses.dataclass
    class Statistic:
        @dataclasses.dataclass
        class InnerStatistic:
            n_error: int | None = None
            error_rate: float | None = None

        n_total: int | None = None
        label: InnerStatistic = dataclasses.field(default_factory=InnerStatistic)
        predict: InnerStatistic = dataclasses.field(default_factory=InnerStatistic)

    metrics: Metric = dataclasses.field(default_factory=Metric)
    char_statistics: Statistic = dataclasses.field(default_factory=Statistic)
    sample_statistics: Statistic = dataclasses.field(default_factory=Statistic)


class Template:

    @classmethod
    def eval_one(cls, label: str, predict: str) -> tuple[int, int, int, list[bool], list[bool]]:
        raise NotImplementedError

    @classmethod
    def html_csc_pair(cls, label: str, label_array: list[bool], predict_array: list[bool]) -> str:
        raise NotImplementedError


class Template0(Template):
    opening_tag = '<csc>'
    closing_tag = '</csc>'

    @classmethod
    def eval_one(cls, label: str, predict: str) -> tuple[int, int, int, list[bool], list[bool]]:
        tp, fp, fn = 0, 0, 0
        label_array = mark_errors(label, cls.opening_tag, cls.closing_tag)
        predict_array = mark_errors(predict, cls.opening_tag, cls.closing_tag)
        if len(label_array) != len(predict_array):
            # Dealing with the situation where there are more punctuation marks at the end of the sentence
            if len(label_array) - len(predict_array) == 1:
                label_array = label_array[:-1]
            elif len(predict_array) - len(label_array) == 1:
                predict_array = predict_array[:-1]
            # If the lengths are inconsistent, it is considered that all the wrong characters have not been found
            else:
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
    def html_csc_pair(cls, label: str, label_array: list[bool], predict_array: list[bool]) -> str:
        label_chars = label.replace(cls.opening_tag, '').replace(cls.closing_tag, '')
        if not (len(label_chars) == len(label_array) == len(predict_array)):
            return ''
        output_string = []
        for b_label, b_predict, c_label in zip(label_array, predict_array, label_chars):
            if b_label == 1 and b_predict == 1:
                output_string.append(f'<span class="tp">{c_label}</span>')
            elif b_label == 0 and b_predict == 1:
                output_string.append(f'<span class="fp">{c_label}</span>')
            elif b_label == 1 and b_predict == 0:
                output_string.append(f'<span class="fn">{c_label}</span>')
            else:
                output_string.append(c_label)
        return f'<div class="csc-pair">{''.join(output_string)}</div>\n'


class Template1(Template0):
    """
    Suitable for `deepseek3` template. Uses vLLM for inference.
    """

    @staticmethod
    def _remove_special_tokens(label: str | None = None, predict: str | None = None) -> tuple[str | None, str | None]:
        if label is not None:
            label = label.split('<｜end▁of▁sentence｜>')[0]
        if predict is not None:
            predict = predict.split('</think>\n\n')[-1]
        return label, predict

    @classmethod
    def eval_one(cls, label: str, predict: str) -> tuple[int, int, int, list[bool], list[bool]]:
        # if '</think>' not in predict:
        #     # If the </think> tag is not found, it means the maximum output tokens were reached.
        #     # We will consider the output as correct in this case.
        #     return super().eval_one(label, label)
        label, predict = cls._remove_special_tokens(label, predict)
        return super().eval_one(label, predict)

    @classmethod
    def html_csc_pair(cls, label: str, label_array: list[bool], predict_array: list[bool]) -> str:
        label, predict = cls._remove_special_tokens(label)
        return super().html_csc_pair(label, label_array, predict_array)


templates = [
    Template0,
    Template1,
]


class Filter(enum.IntFlag):
    HAS_FN = enum.auto()
    HAS_FP = enum.auto()
    HAS_TP = enum.auto()
    HAS_TN = enum.auto()


@dataclasses.dataclass
class EvaluationConfig:
    @dataclasses.dataclass
    class HTMLReportConfig:
        enabled: bool = True
        filter: Filter = Filter.HAS_FN

    @dataclasses.dataclass
    class ExtractionConfig:
        enabled: bool = True
        filter: Filter = Filter.HAS_FN

    @dataclasses.dataclass
    class FilterConfig:
        enabled: bool = False

    report_path: str | pathlib.Path
    html_report: HTMLReportConfig = dataclasses.field(default_factory=HTMLReportConfig)
    json_report: bool = True
    extract_output: ExtractionConfig = dataclasses.field(default_factory=ExtractionConfig)
    filter_output: FilterConfig = dataclasses.field(default_factory=FilterConfig)

    def __post_init__(self):
        self.report_path = pathlib.Path(self.report_path)


def add(a, b):
    if a is None:
        if b == 0:
            return None
        return b
    return a + b


class Metric:

    def __init__(self, config: EvaluationConfig, template: int):
        self.config = config
        self.template = templates[template]
        self.result = EvaluationResult()

    def write_html_report_head(self):
        (self.config.report_path / 'index.html').write_text(html_head)

    def write_html_report_tail(self):
        with (self.config.report_path / 'index.html').open('a') as f:
            f.write(html_tail)

    def write_html_report_entry(self, label: str, label_array: list[bool], predict_array: list[bool]):
        with (self.config.report_path / 'index.html').open('a') as f:
            f.write(self.template.html_csc_pair(label, label_array, predict_array))

    @staticmethod
    def should_pick(tp: int, fp: int, fn: int, length: int, filter_: Filter) -> bool:
        status = (
                (Filter.HAS_TP if tp > 0 else 0) |
                (Filter.HAS_FP if fp > 0 else 0) |
                (Filter.HAS_FN if fn > 0 else 0) |
                (Filter.HAS_TN if tp + fn + fp < length else 0)
        )
        return status & filter_ == filter_

    def eval(self, data: list[dict]) -> EvaluationResult:
        if self.config.report_path.exists():
            print(f'Report path {self.config.report_path} already exists. Overwrite? (y/[n])')
            if input().lower() != 'y':
                return self.result
        self.config.report_path.mkdir(parents=True, exist_ok=True)

        if self.config.html_report.enabled:
            self.write_html_report_head()

        total_tp, total_fp, total_fn = 0, 0, 0
        self.result.char_statistics.n_total = 0
        self.result.sample_statistics.n_total = 0
        n_label_chars = 0
        for item in data:
            label, predict = item['label'], item['predict']
            tp, fp, fn, label_array, predict_array = self.template.eval_one(label, predict)
            total_tp += tp
            total_fp += fp
            total_fn += fn
            self.result.char_statistics.n_total += len(label_array) if len(label_array) else len(predict_array)
            n_label_chars += len(label_array)
            self.result.sample_statistics.label.n_error = add(
                self.result.sample_statistics.label.n_error,
                sum(label_array) > 0,
            )
            self.result.char_statistics.label.n_error = add(
                self.result.char_statistics.label.n_error,
                sum(label_array),
            )
            self.result.sample_statistics.predict.n_error = add(
                self.result.sample_statistics.predict.n_error,
                sum(predict_array) > 0,
            )
            self.result.char_statistics.predict.n_error = add(
                self.result.char_statistics.predict.n_error,
                sum(predict_array),
            )

            if self.config.html_report.enabled:
                if self.should_pick(tp, fp, fn, len(label_array), self.config.html_report.filter):
                    self.write_html_report_entry(label, label_array, predict_array)
            self.result.sample_statistics.n_total += 1

        if n_label_chars > 0:
            precision = total_tp / (total_tp + total_fp + 1e-8)
            recall = total_tp / (total_tp + total_fn + 1e-8)
            f1 = 2 * precision * recall / (precision + recall + 1e-8)
            self.result.metrics.precision = precision
            self.result.metrics.recall = recall
            self.result.metrics.f1 = f1
            self.result.char_statistics.label.error_rate = (
                    self.result.char_statistics.label.n_error / self.result.char_statistics.n_total
            )
            self.result.sample_statistics.label.error_rate = (
                    self.result.sample_statistics.label.n_error / self.result.sample_statistics.n_total
            )

        self.result.char_statistics.predict.error_rate = (
                self.result.char_statistics.predict.n_error / self.result.char_statistics.n_total
        )
        self.result.sample_statistics.predict.error_rate = (
                self.result.sample_statistics.predict.n_error / self.result.sample_statistics.n_total
        )

        if self.config.html_report.enabled:
            self.write_html_report_tail()
        result_string = csc.prettify(csc.dataclass_to_cleaned_dict(self.result))
        print(result_string)
        if self.config.json_report:
            (self.config.report_path / 'result.json').write_text(result_string)

        return self.result
