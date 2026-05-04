import streamlit as st
from transformers import T5ForConditionalGeneration, T5Tokenizer
from utils.post_processing import trim_incomplete_sentence

REPO_ID = "Jason2608/indot5-fin-summarize"
SUMMARIZE_PREFIX = "ringkas: "

MAX_INPUT_LENGTH  = 512
MAX_NEW_TOKENS    = 300   
MIN_NEW_TOKENS    = 50


@st.cache_resource(show_spinner="⏳ Memuat model IndoT5, harap tunggu...")
def load_model():
    tokenizer = T5Tokenizer.from_pretrained(REPO_ID)
    model     = T5ForConditionalGeneration.from_pretrained(REPO_ID)
    model.eval()
    return tokenizer, model


def summarize(text: str) -> str:
    tokenizer, model = load_model()

    input_text = SUMMARIZE_PREFIX + text

    inputs = tokenizer(
        input_text,
        return_tensors="pt",
        max_length=MAX_INPUT_LENGTH,
        truncation=True,
        padding=False,
    )

    output_ids = model.generate(
        inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        max_new_tokens=MAX_NEW_TOKENS,
        min_new_tokens=MIN_NEW_TOKENS,
        num_beams=4,
        early_stopping=False,         
        no_repeat_ngram_size=3,
        length_penalty=1.3,
    )

    raw_result = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    result = trim_incomplete_sentence(raw_result)
    return result