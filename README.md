# SpellXpert

![version-0.0.1](https://img.shields.io/badge/version-0.0.1-blue)
![python->=3.10,<3.13](https://img.shields.io/badge/python->=3.10,<3.13-blue?logo=python&logoColor=white)

## Model

You can download the SpellXpert model from our [Hugging Face](https://huggingface.co/SpellXpert/SpellXpert) repository.

## Dataset

All datasets can be found at
this [Google Drive](https://drive.google.com/drive/folders/1FV57aTYTlUlgqH-YLs-g0WuX_HcxZ_GB?usp=sharing) link.

## SpellXpert Pipeline

### 1. Make your own Llama-Factory compatible dataset

#### 1.1. Create a config file under `configs/datasets/` directory.

Example config file:

```json
{
  "name": "cscd-ns",
  "root": "datasets/original/cscd-ns",
  "files": {
    "train": "train.tsv",
    "valid": "dev.tsv",
    "test": "test.tsv",
    "all": "all.tsv"
  }
}
```

#### 1.2. Create the dataset processing module under `csc/data/datasets/` directory.

#### 1.3. Create the dataset processing script under `scripts/datasets/` directory.

The dataset creation script is located in the `scripts/datasets` directory.

Example dataset processing script:

```bash
python detection.py \
   --dataset-config=../../configs/datasets/cscd-ns.json \
   --template=3 \  # Template 3 is the best performing input template for SpellXpert
   --variant=reasoning \  # Allow SpellXpert to reason about the input
   --input-root=...
```

#### 1.4. Add the dataset to `dataset_info.json`, which is used by Llama-Factory to load the dataset.

Example entry in `dataset_info.json`:

```json
{
  "cscd_ns": {
    "file_name": "cscd-ns/template-3/reasoning-test.jsonl",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  }
}
```

### 2. Run vLLM inference

The inference script is located in the `scripts/inference` directory.
The `vllm-infer.py` script is deviated from Llama-Factory's `vllm_infer.py` script to support the SpellXpert dataset
format and cascade verification.
You have to install Llama-Factory and vLLM first to run the inference script.

Example command to run vLLM inference:

```bash
model_name_or_path=...
dataset_dir=...  # Path to the directory where the `dataset_info.json` file is located
template=deepseek3
cutoff_len=13312
max_new_tokens=4096
dataset=cscd_ns  # Replace with your dataset name (defined in `dataset_info.json`)

python vllm-infer.py \
   --model_name_or_path=${model_name_or_path} \
   --dataset=${dataset} \
   --dataset_dir=${dataset_dir} \
   --template=${template} \
   --cutoff_len=${cutoff_len} \
   --max_new_tokens=${max_new_tokens} \
   --save_name=generated_predictions.jsonl \  # Change this to your desired output file path
   --n 8  # Number of output candidates to generate for each input
```

### 3. Collect and filter results using the cascade verification module

#### 3.1. Build your own vocabulary/dictionary

Make your own vocabulary/dictionary by creating a text file with one word/phrase per line.
Put the file in the `scripts/evaluation/dictionaries` directory.

#### 3.2. Run the cascade verification script (stage 1)

In `scripts/evaluation` directory, run:

```bash
python evaluate.py \
   --path=generated_predictions.jsonl \  # Path to the generated predictions file from the inference step
   --template=1 \  # Template 1 is the best performing output template for SpellXpert
   --run_name=your_run_name \  # Name of the run, used for saving results
   --filter_output_label_whitelist_path='["dictionaries/whitelist.txt"]' \  # Path(s) to the dictionary file(s)
   --filter_output_predict_whitelist_path='["dictionaries/whitelist.txt"]' \  # Path(s) to the dictionary file(s)
   --filter_output_context_path=../../datasets/context/cscd-ns/reasoning-context.pkl
```

Note that the context file is optionally created in step 1.2.
Usually, it is the article where the input sentence is extracted from.

The stage 1 output is presented in `<project root>/reports/evaluation/<run name>/` directory.

#### 3.3. Extract the verification dataset for verification stage 2

In `scripts/verification` directory, run:

```bash
python extract-verification-dataset.py \
   --path=../../reports/evaluation/<run_name>/extract-output-FP-TP.jsonl
```

The verification dataset will be saved in the `datasets/run` folder.
An entry will be automatically added to the `datasets/run/dataset_info.json` file for the verification dataset.

#### 3.4. Use vLLM to run inference on the verification dataset

The inference script is located in the `scripts/inference` directory.

Example command to run vLLM inference:

```bash
model_name_or_path=...  # Path to any open-source LLM model, e.g., `deepseek3`
dataset_dir=...  # Path to the directory where the `dataset_info.json` file is located
template=deepseek3  # Change this according to your model
cutoff_len=13312
max_new_tokens=4096
dataset=...  # Replace with your dataset name (defined in `dataset_info.json`)

python vllm-infer.py \
   --model_name_or_path=${model_name_or_path} \
   --dataset=${dataset} \
   --dataset_dir=${dataset_dir} \
   --template=${template} \
   --cutoff_len=${cutoff_len} \
   --max_new_tokens=${max_new_tokens} \
   --save_name=generated_predictions.jsonl \  # Change this to your desired output file path
   --n 1  # Use 1 for verification stage 2
```

#### 3.5. Run the cascade verification script (stage 2)

In `scripts/verification` directory, run:

```bash
python verify.py \
   --verification-outputs=generated_predictions.jsonl \  # Path to the generated predictions file from the inference step 3.4
   --verification-output-template=1 \  # Template 1 is the best performing output template for SpellXpert'
   --csc-outputs=../../reports/evaluation/<run name>/extract-output-FP-TP.jsonl \  # Path to the output file from stage 1
   --csc-output-template=1 \  # Template 1 is the best performing output template for SpellXpert
   --run_name=your_run_name  # Name of the run, used for saving results
```

The stage 2 output is presented in `<project root>/reports/verification/<run name>/` directory.

This is the final output of the SpellXpert pipeline.
All detected errors are marked with `<csc></csc>` tags in the output text.
