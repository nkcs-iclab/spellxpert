import fire
import pathlib

import csc


def parse_enum(cls, value: str | None):
    if value is None:
        return None
    options = [v.strip() for v in value.split('|')]
    options = [getattr(cls, v) for v in options]
    result = 0
    for option in options:
        result |= option
    return result


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
        filter_output_whitelist_path: str = 'whitelist.txt',
):
    path = pathlib.Path(path)

    config = csc.evaluation.EvaluationConfig(
        report_path=pathlib.Path(report_root) / path.parent.stem,
        html_report=csc.evaluation.HTMLReportConfig(
            enabled=html_report_enabled,
            filter=parse_enum(csc.report.Filter, html_report_filter),
        ),
        json_report=csc.evaluation.JSONReportConfig(
            enabled=json_report_enabled,
        ),
        extract_output=csc.evaluation.ExtractionConfig(
            enabled=extract_output_enabled,
            filter=parse_enum(csc.report.Filter, extract_output_filter),
            mode=parse_enum(csc.report.OutputMode, extract_output_mode),
        ),
        filter_output=csc.evaluation.FilterConfig(
            enabled=filter_output_enabled,
        )
    )
    if filter_output_enabled:
        config.filter_output.whitelist = csc.load_file(filter_output_whitelist_path)

    data = csc.load_file(path)
    metric = csc.evaluation.Metric(config, template)
    result = metric.eval(data)
    print(csc.prettify(csc.dataclass_to_cleaned_dict(result)))


if __name__ == '__main__':
    fire.Fire(main)
