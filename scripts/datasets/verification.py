import fire

import csc


def main(
        path: str,
        input_template: int,
        output_template: int,
        name: str,
        variant: str | None = None,
        output_root: str = '../../datasets/verification',
):
    dataset = csc.data.verification.VerificationDataset(
        path=path,
        input_template=input_template,
        output_template=output_template,
        name=name,
        variant=variant,
    )
    dataset.load_data()
    dataset.save_data(output_root)


if __name__ == '__main__':
    fire.Fire(main)
