import fire
import pathlib

import csc


def main(
        path: str,
        template: int,
        report_root: str = '../../reports/evaluation',
        report_fn_only: bool = False,
):
    path = pathlib.Path(path)
    report_path = pathlib.Path(report_root) / path.parent.stem
    report_path.mkdir(parents=True, exist_ok=True)
    data = csc.datasets.utils.load_data_from_file(path)
    metric = csc.evaluation.DetectionMetric(template, report_path)
    metric.eval(data, report_fn_only=report_fn_only)

if __name__ == '__main__':
    fire.Fire(main)
