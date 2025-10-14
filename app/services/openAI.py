import os
from openai import OpenAI
from app.logger import loggerOpenAI


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def interpret_with_gpt(prompt, system_message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        loggerOpenAI.error(f"Error in ask_gpt: {e}")
        return None
