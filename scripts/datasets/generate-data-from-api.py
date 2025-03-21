import fire
import tqdm
import pathlib
import multiprocessing as mp

from openai import OpenAI
from functools import partial
from concurrent.futures import ProcessPoolExecutor

import csc


def process_item(item: dict, api_key: str, base_url: str) -> dict | None:
    """Process a single item - designed to be run in a separate process"""
    client = OpenAI(api_key=api_key, base_url=base_url)
    instruction = item['instruction']
    input_ = item.get('input')
    label = item['output']
    try:
        reasoning_content, content = generate(instruction, input_, client)
        data = {
            'instruction': instruction,
            'input': input_,
            'output': f'<think>\n{reasoning_content}\n</think>\n\n{content}',
            'extra_info': {
                'reasoning_content': reasoning_content,
                'content': content,
                'label': label,
            },
        }
    except Exception as e:
        print(f"Error processing item: {e}")
        return None
    return data


def generate(instruction: str, input_: str, client) -> tuple[str, str]:
    """Generate inference using the API"""
    response = client.chat.completions.create(
        model='deepseek-r1',
        messages=[
            {
                'role': 'user',
                'content': instruction + '\n' + input_,
            }
        ],
        stream=False
    )
    reasoning_content = response.choices[0].message.reasoning_content
    content = response.choices[0].message.content
    return reasoning_content, content


def main(
        path: str,
        output_path: str,
        api_key: str,
        num_workers: int | None = None,  # Default to number of CPU cores
        skip: int | None = None,
):
    if num_workers is None:
        num_workers = mp.cpu_count()

    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        print('Output file already exists. Overwrite? [y/n]')
        choice = input().strip().lower()
        if choice != 'y':
            return
        output_path.unlink()

    # Read input data
    data = csc.load_file(path)
    if skip:
        data = data[skip:]

    # Create a partial function with fixed arguments
    process_func = partial(
        process_item,
        api_key=api_key,
        base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
    )

    print(f'Starting parallel processing with {num_workers} workers')

    # Process items using ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Use tqdm to show progress
        for item in tqdm.tqdm(
                executor.map(process_func, data),
                total=len(data),
                desc='Processing data'
        ):
            if item is None:
                continue
            # Print result
            tqdm.tqdm.write(csc.prettify(item))
            # Write to file
            with output_path.open('a') as f:
                f.write(csc.prettify(item, indent=None) + '\n')


if __name__ == '__main__':
    fire.Fire(main)
