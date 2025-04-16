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
        filter_output_label_whitelist_path: list[str] | None = None,
        filter_output_predict_whitelist_path: list[str] | None = None,
        filter_output_context_path: str | None = None,
        filter_output_context_threshold: int = 1,
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
        label_whitelist, predict_whitelist = set(), set()
        if filter_output_label_whitelist_path:
            for label_whitelist_path in filter_output_label_whitelist_path:
                label_whitelist.update(csc.load_file(label_whitelist_path))
        if filter_output_predict_whitelist_path:
            for predict_whitelist_path in filter_output_predict_whitelist_path:
                predict_whitelist.update(csc.load_file(predict_whitelist_path))
        config.filter_output.label_whitelist = label_whitelist
        config.filter_output.predict_whitelist = predict_whitelist
        if filter_output_context_path:
            config.filter_output.context_dict, config.filter_output.query_dict = csc.load_file(filter_output_context_path)
        config.filter_output.context_threshold = filter_output_context_threshold

    data = csc.load_file(path)
    metric = csc.evaluation.Metric(config, template)
    result = metric.eval(data)
    print(csc.prettify(csc.dataclass_to_cleaned_dict(result)))


if __name__ == '__main__':
    fire.Fire(main)
