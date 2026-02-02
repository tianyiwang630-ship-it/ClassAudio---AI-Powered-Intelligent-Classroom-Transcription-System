from google import genai
from openai import OpenAI
class DSV3:
    def __init__(self,model_name='deepseek-v3-2-251201'):
        self.client = OpenAI(base_url="https://ark.cn-beijing.volces.com/api/v3",
                             api_key='223d6179-cf08-4fba-abfc-20e506ee24f7')
        self.model_name = model_name
    def generate(self,prompt:str) -> str:
        completion = self.client.chat.completions.create(
            model = self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
class DBFlash16:
    def __init__(self,model_name='doubao-seed-1-6-flash-250828'):
        self.client = OpenAI(base_url="https://ark.cn-beijing.volces.com/api/v3",
                             api_key='223d6179-cf08-4fba-abfc-20e506ee24f7')
        self.model_name = model_name
    def generate(self,prompt:str) -> str:
        completion = self.client.chat.completions.create(
            model = self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
# a = DSV3()
# print(a.generate('你好'))