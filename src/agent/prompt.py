#llm整理，整理要点，并且对下一个循环输出尾声
promptv1 = """
<system prompt>
This is a STRUCTURING task, not a summarization task.

Rewrite the transcript as if you are preparing clean lecture notes
from spoken classroom audio.

Rules:
- Keep the same information density as the original speech.
- You may remove filler words and repetition.
- You must NOT reduce content to high-level summaries.
- If the speaker is mid-explanation, explicitly mark it as ongoing.

Output strict JSON only.

Instructions:
1) Rewrite the content in clear, grammatically complete written English.
2) Preserve the original meaning and level of detail.
3) Classify content into:
   - coursework (deadlines, exams, grading, policies)
   - knowledge (concepts, mechanisms, formulas)
   - questions (questions, exercises, Q&A)

Chunk boundary handling:
- If a point is fully explained here, put it into "content".
- If the explanation is clearly not finished, put it into "supplement.ongoing".
- If a new topic is mentioned but not developed, put raw text into "supplement.carryover_raw".
<output format>
can only output JSON itself in the following format:
Output format:
{
  "content": { "coursework": [], "knowledge": [], "question": [] },
  "supplement": { "ongoing": [], "carryover_raw": [] }
}
</output format>
</system prompt>
"""
promptv2 = """
<system prompt>
You are a lecture transcript ORGANIZER for streaming classroom audio.

This is a restructuring + rewriting task, NOT summarization.
Your goal is to restate what was said in clear, readable written English while preserving meaning and detail.

Core rules:
- Preserve the original meaning and information density. Do not generalize or compress into high-level summaries.
- You may fix ASR issues (repetitions, stutters, broken sentences), remove filler words, and improve grammar.
- Do NOT add facts that are not present. If something is implied but not stated, keep it uncertain.
- Write for readability: combine related sentences into coherent paragraphs, not one sentence per line.

What to produce:
- Organize the rewritten notes into three buckets:
  1) coursework: homework, exams, deadlines, grading, policies
  2) knowledge: concepts, mechanisms, definitions, formulas
  3) question: questions, exercises, prompts, Q&A

Chunk boundary handling (streaming):
- If a point is fully expressed within this chunk, place the rewritten version in content.
- If the speaker is clearly mid-explanation, place the rewritten partial note in supplement.ongoing and indicate that it continues.
- If a new topic is only mentioned but not developed, put the raw trailing fragment(s) in supplement.carryover_raw for the next chunk.

Output constraints:
- Output STRICT JSON ONLY (no markdown fences, no extra commentary).
- You may use Markdown/LaTeX formatting INSIDE JSON strings to improve readability (e.g., paragraphs, bullet points, $...$ or $$...$$), remember put everything inside JSON strings.

<output format>
can only output JSON itself in the following format:
{
  "content": { "coursework": [], "knowledge": [], "question": [] },
  "supplement": { "ongoing": [], "carryover_raw": [] }
}
</output format>
</system prompt>
"""



#判断噪音
#判断何时截断
# prompt_ctr = """
# <system prompt>
# 你是一个流式文本的切分控制器。你的任务是阅读当前的【文本缓冲区】，判断是否应该立即将内容发送给后台进行知识提取。

# 判断标准：
# 1. **完整性**：当前的缓冲区是否包含了一个完整的逻辑闭环？
# 2. **独立性**：如果现在切分，下一句话是否能独立存在（不严重依赖上文的代词）？
# 3. **话题转变**：讲师是否通过 "Next", "However", "Now" 等词开启了新话题？

# 输出：如果要转发后台进行知识提取，就输出1；否则，输出0
# <output format>
# 请输出 JSON 格式：
# {
#   "action": 1或0
# }
# </output format>
# </system prompt>
# """
# #重新组织语言，输出知识点
# prompt_arr = """
# <system prompt>
# # Role
# 你是一个专业的学术课堂笔记整理专家。你的输入是一段实时的、未经处理的语音识别（ASR）文本流。你的任务是将这些碎片化的口语文本重构为**高密度的知识笔记**。

# # Goal
# 输出结构化的 Markdown 笔记，必须保留所有具体细节（数字、定义、公式、案例），但要去除口语废话和ASR错误。

# # Critical Rules (必须严格遵守)
# 1. **NO SUMMARIZATION (严禁摘要)**：不要写“讲师介绍了...”，不要概括。要**直接陈述**知识本身。
#    - 错误：老师举了一个牛顿定律的例子。
#    - 正确：例如：牛顿第二定律 ($F=ma$) 说明了力与质量的关系。
# 2. **Fact Retention (事实保留)**：保留所有的专有名词、逻辑因果、参数具体的数值。
# 3. **De-noising (强力清洗)**：
#    - 剔除 ASR 幻觉（如重复多次的 "The gradient. The gradient..."，直接删除）。
#    - 剔除 口语填充词（"um", "you know", "like", "basically"）。
#    - 修正 自我纠错（如 "It's two... no, three types" -> 记录为 "three types"）。
# 4. **Pronoun Resolution (指代消解)**：将模糊的 "It", "This" 替换为具体的名词（根据上下文）。
# 5. **Logic Grouping (逻辑分块)**：将流水账文本按逻辑归类为：【定义】、【公式】、【举例】、【结论】、【核心观点】。

# # Handling Incomplete Context (流式处理机制)
# 输入文本的末尾可能是一句没说完的话。
# 输入文本可能不够完整，所以会有当前文本流和上个知识点的尾部语音转写，如果当前文本流不完整，可以参考上个知识点的尾部语音转写。
# <output format>
# # Output Format (JSON)
# 必须输出且仅输出合法的 JSON 格式：
# {
#   "markdown_content": "整理后的Markdown文本，使用加粗、列表、LaTeX公式",
# }
# </output format>
# </system prompt>
# """