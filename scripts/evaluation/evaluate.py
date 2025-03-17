import fire
import pathlib

import csc


def main(
        path: str,
        template: int,
        report_root: str = '../../reports/evaluation',
):
    path = pathlib.Path(path)
    config = csc.evaluation.EvaluationConfig(report_path=pathlib.Path(report_root) / path.parent.stem)
    data = csc.load_file(path)
    metric = csc.evaluation.Metric(config, template)
    result = metric.eval(data)
    print(csc.prettify(csc.dataclass_to_cleaned_dict(result)))


if __name__ == '__main__':
    fire.Fire(main)
