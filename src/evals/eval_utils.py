from typing import Dict, List

import enum
import re
import torch
import tqdm
import transformer_lens.utils as utils

class ModelType(enum.Enum):
    """Determines what type of model we should use, which determines how we run inference."""
    TRANSFORMER_LENS = 'TransformerLens'
    HUGGINGFACE = 'HuggingFace'


def get_spelling(word: str, separator: str, case="upper"):
    """Get the spelling of a word with a given separator and case. e.g, hello -> H-E-L-L-O"""
    case_map = {"upper": lambda x: x.upper(), "lower": lambda x: x.lower(), "original": lambda x: x}
    return separator.join([char if case not in case_map else case_map[case](char) for char in word])


def run_inference_on_model(model, model_type: ModelType, tokenizer, prompts: List[str], answers: List[str], batch_size: int) -> List[Dict]:
    """Run inference on a model with a given tokenizer and device.
    This function is designed to be eval-agnostic, so it doesn't judge or format the answers for you.
    
    In order for the 'word' field to be populated in the returned data, the prompt must contain the word to be examined
    as the last item in single quotes. e.g, "Spell 'hello'." or "Spell 'goodbye'." We use a regex to search for it at the moment.
    
    Args:
    model: Contains the HuggingFace or TransformerLens model to run inference on.
    model_type: Determines how we run inference. Either HuggingFace or TransformerLens.
    tokenizer: Contains the tokenizer to apply to prompts.
    prompts: A list of prompts to pass into the model.
    answers: A list of answers the model should output.
    batch_size: How many prompts to pass in at once to the model
    
    Returns:
    An object containing a list of {'word': str, 'prompt': str, 'answer': str, 'response': str, 'formatted_response': str} dicts,
    where response is the model's output as a string. formatted_response = response, since this function is eval-agnostic.
    """
    num_batches = (len(prompts) + batch_size - 1) // batch_size
    data = []

    for i in tqdm.tqdm(range(num_batches)):
        start_index = i * batch_size
        end_index = min(len(prompts), start_index + batch_size)

        if model_type == ModelType.HUGGINGFACE:
            responses = run_huggingface_inference(model, tokenizer, prompts[start_index:end_index], answers[start_index:end_index])
        elif model_type == ModelType.TRANSFORMER_LENS:
            responses = run_transformerlens_inference(model, prompts[start_index:end_index], answers[start_index:end_index])
        
        for i, response in enumerate(responses):
            data.append({'word': get_word_from_prompt(prompts[start_index + i]),
                        'prompt': prompts[start_index + i],
                         'answer': answers[start_index + i], 
                         'response': response,
                         'formatted_response': response}) # formatted_response is populated by specific evaluation functions.
    
    return data

def run_huggingface_inference(model, tokenizer, prompts: List[str], answers: List[str], temperature=0.0):
    """Pass in a list of prompts with a HuggingFace model, and get a list of responses back."""
    inputs = tokenizer(prompts, padding=True, truncation=True, return_tensors="pt").to(model.device)
        
    max_batch_tokens = max([len(tokenizer.encode(ans, add_special_tokens=False))+1 for ans in answers])
    if temperature > 0:
        outputs = model.generate(**inputs, max_new_tokens=max_batch_tokens, num_return_sequences=1, temperature=temperature, do_sample=True)
    else:
        outputs = model.generate(**inputs, max_new_tokens=max_batch_tokens, num_return_sequences=1, do_sample=False)
    responses = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]
    return responses


def run_transformerlens_inference(model, prompts: List[str], answers: List[str], temperature=0.0):
    """Pass in a list of prompts with a TransformerLens model, and get a list of responses back."""
    max_batch_tokens = max([(model.to_tokens(ans).shape[-1]) for ans in answers]) + 1
    tokens = [model.to_tokens(prompt) for prompt in prompts]
    max_length = max([token.shape[-1] for token in tokens])
    eos_token = model.to_tokens(model.tokenizer.eos_token, prepend_bos=False).item()

    # Pads on the left by an amount of tokens equal to the max length token - length of this token.
    tokens = [torch.cat((torch.full((max_length - token.shape[-1],), eos_token, dtype=torch.long).to(utils.get_device()), 
                         torch.as_tensor(token).to(utils.get_device()).squeeze(0))) for token in tokens]
    tokens = torch.stack(tokens)
    outputs = model.generate(tokens, max_new_tokens=max_batch_tokens, temperature=temperature)
    return model.to_string(outputs)


def get_word_from_prompt(prompt: str) -> str:
    """Get the word the model is being asked to spell from a prompt."""
    matches = re.findall(r"'([^']*)'", prompt) # Find all substrings in single quotes.
    return matches[-1] if matches else '' # Then return the last one.


def get_accuracy(outputs: List[str], answers: List[str]):
    """Get the accuracy of a model's outputs compared to a list of answers.
    Works as a generic accuracy check if you're not looking for something in particular."""
    return sum([1 if outputs[i] == answers[i] else 0 for i in range(len(outputs))]) / len(outputs)
