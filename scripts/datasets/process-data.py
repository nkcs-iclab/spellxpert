import fire
import json
import pathlib
import deepmerge

import csc


def main(
        dataset_config: str,
        template: int,
        variant: str | None = None,
        train_test_split: float | None = None,
        input_root: str = '../..',
        output_root: str = '../../datasets/processed',
):
    dataset_config = json.loads(pathlib.Path(dataset_config).read_text())
    if variant:
        dataset_config = deepmerge.always_merger.merge(dataset_config, dataset_config['variants'][variant])
    dataset_config['files']['root'] = pathlib.Path(input_root) / dataset_config['files']['root']
    dataset_class = csc.datasets.datasets[dataset_config['name']](dataset_config)
    dataset_class.load_data(template)
    dataset_class.split_data(train_test_split)
    dataset_class.save_data(output_root, variant)


if __name__ == '__main__':
    fire.Fire(main)
