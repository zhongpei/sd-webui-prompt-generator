import gradio as gr
from scripts.format_prompt import format_prompt
from modules import scripts, script_callbacks, shared
from scripts.translate_prompt import GoogleTranslate, YoudaoTranslate
from scripts.gen_prompt import MODEL_NAME
from scripts.gen_prompt import init_model as gen_init_model

ui_prompts = []
ui_format_prompts = []


def translate_prompt_one(prompt: str) -> str:
    if shared.opts.prompt_generator_zh_translate == "google":
        tp = GoogleTranslate()
        return tp.translate(prompt, output_lang="en")
    if shared.opts.prompt_generator_zh_translate == "youdao":
        tp = YoudaoTranslate()
        return tp.translate(prompt, input_lang=shared.opts.prompt_generator_zh_translate_from, output_lang="en")
    return prompt


def format_prompts(*prompts: list):
    ret = []

    for prompt in prompts:
        if not prompt or prompt.strip() == '':
            ret.append('')
            continue

        prompt = format_prompt(prompt)

        ret.append(prompt)

    return ret


def gen_prompt(*ui_prompts: list):
    model = gen_init_model(
        model_id=shared.opts.prompt_generator_zh_model_id,
        device=shared.opts.prompt_generator_zh_model_device,
        base_dir=scripts.basedir(),
    )
    model.temperature = shared.opts.prompt_generator_zh_temperature

    result_list = []

    for prompt in ui_prompts:

        if not prompt or len(prompt.strip()) == 0:
            result_list.append(prompt)
            print(f"gen prompt(empty): {prompt} --> {prompt}")
            continue

        prompt = prompt.strip()
        prompt = translate_prompt_one(prompt)

        result = model.gen_prompt(prompt)
        if result is None:
            result_list.append(prompt)
            print(f"gen prompt(empty): {prompt} --> {prompt}")
            continue
        result = format_prompt(result)
        result_list.append(result)

        print(f"gen prompt: {prompt} --> {result}")
    print(f"len ui_prompts: {len(ui_prompts)}  : {len(result_list)}")
    if len(ui_prompts) == 1:
        return result_list[0]
    return result_list


def on_before_component(component: gr.component, **kwargs: dict):
    if 'elem_id' in kwargs:
        # print(f"elem_id: {kwargs['elem_id']}")
        if kwargs['elem_id'] in ['txt2img_prompt', 'txt2img_neg_prompt', 'img2img_prompt', 'img2img_neg_prompt']:
            ui_format_prompts.append(component)

        if kwargs['elem_id'] in ['txt2img_prompt', 'img2img_prompt']:
            ui_prompts.append(component)

        if kwargs['elem_id'] == 'paste':
            with gr.Blocks(analytics_enabled=False) as ui_component:
                format_btn = gr.Button(value='F', elem_classes='tool', elem_id='format_prompt')
                format_btn.click(
                    fn=format_prompts,
                    inputs=ui_format_prompts,
                    outputs=ui_format_prompts
                )
                gen_btn = gr.Button(value='G', elem_classes='tool', elem_id='gen_prompt')
                gen_btn.click(
                    fn=gen_prompt,
                    inputs=ui_prompts,
                    outputs=ui_prompts
                )
                return ui_component


SETTINGS_SECTION = ("prompt_generator_zh", "Prompt Generator")


def on_ui_settings():
    model_ids = list(MODEL_NAME.keys())
    shared.opts.add_option(
        "prompt_generator_zh_model_id",
        shared.OptionInfo(
            model_ids[0], "model type", gr.Radio,
            lambda: {"choices": model_ids},
            section=SETTINGS_SECTION
        )
    )
    shared.opts.add_option(
        "prompt_generator_zh_model_device",
        shared.OptionInfo(
            "cuda", "model device", gr.Radio,
            lambda: {"choices": ["cpu", "cuda"]},
            section=SETTINGS_SECTION
        )
    )
    shared.opts.add_option(
        "prompt_generator_zh_translate",
        shared.OptionInfo(
            "youdao", "translate prompt to english", gr.Radio,
            lambda: {"choices": ["none", "google", "youdao"]},
            section=SETTINGS_SECTION
        )
    )
    shared.opts.add_option(
        "prompt_generator_zh_translate_from",
        shared.OptionInfo(
            "zh-CN", "translate from lagrange", gr.Radio,
            lambda: {"choices": ["zh-CN", "ja", "ru"]},
            section=SETTINGS_SECTION
        )
    )
    shared.opts.add_option(
        "prompt_generator_zh_temperature",
        shared.OptionInfo(
            0.6, "generator temperature (higher more random)", gr.Slider,
            lambda: {"maximum": 1.0, "minimum": 0.1, "step": 0.05},
            section=SETTINGS_SECTION
        )
    )


script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_before_component(on_before_component)
