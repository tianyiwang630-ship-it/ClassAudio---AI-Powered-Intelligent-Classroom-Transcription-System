def cur_text(text):
    return '<current text>'+text+'</current text>'
def pre(text):
    return '<previous>'+text+'</previous>'
def transript_chunk(text):
    return '<transcript chunk>'+text+'</transcript chunk>'

import re
import json

def extract_json_object(text: str):
    """
    从 LLM 输出中提取第一个完整的 JSON 对象
    支持最外层是 {} 或 []
    返回 dict / list，失败返回 None
    """
    if not text:
        return None

    # 去掉 markdown 包裹
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()

    # 先尝试 {}
    obj_match = re.search(r"\{[\s\S]*\}", text)
    if obj_match:
        json_str = obj_match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # 再尝试 []
    arr_match = re.search(r"\[[\s\S]*\]", text)
    if arr_match:
        json_str = arr_match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    return None
