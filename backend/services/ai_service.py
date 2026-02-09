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
        
        # Log mais informativo
        if self.api_key:
            logger.info(f"🔑 AIService inicializado - API Key: ✅ PRESENTE ({len(self.api_key)} caracteres)")
            # Log apenas os primeiros e últimos 4 caracteres para segurança
            masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
            logger.info(f"🔑 API Key (mascarada): {masked_key}")
        else:
            logger.error("❌ OPENROUTER_API_KEY não encontrada!")
            logger.info("💡 Configure a variável de ambiente OPENROUTER_API_KEY")

        # CORREÇÃO: Headers corretos para OpenRouter
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://cringe-chat.streamlit.app",  # URL do seu app
            "X-Title": "CRINGE Chat RPG",
            "Content-Type": "application/json"
        }
        
        # CORREÇÃO: Modelos atualizados e testados
        self.available_models = [
            "mistralai/mistral-7b-instruct:free",
            "google/gemma-7b-it:free",
            "huggingfaceh4/zephyr-7b-beta:free",
            "meta-llama/llama-3.1-8b-instruct:free"
        ]
        
        self.current_model_index = 0
        # CORREÇÃO: Timeout aumentado
        self.http_client = httpx.Client(timeout=60.0)

    def _test_api_connection(self) -> bool:
        """Testa a conexão com a API OpenRouter"""
        if not self.api_key:
            logger.error("❌ API Key não configurada")
            return False
            
        try:
            test_payload = {
                "model": self.available_models[0],
                "messages": [
                    {
                        "role": "user", 
                        "content": "Responda apenas com 'TESTE_OK' se esta mensagem for recebida."
                    }
                ],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            logger.info(f"🔍 Testando conexão com OpenRouter...")
            logger.info(f"📡 URL: {self.api_url}")
            logger.info(f"🔑 Headers: Authorization: Bearer ***")
            
            response = self.http_client.post(
                self.api_url,
                headers=self.headers,
                json=test_payload,
                timeout=15
            )
            
            logger.info(f"📥 Resposta do teste: Status {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                logger.info(f"✅ Conexão com OpenRouter: OK - Resposta: '{content}'")
                return True
            elif response.status_code == 401:
                logger.error("❌ API Key inválida ou não autorizada")
                logger.error(f"🔍 Resposta completa: {response.text}")
                return False
            elif response.status_code == 402:
                logger.error("❌ Sem créditos ou limite excedido")
                return False
            elif response.status_code == 429:
                logger.error("❌ Rate limit excedido")
                return False
            else:
                logger.error(f"❌ Erro HTTP {response.status_code}: {response.text}")
                return False
                
        except httpx.TimeoutException:
            logger.error("⏰ Timeout na conexão com OpenRouter")
            return False
        except httpx.ConnectError:
            logger.error("🔌 Erro de conexão - não foi possível conectar ao OpenRouter")
            return False
        except Exception as e:
            logger.error(f"💥 Erro inesperado na conexão: {str(e)}")
            return False

    def _call_openrouter_api(self, payload: Dict[str, Any]) -> str:
        """Faz chamada para API OpenRouter com fallback"""
        
        if not self.api_key:
            return "🔌 Erro: API Key do OpenRouter não configurada."
        
        # Testar conexão primeiro
        if not self._test_api_connection():
            return "🔌 Problema de conexão com o serviço de IA. Verifique a API Key e conexão."

        # Tentar cada modelo disponível
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
                        timeout=45.0
                    )
                    
                    logger.info(f"📥 Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result['choices'][0]['message']['content'].strip()
                        logger.info(f"✅ Resposta recebida com sucesso do modelo {current_model}")
                        logger.info(f"📝 Resposta (primeiros 100 chars): {content[:100]}...")
                        self.current_model_index = model_index
                        return content
                    
                    elif response.status_code == 402:
                        logger.warning(f"⚠️ Sem créditos para {current_model}")
                        break  # Pula para o próximo modelo
                    
                    elif response.status_code == 429:
                        wait_time = BACKOFF_FACTOR * (2 ** attempt)
                        logger.warning(f"⏰ Rate limit, aguardando {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    
                    else:
                        logger.warning(f"⚠️ Erro {response.status_code} para {current_model}: {response.text[:200]}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                            continue
                        break
                
                except httpx.TimeoutException:
                    logger.warning(f"⏰ Timeout na tentativa {attempt + 1} para {current_model}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                        continue
                    break
                
                except Exception as e:
                    logger.error(f"💥 Erro na tentativa {attempt + 1} para {current_model}: {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                        continue
                    break
            
            logger.info(f"❌ Modelo {current_model} falhou, tentando próximo...")
        
        error_msg = "❌ Todos os modelos falharam após várias tentativas."
        logger.error(error_msg)
        return error_msg

    def _prepare_payload(self, system_prompt: str, chat_history: List[Dict[str, str]], user_message: str, temperature: float = 0.7, max_tokens: int = 400) -> Dict[str, Any]:
        """Prepara o payload para a API"""
        messages = []
        
        # CORREÇÃO: System prompt como mensagem de sistema
        if system_prompt and system_prompt.strip():
            messages.append({
                "role": "system", 
                "content": system_prompt.strip()
            })
        
        # CORREÇÃO: Histórico de conversa limitado para evitar token overflow
        for message in chat_history[-8:]:  # Mantém apenas últimas 8 mensagens
            role = message.get("role")
            content = message.get("content", "").strip()
            
            if role in ["user", "assistant"] and content:
                # Mapear 'assistant' para 'system' se necessário, mas geralmente é 'assistant'
                if role == "assistant" and "system" in content.lower():
                    messages.append({"role": "system", "content": content})
                else:
                    messages.append({"role": role, "content": content})
        
        # CORREÇÃO: Garantir que a mensagem do usuário seja adicionada
        if user_message.strip():
            messages.append({"role": "user", "content": user_message.strip()})
        
        # CORREÇÃO: Parâmetros ajustados
        payload = {
            "messages": messages,
            "model": self.available_models[self.current_model_index],
            "temperature": max(0.1, min(temperature, 1.0)),  # Range mais amplo
            "max_tokens": min(max_tokens, 1024),  # Aumentado para 1024
            "top_p": 0.9,
            "stream": False
        }
        
        logger.info(f"📝 Payload preparado:")
        logger.info(f"   - Modelo: {payload['model']}")
        logger.info(f"   - Mensagens: {len(messages)}")
        logger.info(f"   - Temperature: {payload['temperature']}")
        logger.info(f"   - Max Tokens: {payload['max_tokens']}")
        
        return payload

    def generate_response(self, bot_data: Any, ai_config: Dict[str, Any], user_message: str, chat_history: List[Dict[str, str]]) -> str:
        """Gera resposta usando IA"""
        try:
            # Converter bot_data para dict se necessário
            if hasattr(bot_data, 'to_dict'):
                bot_dict = bot_data.to_dict()
            else:
                bot_dict = bot_data
            
            logger.info(f"🤖 Iniciando geração de resposta para: {bot_dict.get('name', 'Unknown')}")
            logger.info(f"💬 Mensagem do usuário: {user_message[:100]}...")
            
            # CORREÇÃO: Valores padrão mais conservadores
            temperature = ai_config.get('temperature', 0.7)
            max_tokens = ai_config.get('max_output_tokens', 500)
            
            # Garantir limites razoáveis
            temperature = max(0.1, min(temperature, 1.0))
            max_tokens = min(max_tokens, 1024)
            
            system_prompt = bot_dict.get('system_prompt', '')
            if not system_prompt:
                system_prompt = f"Você é {bot_dict.get('name', 'um assistente')}. {bot_dict.get('personality', 'Seja útil e amigável.')}"
            
            payload = self._prepare_payload(
                system_prompt=system_prompt,
                chat_history=chat_history,
                user_message=user_message,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            logger.info("🚀 Chamando API OpenRouter...")
            start_time = time.time()
            
            response = self._call_openrouter_api(payload)
            
            end_time = time.time()
            logger.info(f"⏱️  Tempo de resposta: {end_time - start_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"💥 Erro crítico em generate_response: {str(e)}")
            import traceback
            logger.error(f"📋 Stack trace: {traceback.format_exc()}")
            
            # Fallback mais informativo
            fallback_responses = {
                "Pimenta (Pip)": "💫 *Chocalho!* Minhas conexões mágicas estão instáveis... Mas sinto sua energia! O que mais você gostaria de compartilhar?",
                "Zimbrak": "⚙️ *Engrenagens rangendo* Hmm, uma falha técnica momentânea... Suas palavras ainda ecoam em minha oficina.",
                "Luma": "📖 *Letras tremulam* Um silêncio inesperado... Sua mensagem foi registrada. Continue, por favor.",
                "Tiko": "🎪 *Cores piscando* OPA! Um pequeno tremor dimensional! Conte mais, conte mais!"
            }
            
            bot_name = bot_dict.get('name', 'Assistente')
            return fallback_responses.get(bot_name, "🤖 Estou tendo dificuldades técnicas no momento. Podemos tentar novamente?")

    def get_status(self) -> Dict[str, Any]:
        """Retorna o status atual do serviço de IA"""
        return {
            "api_key_set": bool(self.api_key),
            "api_key_length": len(self.api_key) if self.api_key else 0,
            "connection_test": self._test_api_connection(),
            "current_model": self.available_models[self.current_model_index] if self.available_models else None,
            "available_models": self.available_models,
            "http_referer": self.headers.get("HTTP-Referer", "Not set")
        }