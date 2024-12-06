import fire
import json
import pathlib

import csc


def main(
        dataset_config: str,
        task: str,
        template: int,
        train_test_split: float | None = None,
        input_root: str = '../..',
        output_root: str = '../../datasets/processed',
):
    dataset_config = json.loads(pathlib.Path(dataset_config).read_text())
    dataset_config['files']['root'] = pathlib.Path(input_root) / dataset_config['files']['root']
    dataset_class = csc.datasets.datasets[f'{dataset_config['name']}.{task}'](dataset_config)
    dataset_class.load_data(template)
    dataset_class.split_data(train_test_split)
    dataset_class.save_data(output_root)


if __name__ == '__main__':
    fire.Fire(main)
