import fire

import csc


def main(
        dataset_config: str,
        template: int,
        variant: str | None = None,
        train_test_split: float | None = None,
        input_root: str = '../..',
        output_root: str = '../../datasets/processed',
        context_root: str = '../../datasets/context',
):
    dataset_config = csc.data.utils.load_dataset_config(dataset_config, input_root, variant)
    dataset_class = csc.data.datasets[dataset_config['name']]
    dataset = dataset_class(dataset_config, template, variant)
    dataset.load_data()
    dataset.split_data(train_test_split)
    dataset.save_data(output_root)
    dataset.save_context(context_root)


if __name__ == '__main__':
    fire.Fire(main)
