import re
import abc
import pathlib
import dataclasses

import csc


@dataclasses.dataclass
class HTMLReportConfig:
    enabled: bool = True
    filter: csc.report.Filter | None = csc.report.Filter.FN


@dataclasses.dataclass
class JSONReportConfig:
    enabled: bool = True


@dataclasses.dataclass
class ExtractionConfig:
    enabled: bool = True
    filter: csc.report.Filter | None = csc.report.Filter.FN
    mode: csc.report.OutputMode = csc.report.OutputMode.JSONL


@dataclasses.dataclass
class FilterConfig:
    enabled: bool = False
    whitelist: set[str] = dataclasses.field(default_factory=set)


@dataclasses.dataclass
class EvaluationConfig:
    report_path: str | pathlib.Path
    html_report: HTMLReportConfig = dataclasses.field(default_factory=HTMLReportConfig)
    json_report: JSONReportConfig = dataclasses.field(default_factory=JSONReportConfig)
    extract_output: ExtractionConfig = dataclasses.field(default_factory=ExtractionConfig)
    filter_output: FilterConfig = dataclasses.field(default_factory=FilterConfig)

    def __post_init__(self):
        self.report_path = pathlib.Path(self.report_path)


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


class Template(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def eval_one(cls, label: str, predict: str) -> tuple[int, int, int, list[bool], list[bool]]:
        raise NotImplementedError

    @classmethod
    def clean_prompt(cls, prompt: str) -> str:
        return prompt

    @classmethod
    def clean_label(cls, label: str) -> str:
        return label

    @classmethod
    def clean_predict(cls, predict: str) -> str:
        return predict

    @classmethod
    def filter_text(cls, text: str, whitelist: set[str]) -> str:
        for char in whitelist:
            text = text.replace(char, '')
        return text


class Template0(Template):
    """
    For training template 1
    """
    opening_tag = '<csc>'
    closing_tag = '</csc>'

    @classmethod
    def mark_errors(cls, string) -> list[bool]:
        is_error = []
        pattern = re.compile(rf'{cls.opening_tag}(.?){cls.closing_tag}')
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

    @classmethod
    def clean_prompt(cls, prompt: str) -> str:
        return prompt.split('user\n')[-1].split('<|im_end|>\n<|im_start|>assistant\n')[0].split('\nassistant\n')[0]

    @classmethod
    def eval_one(cls, label: str, predict: str) -> tuple[int, int, int, list[bool], list[bool]]:
        tp, fp, fn = 0, 0, 0
        label_array = cls.mark_errors(label)
        predict_array = cls.mark_errors(predict)
        if label == '':
            # No labels provided. Assuming all predictions are correct.
            return sum(predict_array), 0, 0, label_array, predict_array
        if len(label_array) != len(predict_array):
            # Dealing with the situation where there are more punctuation marks at the end of the sentence
            if len(label_array) - len(predict_array) == 1:
                label_array = label_array[:-1]
            elif len(predict_array) - len(label_array) == 1:
                predict_array = predict_array[:-1]
            # If the lengths are inconsistent, it is considered that all the wrong characters have not been found
            else:
                return 0, 0, sum(label_array), label_array, [False] * len(label_array)
        for i in range(len(label_array)):
            if label_array[i] == 1 and predict_array[i] == 1:
                tp += 1
            elif label_array[i] == 0 and predict_array[i] == 1:
                fp += 1
            elif label_array[i] == 1 and predict_array[i] == 0:
                fn += 1
        return tp, fp, fn, label_array, predict_array

    @classmethod
    def filter_text(cls, text: str, whitelist: set[str]) -> str:
        text_array = cls.mark_errors(text)
        text_without_tags = text.replace(cls.opening_tag, '').replace(cls.closing_tag, '')
        for i in range(len(text_array)):
            if text_array[i]:
                whitelisted = False
                for context_len in range(0, 7):
                    if i - context_len >= 0:
                        context = text_without_tags[i - context_len:i + 1]
                        if context in whitelist:
                            whitelisted = True
                            break
                    if i + context_len < len(text_array):
                        context = text_without_tags[i:i + context_len + 1]
                        if context in whitelist:
                            whitelisted = True
                            break
                if whitelisted:
                    text_array[i] = False
        text = ''
        for should_mark, char in zip(text_array, text_without_tags):
            if should_mark:
                text += f'{cls.opening_tag}{char}{cls.closing_tag}'
            else:
                text += char
        return text


class Template1(Template0):
    """
    Suitable for `deepseek3` template
    Uses vLLM for inference
    For training template 3
    """

    @classmethod
    def clean_prompt(cls, prompt: str) -> str:
        return prompt.split('待检查的句子：\n\n\n')[-1].split('<｜Assistant｜>')[0]

    @classmethod
    def clean_label(cls, label: str) -> str:
        return label.split('<｜end▁of▁sentence｜>')[0]

    @classmethod
    def clean_predict(cls, predict: str) -> str:
        if '\n</think>\n\n' not in predict:
            return ''
        return predict.split('\n</think>\n\n')[-1]

    @classmethod
    def clean_reasoning(cls, predict: str) -> str:
        if '\n</think>\n\n' not in predict:
            return ''
        return predict.split('<think>\n')[-1].split('\n</think>\n\n')[0]


templates = [
    Template0,
    Template1,
]


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
        self.reports = csc.report.ReportManager(self.config)

    def eval(self, data: list[dict]) -> EvaluationResult:
        if not self.reports.init():
            return self.result
        self.reports.write_head()

        total_tp, total_fp, total_fn = 0, 0, 0
        self.result.char_statistics.n_total = 0
        self.result.sample_statistics.n_total = 0
        has_label = False
        for item in data:
            prompt = self.template.clean_prompt(item['prompt'])
            label = self.template.clean_label(item['label'])
            predict = self.template.clean_predict(item['predict'])
            if self.config.filter_output.enabled:
                label = self.template.filter_text(label, self.config.filter_output.whitelist)
                predict = self.template.filter_text(predict, self.config.filter_output.whitelist)
            self.result.char_statistics.n_total += len(prompt)
            self.result.sample_statistics.n_total += 1

            tp, fp, fn, label_array, predict_array = self.template.eval_one(label, predict)
            total_tp += tp
            total_fp += fp
            total_fn += fn

            has_label |= len(label_array)
            self.result.char_statistics.label.n_error = add(
                self.result.char_statistics.label.n_error,
                sum(label_array),
            )
            self.result.sample_statistics.label.n_error = add(
                self.result.sample_statistics.label.n_error,
                sum(label_array) > 0,
            )
            self.result.char_statistics.predict.n_error = add(
                self.result.char_statistics.predict.n_error,
                sum(predict_array),
            )
            self.result.sample_statistics.predict.n_error = add(
                self.result.sample_statistics.predict.n_error,
                sum(predict_array) > 0,
            )

            self.reports.write_entry(
                tp=tp,
                fp=fp,
                fn=fn,
                length=len(label_array),
                item=item,
                template=self.template,
                label_array=label_array,
                predict_array=predict_array,
            )

        if has_label:
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

        self.reports.write_tail(self.result)
        return self.result
