import fire
import pathlib
import dataclasses

import csc


@dataclasses.dataclass
class EvalInfo:
    name: str
    model_name_or_path: str
    finetuning_type: str
    checkpoint_path: str
    dataset_dir: str
    dataset: str
    comment: str
    cutoff_len: int
    max_samples: int
    batch_size: int
    max_new_tokens: int
    top_p: float
    temperature: float
    output_dir: str


@dataclasses.dataclass
class TrainInfo:
    name: str
    model_name_or_path: str
    finetuning_type: str
    checkpoint_path: str
    stage: str
    dataset_dir: str
    dataset: str
    learning_rate: float
    num_train_epochs: float
    max_grad_norm: float
    max_samples: int
    compute_type: str
    cutoff_len: int
    batch_size: int
    gradient_accumulation_steps: int
    lr_scheduler_type: str
    logging_steps: int
    save_steps: int
    warmup_steps: int
    optim: str
    packing: bool
    freeze_trainable_modules: str
    lora_rank: int
    lora_alpha: int
    lora_dropout: float
    use_dora: bool
    output_dir: str
    ds_stage: int
    ds_offload: bool


def extract_train_info(path: pathlib.Path) -> str:
    if not (config := path / 'llamaboard_config.yaml').exists():
        print('No llamaboard_config.yaml found. Maybe this training was run without llamaboard?')
        return path.name
    config = csc.datasets.utils.load_data_from_file(config)
    args = csc.datasets.utils.load_data_from_file(path / 'training_args.yaml')
    train_info = TrainInfo(
        name=pathlib.Path(args['output_dir']).name,
        model_name_or_path=pathlib.Path(args['model_name_or_path']).name,
        finetuning_type=args['finetuning_type'],
        checkpoint_path=','.join(config['top.checkpoint_path']),
        stage=args['stage'],
        dataset_dir=args['dataset_dir'],
        dataset=','.join(config['train.dataset']),
        learning_rate=args['learning_rate'],
        num_train_epochs=args['num_train_epochs'],
        max_grad_norm=args['max_grad_norm'],
        max_samples=args['max_samples'],
        compute_type=config['train.compute_type'],
        cutoff_len=args['cutoff_len'],
        batch_size=args['per_device_train_batch_size'],
        gradient_accumulation_steps=args['gradient_accumulation_steps'],
        lr_scheduler_type=args['lr_scheduler_type'],
        logging_steps=args['logging_steps'],
        save_steps=args['save_steps'],
        warmup_steps=args['warmup_steps'],
        optim=args['optim'],
        packing=args['packing'],
        freeze_trainable_modules=config['train.freeze_trainable_modules'],
        lora_rank=args['lora_rank'],
        lora_alpha=args['lora_alpha'],
        lora_dropout=args['lora_dropout'],
        use_dora=config['train.use_dora'],
        output_dir=args['output_dir'],
        ds_stage=config['train.ds_stage'],
        ds_offload=config['train.ds_offload'],
    )
    string = '\t'.join(map(str, dataclasses.asdict(train_info).values()))
    print(string)
    return string


def extract_eval_info(path: pathlib.Path) -> str:
    if not (config := path / 'llamaboard_config.yaml').exists():
        print('No llamaboard_config.yaml found. Maybe this evaluation was run without llamaboard?')
        return path.name
    config = csc.datasets.utils.load_data_from_file(config)
    args = csc.datasets.utils.load_data_from_file(path / 'training_args.yaml')
    eval_info = EvalInfo(
        name=pathlib.Path(args['output_dir']).name,
        model_name_or_path=pathlib.Path(args['model_name_or_path']).name,
        finetuning_type=args['finetuning_type'],
        checkpoint_path=','.join(config['top.checkpoint_path']),
        dataset_dir=args['dataset_dir'],
        dataset=','.join(config['eval.dataset']),
        comment='',
        cutoff_len=args['cutoff_len'],
        max_samples=args['max_samples'],
        batch_size=args['per_device_eval_batch_size'],
        max_new_tokens=args['max_new_tokens'],
        top_p=args['top_p'],
        temperature=args['temperature'],
        output_dir=args['output_dir'],
    )
    string = '\t'.join(map(str, dataclasses.asdict(eval_info).values()))
    print(string)
    return string


def main(*path: str):
    strings = []
    for path in path:
        path = pathlib.Path(path)
        if path.name.startswith('train'):
            strings.append(extract_train_info(path))
        elif path.name.startswith('eval'):
            strings.append(extract_eval_info(path))
        else:
            raise ValueError(f'Unknown path: {path}')
    pathlib.Path('entries.txt').write_text('\n'.join(strings))


if __name__ == '__main__':
    fire.Fire(main)
