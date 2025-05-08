import json
import tqdm
import pathlib

import csc

from csc.data.base import DatasetItem, count_data_length, print_save_log


class Template0:
    opening_tag = '<csc>'
    closing_tag = '</csc>'
    instruction = (
        f'我在下列句子中使用{opening_tag}{closing_tag}标记出了疑似的错别字。'
        f'请帮我判断一下我标记出的错别字是否是真正的错别字。'
        f'如果你觉得某个字不是错别字，则将标记去掉，其他字符原封不动输出。'
        f'例如，输入：今天{opening_tag}添{closing_tag}气不{opening_tag}错{closing_tag}，'
        f'则应该输出：今天{opening_tag}添{closing_tag}气不错。'
        f'不要输出任何其他内容，不要给出解释。\n'
    )

    @classmethod
    def process_string(
            cls,
            original_sentence: str,
            marked_sentences: list[str],
            label: str = '',
            reasoning: str = '',
    ) -> DatasetItem:
        return DatasetItem(
            instruction=cls.instruction,
            input=marked_sentences[0],
            output=label,
        )


class Template1(Template0):
    instruction = (
        f'我在下列句子中使用{Template0.opening_tag}{Template0.closing_tag}标记出了疑似的错别字。'
        f'请帮我判断一下我标记出的错别字是否是真正的错别字。要求如下：\n'
        f'1. 如果你觉得某个字不是错别字，则将标记去掉，其他字符原封不动输出。\n'
        f'2. 如果你觉得某个字是错别字但是我没有标记出来，你也不要新增标记。\n'
        f'3. 不要输出任何其他内容，不要给出解释。\n'
        f'例如，输入：今天{Template0.opening_tag}添{Template0.closing_tag}气不{Template0.opening_tag}错{Template0.closing_tag}，'
        f'则应该输出：今天{Template0.opening_tag}添{Template0.closing_tag}气不错。\n'
    )


class Template2(Template0):
    instruction = (
        f'我在下列JSON中使用{Template0.opening_tag}{Template0.closing_tag}标记出了“originalSentence”中疑似的错别字。'
        f'我给出了多种标注结果，列在“outputs”中。'
        f'请帮我判断一下哪一个输出是最合理、最科学的。'
        f'如果你觉得“outputs”中没有正确答案，也请你选择一个其中最接近的答案。'
        f'请直接将正确答案（带标注）复述出来。'
        f'不要输出任何其他内容，不要给出解释。\n'
    )

    @classmethod
    def process_string(
            cls,
            original_sentence: str,
            marked_sentences: list[str],
            label: str = '',
            reasoning: str = '',
    ) -> DatasetItem:
        return DatasetItem(
            instruction=cls.instruction,
            input=csc.prettify({
                'originalSentence': original_sentence,
                'outputs': marked_sentences,
            }, indent=None),
            output=label,
        )


class Template3(Template0):
    instruction = (
        f'我在下列JSON的“output”中使用{Template0.opening_tag}{Template0.closing_tag}标记出了“originalSentence”中疑似的错别字。'
        f'在“reasoning”中，我给出了思考的过程。'
        f'请根据思考的过程，直接输出修改后的句子。不要多字或少字，不要给出解释或者输出修改后的原句之外的内容。'
    )

    @classmethod
    def process_string(
            cls,
            original_sentence: str,
            marked_sentences: list[str],
            label: str = '',
            reasoning: str = '',
    ) -> DatasetItem:
        return DatasetItem(
            instruction=cls.instruction,
            input=csc.prettify({
                'originalSentence': original_sentence,
                'reasoning': reasoning,
                'output': marked_sentences[0],
            }, indent=None),
            output='',
        )


templates = [
    Template0,
    Template1,
    Template2,
    Template3,
]


class VerificationDataset:

    def __init__(
            self,
            path: str | pathlib.Path,
            input_template: int,
            output_template: int,
            name: str,
            variant: str | None = None,
    ):
        self.path = pathlib.Path(path)
        self.input_template = input_template
        self.output_template = output_template
        self.name = name
        self.variant = variant
        self.data = {}

    def load_data(self):
        data = csc.load_file(self.path)
        input_template = csc.evaluation.templates[self.input_template]
        output_template = templates[self.output_template]
        self.data[csc.TEST] = []
        current_index = -1
        prompt, label = None, None
        predict = []
        reasoning = None
        for item in tqdm.tqdm(data):
            index = item.get('index', -1)
            if index != current_index or index == -1:
                if prompt is not None and predict:
                    predict = list(set(predict))
                    self.data[csc.TEST].append(
                        output_template.process_string(prompt, predict, label, reasoning)
                    )
                prompt = input_template.clean_prompt(item['prompt'])
                label = input_template.clean_label(item['label'])
                predict = []
                current_index = index
            predict.append(input_template.clean_predict(item['predict']))
            reasoning = input_template.clean_reasoning(item['predict'])
        if prompt is not None and predict:
            self.data[csc.TEST].append(
                output_template.process_string(prompt, predict, label, reasoning)
            )

    def save_data(self, root: str | pathlib.Path):
        path = pathlib.Path(root) / self.name
        for key, data in self.data.items():
            self._save_data(data, path, key)

    def _save_data(self, data: list[DatasetItem], path: pathlib.Path, key: str):
        path /= f'template-{self.output_template}'
        path.mkdir(parents=True, exist_ok=True)
        max_input_length, max_full_length = 0, 0
        if self.variant:
            path = path / f'{self.variant}-{key}.jsonl'
        else:
            path = path / f'{key}.jsonl'
        if path.exists():
            print(f'File {path} already exists. Overwrite? (y/[n])')
            if input().lower() != 'y':
                return
        with path.open('w') as file:
            for item in data:
                text = json.dumps(csc.dataclass_to_cleaned_dict(item), ensure_ascii=False) + '\n'
                input_length, full_length = count_data_length(item)
                max_input_length = max(max_input_length, input_length)
                max_full_length = max(max_full_length, full_length)
                file.write(text)
        print_save_log(data, max_input_length, max_full_length, path)
