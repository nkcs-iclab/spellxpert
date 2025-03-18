import fire
import pathlib

import csc

FN = csc.report.Filter.FN
FP = csc.report.Filter.FP
TP = csc.report.Filter.TP
TN = csc.report.Filter.TN
JSONL = csc.report.OutputMode.JSONL
CLEANED_JSONL = csc.report.OutputMode.CLEANED_JSONL
HUMAN_READABLE = csc.report.OutputMode.HUMAN_READABLE
PLAIN_TEXT = csc.report.OutputMode.PLAIN_TEXT


def main(
        path: str,
        template: int,
        report_root: str = '../../reports/evaluation',
        html_report_enabled: bool = True,
        html_report_filter: str | None = 'FN',
        json_report_enabled: bool = True,
        extract_output_enabled: bool = True,
        extract_output_filter: str | None = 'TP | FP',
        extract_output_mode: str = 'JSONL | CLEANED_JSONL | HUMAN_READABLE | PLAIN_TEXT',
        filter_output_enabled: bool = True,
        filter_output_black_list_path: str = 'black-list.txt',
):
    path = pathlib.Path(path)
    config = csc.evaluation.EvaluationConfig(report_path=pathlib.Path(report_root) / path.parent.stem)
    config.html_report.enabled = html_report_enabled
    config.html_report.filter = eval(html_report_filter) if html_report_filter is not None else None
    config.json_report.enabled = json_report_enabled
    config.extract_output.enabled = extract_output_enabled
    config.extract_output.filter = eval(extract_output_filter) if extract_output_filter is not None else None
    config.extract_output.mode = eval(extract_output_mode)
    config.filter_output.enabled = filter_output_enabled
    if filter_output_enabled:
        filter_output_black_list = csc.load_file(filter_output_black_list_path)
        config.filter_output.black_list = filter_output_black_list
    data = csc.load_file(path)
    metric = csc.evaluation.Metric(config, template)
    result = metric.eval(data)
    print(csc.prettify(csc.dataclass_to_cleaned_dict(result)))


if __name__ == '__main__':
    fire.Fire(main)
