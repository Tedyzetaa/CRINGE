import os
import httpx
import time
from typing import Dict, Any, List

OPENROUTER_API_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_RETRIES = 2
BACKOFF_FACTOR = 1.0

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = OPENROUTER_API_BASE_URL
        
        print(f"🔑 DEBUG AI Service - API Key: {'✅ PRÉSENTE' if self.api_key else '❌ AUSENTE'}")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/Tedyzetaa/CRINGE",
            "X-Title": "CRINGE Bot Platform",
            "Content-Type": "application/json"
        }
        self.http_client = httpx.Client(timeout=30.0)
        
        # Modelos mais estáveis em ordem de preferência
        self.available_models = [
            "google/gemini-flash-1.5:free",
            "anthropic/claude-3-haiku:beta",
            "meta-llama/llama-3.1-8b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
        ]
        
        self.current_model = self.available_models[0]

    def _call_openrouter_api(self, payload: Dict[str, Any]) -> str:
        print(f"🔍 DEBUG - Chamando OpenRouter com modelo: {self.current_model}")
        
        for attempt in range(MAX_RETRIES):
            try:
                print(f"📤 Tentativa {attempt + 1} para {self.current_model}")
                response = self.http_client.post(
                    self.api_url, 
                    headers=self.headers, 
                    json=payload,
                    timeout=30.0
                )
                
                print(f"📥 Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content'].strip()
                    print(f"✅ Resposta recebida: {content[:100]}...")
                    return content
                elif response.status_code == 429:
                    print("⚠️ Rate limit, tentando próximo modelo...")
                    break
                else:
                    response.raise_for_status()
                    
            except httpx.TimeoutException:
                print(f"⏰ Timeout na tentativa {attempt + 1}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                    continue
            except Exception as e:
                print(f"❌ Erro na tentativa {attempt + 1}: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                    continue
        
        # Se todos os modelos falharem, tentar o próximo modelo na lista
        current_index = self.available_models.index(self.current_model)
        if current_index < len(self.available_models) - 1:
            self.current_model = self.available_models[current_index + 1]
            print(f"🔄 Mudando para modelo: {self.current_model}")
            return self._call_openrouter_api(payload)
        
        return "❌ Desculpe, estou tendo dificuldades técnicas no momento. Podemos tentar novamente?"

    def _prepare_payload(self, system_prompt: str, chat_history: List[Dict[str, str]], user_message: str, temperature: float = 0.7, max_tokens: int = 400) -> Dict[str, Any]:
        messages = []
        
        # System prompt mais claro
        if system_prompt:
            messages.append({
                "role": "system", 
                "content": f"{system_prompt}\n\nIMPORTANTE: Responda com APENAS UMA mensagem. Não repita a mesma resposta. Mantenha a conversa fluindo naturalmente."
            })
        
        # Histórico limitado para evitar contexto muito longo
        for message in chat_history[-6:]:  # Últimas 6 mensagens apenas
            role = message.get("role")
            content = message.get("content", "")
            if role in ["user", "assistant"] and content.strip():
                messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "messages": messages,
            "model": self.current_model,
            "temperature": max(0.3, min(temperature, 0.9)),  # Limitar temperatura
            "max_tokens": max_tokens,
            "stream": False
        }
        
        print(f"📝 Payload - Temperature: {payload['temperature']}, Max Tokens: {max_tokens}")
        return payload

    def generate_response(self, bot_data: Any, ai_config: Dict[str, Any], user_message: str, chat_history: List[Dict[str, str]]) -> str:
        # Converter para dict se for objeto SQLAlchemy
        if hasattr(bot_data, 'to_dict'):
            bot_dict = bot_data.to_dict()
        else:
            bot_dict = bot_data
        
        # System prompt mais limpo
        system_prompt = bot_dict['system_prompt']
        
        # Configurações com fallbacks seguros
        temperature = min(ai_config.get('temperature', 0.7), 0.8)  # Limitar temp máxima
        max_tokens = min(ai_config.get('max_output_tokens', 400), 500)  # Limitar tokens
        
        print(f"🤖 Gerando resposta para: {user_message[:50]}...")
        print(f"⚙️ Config - Temp: {temperature}, Tokens: {max_tokens}")

        payload = self._prepare_payload(
            system_prompt=system_prompt,
            chat_history=chat_history,
            user_message=user_message,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return self._call_openrouter_api(payload)
