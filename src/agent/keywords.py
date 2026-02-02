"""
生成课程专业词汇提示词（prof_words）
基于用户输入的课堂主题，使用 LLM 生成技术术语列表
"""
from src.agent.llm import DSV3


KEYWORD_PROMPT = """
<system prompt>
You will be given a course lecture topic. The topic may be written in any language.

Task:
Produce an output in EXACTLY the following style:
1) A single opening sentence: "This lecture discusses ...".
2) A line: "Key technical terms include:"
3) A dense list of technical terms relevant to the topic (comma-separated, line breaks allowed).
4) A final line: "All technical terms should be transcribed accurately using their standard spelling."

CRITICAL RULE:
- The output MUST be written in ENGLISH ONLY.
- Even if the input topic is written in Chinese or any other language, the output must still be in English.

Additional rules:
- Do NOT ask for the transcript.
- Use ONLY the given topic.
- Do NOT write explanations of the terms.
- Generate at least 30 technical terms.
- Include core terms and closely related terms students are expected to know.
- Use standard, academically correct terminology and canonical spelling.
- Avoid duplicates and near-duplicates.

One-shot example:

Input topic:
Transformer architecture

Output:
This lecture discusses large language models and the Transformer architecture.

Key technical terms include:
Transformer architecture, attention mechanism,
self-attention, scaled dot-product attention,
multi-head attention, attention weights,
query, key, value,
encoder, decoder, encoder-decoder architecture,
stacked layers, hidden states,
feed-forward network (FFN),
layer normalization, residual connection,
positional encoding, token embeddings,
subword tokenization, Byte Pair Encoding (BPE),
context window, sequence length,
causal masking, padding mask,
autoregressive generation,
training objective, language modeling loss,
pretraining, fine-tuning, instruction tuning,
parameters, model weights,
inference, decoding, sampling,
softmax, logits,
backpropagation, gradient descent,
large-scale datasets.

All technical terms should be transcribed accurately using their standard spelling.

Now produce the output for this input topic:
</system prompt>
"""


def generate_prof_words(topic: str) -> str:
    """
    根据课堂主题生成专业词汇提示词

    Args:
        topic: 课堂主题（可以是任何语言）

    Returns:
        生成的专业词汇提示词（英文）
    """
    llm = DSV3()

    # 构建完整提示词
    full_prompt = KEYWORD_PROMPT + f"\n<input topic>{topic}</input topic>"

    # 生成专业词汇
    prof_words = llm.generate(full_prompt)

    return prof_words.strip()


if __name__ == "__main__":
    # 测试
    topic = input("请输入课堂主题: ")
    prof_words = generate_prof_words(topic)
    print("\n生成的专业词汇提示词：")
    print("=" * 60)
    print(prof_words)
    print("=" * 60)
