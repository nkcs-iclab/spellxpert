import fire
import pathlib

import csc


def main(
        verification_outputs: str,
        verification_output_template: int,
        csc_outputs: str,
        csc_output_template: int,
        run_name: str | None = None,
        report_root: str = '../../reports/verification',
):
    verification_outputs = pathlib.Path(verification_outputs)
    if run_name is None:
        run_name = verification_outputs.parent.stem
    report_path = pathlib.Path(report_root) / run_name
    report_path.mkdir(parents=True, exist_ok=True)

    verification_output_template = csc.evaluation.templates[verification_output_template]
    csc_output_template = csc.evaluation.templates[csc_output_template]
    verification_outputs = csc.load_file(verification_outputs)
    csc_outputs = csc.load_file(csc_outputs)
    grouped_csc_outputs = {}
    for item in csc_outputs:
        prompt = csc_output_template.clean_prompt(item['prompt'])
        if prompt not in grouped_csc_outputs:
            grouped_csc_outputs[prompt] = []
        grouped_csc_outputs[prompt].append(item)
    final_output = []
    for item in verification_outputs:
        verification_result = verification_output_template.clean_predict(item['predict'])
        if verification_result == 'B':
            final_output.extend(grouped_csc_outputs[item['prompt'].split('\n句子A：')[1].split('\n句子B：')[0]])
    with (report_path / 'final.jsonl').open('w', encoding='utf-8') as f:
        for item in final_output:
            f.write(csc.prettify(item, indent=None) + '\n')


if __name__ == '__main__':
    fire.Fire(main)
