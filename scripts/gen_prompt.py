import os.path
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from typing import List
from huggingface_hub import hf_hub_download
import re
import torch

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DEVICE_ID = 0 if torch.cuda.is_available() else -1
ui_prompts = []

MODEL_NAME = {
    "normal": 'FredZhang7/distilgpt2-stable-diffusion-v2',
    "anime": 'FredZhang7/anime-anything-promptgen-v2',
}

RE_PERSON_TAG = re.compile(r"(\d\+?girl)|(\d\+?boy)|(\d\+?man)|(\d\+?women)|(\d\+?woman)")


def clean_tags(tags: str, prompt: str) -> str:
    # Make tags more human readable
    if tags.startswith(prompt):
        tags = tags[len(prompt):]

    tags = tags.replace(' ', ', ').replace('_', ' ')

    # Remove "!", "?", ".", "(", ")" from the tags
    tags = re.sub(r"[!.?()]", "", tags)

    # Replace " , " with an empty space
    tags = re.sub(r" , ", " ", tags)

    # Remove any trailing commas
    tags = re.sub(r"^,|,$", "", tags)

    # Strip spaces
    tags = tags.strip()

    # Remove any usernames
    words = tags.split(", ")
    result = []
    for word in words:
        word = word.strip()
        if word == 'v':
            result.append(word)
            continue
        if len(word) < 2:
            continue
        if any(char.isdigit() for char in word) and RE_PERSON_TAG.match(word) is None:
            continue
        result.append(word)

    return prompt + ", " + ", ".join(result)


def torch_clean():
    pass


class Model(object):
    def __init__(self, base_dir: str):
        self.model = None
        self.tokenizer = None
        self.cache = {}
        self.model_name = None
        self.model_id = None
        self.last_result = None
        self.last_prompt = None
        self.base_dir = base_dir
        self.device = DEVICE
        self.device_id = DEVICE_ID
        self._temperature = 0.9

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, value):
        value = min(value, 1.0)
        value = max(0.1, value)
        self._temperature = value

    def local_dir(self, model_name):
        local_model_dir = model_name.split("/")[-1]
        local_dir = os.path.join(self.base_dir, "models", local_model_dir)
        if not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)
        return local_dir

    def download_file(self, model_name, filename, force=False):
        local_dir = self.local_dir(model_name)
        if not os.path.exists(os.path.join(local_dir, filename)) or force:
            print(f"download {filename} ==> {os.path.join(local_dir, filename)}")
            hf_hub_download(repo_id=model_name, filename=filename, local_dir=local_dir, resume_download=True)

    def download_model(self, model_name, force=False):
        local_dir = self.local_dir(model_name)
        # print(f"local dir: {local_dir}")
        for filename in ("model.safetensors", "tokenizer.json", "config.json"):
            if not os.path.exists(os.path.join(local_dir, filename)) or force:
                self.download_file(model_name=model_name, filename=filename)

    def reset_model(self):
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        self.cache = {}
        self.model_name = None
        self.model_id = None
        self.last_result = None
        self.last_prompt = None

    def __add_cache(self, prompt, gen_prompts):
        prompt = prompt.strip()
        self.cache.setdefault(prompt, []).extend(gen_prompts)

    def __get_cache(self, prompt):
        if prompt is None:
            return

        prompt = prompt.strip()
        if len(prompt) == 0:
            return

        gen_prompts = self.cache.get(prompt, None)
        if gen_prompts is not None and len(gen_prompts) > 0:
            return gen_prompts.pop()

    def init_model(self, model_id="anime", device=DEVICE):
        self.device = "cpu" if device == "cpu" else DEVICE
        self.device_id = 0 if device == "cpu" else DEVICE_ID

        self.reset_model()

        model_name = MODEL_NAME.get(model_id)
        self.model_name = model_name
        try:
            self.download_model(model_name)
            self.download_model('distilgpt2')
            self.download_file('distilgpt2', filename="generation_config.json")
            self.download_file('distilgpt2', filename="generation_config_for_text_generation.json")
            self.download_file('distilgpt2', filename="merges.txt")
            self.download_file('distilgpt2', filename="vocab.json")
        except Exception as err:
            print(err)

        self.model_id = model_id

        tokenizer = GPT2Tokenizer.from_pretrained(self.local_dir('distilgpt2'), local_files_only=True)
        tokenizer.add_special_tokens({'pad_token': '[PAD]'})
        model = GPT2LMHeadModel.from_pretrained(self.local_dir(model_name), local_files_only=True).to(self.device)

        self.model = model
        self.tokenizer = tokenizer

    def gen_prompt(self, prompt: str) -> str:
        p = self.__get_cache(prompt)
        if p is not None:
            return p

        if self.last_result == prompt and self.last_prompt is not None:
            p = self.__get_cache(self.last_prompt)
            if p is not None:
                return p

        prompts = self.gen_prompts(prompt=prompt)
        if len(prompts) == 0:
            return prompt

        result = prompts.pop()
        self.last_prompt = prompt
        self.last_result = result
        if len(prompts) > 0:
            self.__add_cache(prompt=prompt, gen_prompts=prompts)
        return result

    def gen_prompts(self, prompt: str) -> List[str]:
        temperature = self._temperature or 0.9  # a higher temperature will produce more diverse results, but with a higher risk of less coherent text
        top_k = 8  # the number of tokens to sample from at each step
        max_length = 80  # the maximum number of tokens for the output of the model
        repitition_penalty = 1.2  # the penalty value for each repetition of a token
        num_return_sequences = 5  # the number of results to generate

        # generate the result with contrastive search
        input_ids = self.tokenizer(prompt, return_tensors='pt').input_ids.to(self.device)
        output = self.model.generate(
            input_ids,
            do_sample=True,
            temperature=temperature,
            top_k=top_k,
            max_length=max_length,
            num_return_sequences=num_return_sequences,
            repetition_penalty=repitition_penalty,
            penalty_alpha=0.6,
            no_repeat_ngram_size=1,
            early_stopping=True,
        )

        prompt_output = []
        for i in range(len(output)):
            p = self.tokenizer.decode(output[i], skip_special_tokens=True, device=self.device_id)
            prompt_output.append(p)

        prompt_output = list(set(prompt_output))

        if self.model_id == "anime":
            prompt_output = [clean_tags(p, prompt=prompt) for p in prompt_output]

        print('\nInput:\n' + 100 * '-')
        print('\033[96m' + prompt + '\033[0m')
        print('\nOutput:\n' + 100 * '-')
        for p in prompt_output:
            print('\033[92m' + p + '\033[0m\n')

        return prompt_output


MODEL: Model | None = None


def init_model(
        model_id: str,
        device: str,
        base_dir: str,
) -> Model:
    global MODEL
    if MODEL is None:
        MODEL = Model(base_dir=base_dir)
        MODEL.init_model(model_id=model_id, device=device)
    elif MODEL.model_id != model_id or MODEL.device != device:
        print(f"reinit model {MODEL.model_id} ==> {model_id}")
        MODEL.reset_model()
        MODEL.init_model(model_id=model_id, device=device)
    return MODEL


if __name__ == "__main__":
    m = Model(base_dir=".")
    m.download_model(MODEL_NAME.get("anime"))
    m.init_model()
    output = m.gen_prompt("1 girl")
    print(output)
