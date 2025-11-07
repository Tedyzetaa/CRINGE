import os
import httpx
import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

OPENROUTER_API_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = OPENROUTER_API_BASE_URL
        
        logger.info(f"🔑 AIService inicializado - API Key: {'✅ PRÉSENTE' if self.api_key else '❌ AUSENTE'}")
        
        if not self.api_key:
            logger.error("❌ OPENROUTER_API_KEY não encontrada!")
            logger.info("💡 Configure a variável de ambiente OPENROUTER_API_KEY")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/Tedyzetaa/CRINGE",
            "X-Title": "CRINGE Bot Platform",
            "Content-Type": "application/json"
        }
        
        self.available_models = [
            "google/gemini-flash-1.5:free",
            "meta-llama/llama-3.1-8b-instruct:free", 
            "mistralai/mistral-7b-instruct:free",
            "huggingfaceh4/zephyr-7b-beta:free",
        ]
        
        self.current_model_index = 0
        self.http_client = httpx.Client(timeout=45.0)

    def _test_api_connection(self) -> bool:
        """Testa a conexão com a API OpenRouter"""
        try:
            test_payload = {
                "model": self.available_models[0],
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10
            }
            
            response = self.http_client.post(
                self.api_url,
                headers=self.headers,
                json=test_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Conexão com OpenRouter: OK")
                return True
            elif response.status_code == 401:
                logger.error("❌ API Key inválida")
                return False
            else:
                logger.warning(f"⚠️ API retornou status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro na conexão: {str(e)}")
            return False

    def _call_openrouter_api(self, payload: Dict[str, Any]) -> str:
        """Faz chamada para API OpenRouter com fallback"""
        
        if not self._test_api_connection():
            return "🔌 Problema de conexão com o serviço de IA."
        
        for model_index in range(len(self.available_models)):
            current_model = self.available_models[model_index]
            payload["model"] = current_model
            
            logger.info(f"🔄 Tentando modelo: {current_model}")
            
            for attempt in range(MAX_RETRIES):
                try:
                    logger.info(f"📤 Tentativa {attempt + 1} para {current_model}")
                    
                    response = self.http_client.post(
                        self.api_url,
                        headers=self.headers,
                        json=payload,
                        timeout=30.0
                    )
                    
                    logger.info(f"📥 Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result['choices'][0]['message']['content'].strip()
                        logger.info("✅ Resposta recebida com sucesso")
                        self.current_model_index = model_index
                        return content
                    
                    elif response.status_code == 402:
                        logger.warning(f"⚠️ Sem créditos para {current_model}")
                        break
                    
                    elif response.status_code == 429:
                        wait_time = BACKOFF_FACTOR * (2 ** attempt)
                        logger.warning(f"⏰ Rate limit, aguardando {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    
                    else:
                        logger.warning(f"⚠️ Erro {response.status_code} para {current_model}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                            continue
                
                except httpx.TimeoutException:
                    logger.warning(f"⏰ Timeout na tentativa {attempt + 1}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                        continue
                
                except Exception as e:
                    logger.error(f"💥 Erro na tentativa {attempt + 1}: {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                        continue
            
            logger.info(f"❌ Modelo {current_model} falhou, tentando próximo...")
        
        error_msg = "❌ Todos os modelos falharam."
        if not self.api_key:
            error_msg += " API Key não configurada."
        else:
            error_msg += " Verifique créditos ou conexão."
        
        logger.error(error_msg)
        return error_msg

    def _prepare_payload(self, system_prompt: str, chat_history: List[Dict[str, str]], user_message: str, temperature: float = 0.7, max_tokens: int = 400) -> Dict[str, Any]:
        """Prepara o payload para a API"""
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system", 
                "content": f"{system_prompt}\n\nInstrução: Responda de forma natural e coerente."
            })
        
        for message in chat_history[-6:]:
            role = message.get("role")
            content = message.get("content", "")
            if role in ["user", "assistant"] and content.strip():
                messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "messages": messages,
            "model": self.available_models[self.current_model_index],
            "temperature": max(0.3, min(temperature, 0.9)),
            "max_tokens": min(max_tokens, 800),
            "stream": False
        }
        
        logger.info(f"📝 Payload preparado - Mensagens: {len(messages)}")
        return payload

    def generate_response(self, bot_data: Any, ai_config: Dict[str, Any], user_message: str, chat_history: List[Dict[str, str]]) -> str:
        """Gera resposta usando IA"""
        try:
            if hasattr(bot_data, 'to_dict'):
                bot_dict = bot_data.to_dict()
            else:
                bot_dict = bot_data
            
            logger.info(f"🤖 Gerando resposta para: {user_message[:50]}...")
            
            temperature = min(ai_config.get('temperature', 0.7), 0.9)
            max_tokens = min(ai_config.get('max_output_tokens', 400), 800)
            
            payload = self._prepare_payload(
                system_prompt=bot_dict['system_prompt'],
                chat_history=chat_history,
                user_message=user_message,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response = self._call_openrouter_api(payload)
            return response
            
        except Exception as e:
            logger.error(f"💥 Erro em generate_response: {str(e)}")
            return f"❌ Erro interno do serviço de IA: {str(e)}"