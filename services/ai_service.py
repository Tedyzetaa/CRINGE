from google import genai

def generate_response(prompt: str, config: dict):
    client = genai.Client(api_key="...")
    return client.models.generate(
        model="gemini-2.5-flash",
        input=prompt,
        config=config
    )