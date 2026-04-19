import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# src/Core/llm.py
VALID_MODELS = {
    "fast": "llama-3.1-8b-instant",
    "smart": "llama-3.3-70b-versatile",
    "openai": "openai/gpt-oss-120b"
}

def generate_report(prompt: str, model_key="fast"):
    model = VALID_MODELS.get(model_key, VALID_MODELS["fast"])
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a cybersecurity reconnaissance analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        print("GROQ ERROR:", str(e))   # 🔥 IMPORTANT
        raise e