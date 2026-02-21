from google import genai
from zhipuai import ZhipuAI
from openai import OpenAI
import os

def generate_prompt(friend_info, chat_history):
    return f"""
    任务：根据好友信息和聊天记录生成有针对性的春节祝福。
    好友信息:
    {friend_info}
    
    聊天记录：
    {chat_history}
    
    
    要求：
    1. 分析我和对方的关系（是死党、长辈、还是工作伙伴）。
    2. 结合聊天中提到的生活细节（如最近的困难、成就、共同话题）。
    3. 聊天记录中的"我"是我发送消息，"好友"是对方发送消息。
    4. 生成一段简短、温暖、不尴尬的新年祝福。
    5. 直接输出祝福语，不要包含解释。
    """
    
def generate_greeting(friend_info, chat_history, api_key, model_name):
    assert api_key, "API key is required for LLM generation"
    # 1. 初始化客户端 (新版用法)
    client = genai.Client(api_key=api_key)
    prompt = generate_prompt(friend_info, chat_history)
    
    model_name_lower = model_name.lower()
    
    try:
        # 1. Google Gemini 系列
        if "gemini" in model_name_lower:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text

        # 2. 智谱 GLM 系列
        elif "glm" in model_name_lower:
            client = ZhipuAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        
        # 3. 其他兼容 OpenAI 协议的模型 (GPT, DeepSeek, Qwen, Minimax)
        else:
            # 根据模型名称动态确定 base_url
            if "qwen" in model_name_lower:
                base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            
            if base_url:
                client = OpenAI(api_key=api_key, base_url=base_url)
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            else:
                return f"未定义的模型类型: {model_name}"
            
    except Exception as e:
        return f"生成失败: {str(e)}"

# 测试代码
if __name__ == "__main__":
    print("正在测试生成...")
    model_name = ""
    api_key = ""
    mock_info = "姓名：老王\n关系：大学同学，关系不错但不算特别亲密"
    mock_history = "我: 那个项目终于搞完了\n好友: 是啊，累死个人，今晚去喝一杯？\n我: 行啊，老地方见"
    
    print(generate_greeting(mock_info, mock_history, api_key, model_name))