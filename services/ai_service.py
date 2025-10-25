import os
import httpx
import time
from typing import Dict, Any, List

OPENROUTER_API_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = OPENROUTER_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/Tedyzetaa/CRINGE",
            "X-Title": "CRINGE Bot Platform",
            "Content-Type": "application/json"
        }
        self.http_client = httpx.Client(timeout=60.0)
        
        # Lista de modelos disponíveis no OpenRouter
        self.available_models = [
            "mistralai/mistral-7b-instruct:free",
            "huggingfaceh4/zephyr-7b-beta:free",
            "google/palm-2-chat-bison-32k:free",
            "anthropic/claude-3-haiku",
            "openai/gpt-3.5-turbo",
        ]
        
        self.current_model = self.available_models[0]
        
        if not self.api_key:
            print("❌ AVISO: OPENROUTER_API_KEY não encontrada!")

    def _call_openrouter_api(self, payload: Dict[str, Any]) -> str:
        for model in self.available_models:
            payload["model"] = model
            self.current_model = model
            
            for attempt in range(MAX_RETRIES):
                try:
                    response = self.http_client.post(self.api_url, headers=self.headers, json=payload)
                    response.raise_for_status()
                    
                    result = response.json()
                    return result['choices'][0]['message']['content'].strip()

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        break
                    elif e.response.status_code == 402:
                        return "❌ Sem créditos na API OpenRouter."
                    elif e.response.status_code in (429, 503) and attempt < MAX_RETRIES - 1:
                        time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                        continue
                    else:
                        if attempt == MAX_RETRIES - 1:
                            continue
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                        continue
        
        return "❌ Todos os modelos falharam."

    def _prepare_payload(self, system_prompt: str, chat_history: List[Dict[str, str]], user_message: str, temperature: float = 0.7, max_tokens: int = 512) -> Dict[str, Any]:
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        for message in chat_history:
            role = message.get("role")
            content = message.get("content", "")
            if role in ["user", "assistant"]:
                messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "messages": messages,
            "model": self.current_model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        return payload

    def generate_response(self, bot_data: Any, ai_config: Dict[str, Any], user_message: str, chat_history: List[Dict[str, str]]) -> str:
        system_prompt = f"{bot_data.system_prompt}\n\nPersonalidade: {bot_data.personality}\nContexto: {bot_data.conversation_context}"
        temperature = ai_config.get('temperature', 0.7)
        max_tokens = ai_config.get('max_output_tokens', 512)

        payload = self._prepare_payload(
            system_prompt=system_prompt,
            chat_history=chat_history,
            user_message=user_message,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return self._call_openrouter_api(payload)
