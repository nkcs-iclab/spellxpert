import fire

import csc


def main(
        path: str,
        run_name: str | None = None,
        output_root: str = '../../datasets/run',
):
    dataset = csc.verification.Dataset(path, run_name=run_name)
    dataset.load_data()
    dataset.get_corrected_samples()
    dataset.convert_samples_to_dataset_items()
    dataset.save_data(output_root)


if __name__ == '__main__':
    fire.Fire(main)
