import os
import httpx
import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

OPENROUTER_API_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_RETRIES = 2
BACKOFF_FACTOR = 1.0

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = OPENROUTER_API_BASE_URL
        
        # Log detalhado da API Key
        if not self.api_key:
            logger.error("❌ OPENROUTER_API_KEY não encontrada nas variáveis de ambiente!")
            logger.info("💡 No Render: Settings → Environment Variables → OPENROUTER_API_KEY")
        else:
            logger.info(f"✅ API Key detectada (primeiros 8 chars): {self.api_key[:8]}...")
            logger.info(f"📏 Comprimento da API Key: {len(self.api_key)} caracteres")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://cringe-render.com",
            "X-Title": "CRINGE Bot Platform",
            "Content-Type": "application/json"
        }
        
        # MODELOS OPENROUTER VÁLIDOS E TESTADOS
        self.available_models = [
            "meta-llama/llama-3.1-8b-instruct:free",  # Modelo gratuito e estável
            "mistralai/mistral-7b-instruct:free",     # Outro modelo gratuito
            "huggingfaceh4/zephyr-7b-beta:free",      # Modelo alternativo
            "microsoft/wizardlm-2-8x22b:free",        # Modelo maior (se disponível)
        ]
        
        self.current_model_index = 0
        self.http_client = httpx.Client(timeout=30.0)

    def _test_api_connection(self) -> bool:
        """Testa a conexão com a API OpenRouter usando modelos válidos"""
        if not self.api_key:
            logger.error("❌ Falha no teste: API Key não configurada")
            return False
            
        try:
            logger.info("🧪 Iniciando teste de conexão com OpenRouter...")
            
            # Usar o primeiro modelo da lista para teste
            test_model = self.available_models[0]
            
            test_payload = {
                "model": test_model,
                "messages": [{"role": "user", "content": "Responda apenas 'TESTE_OK'"}],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            logger.info(f"🔧 Testando modelo: {test_model}")
            logger.info(f"🔧 Debug URL: {self.api_url}")
            
            response = self.http_client.post(
                self.api_url,
                headers=self.headers,
                json=test_payload,
                timeout=15
            )
            
            logger.info(f"📡 Status da Resposta: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                logger.info(f"✅ Teste de conexão BEM-SUCEDIDO! Resposta: {content}")
                return True
            elif response.status_code == 401:
                logger.error("❌ ERRO 401: API Key inválida ou não autorizada")
                logger.error("💡 Verifique se a API Key está correta e ativa no OpenRouter")
                return False
            elif response.status_code == 404:
                error_data = response.json()
                model_error = error_data.get('error', {}).get('message', 'Modelo não encontrado')
                logger.error(f"❌ ERRO 404: {model_error}")
                logger.error(f"💡 Modelo '{test_model}' não disponível. Tentando próximo...")
                return False
            elif response.status_code == 402:
                logger.error("❌ ERRO 402: Sem créditos ou requisição não autorizada")
                return False
            elif response.status_code == 429:
                logger.warning("⚠️ ERRO 429: Rate limit excedido")
                return False
            else:
                logger.error(f"❌ ERRO {response.status_code}: {response.text}")
                return False
                
        except httpx.TimeoutException:
            logger.error("⏰ Timeout: OpenRouter não respondeu em 15 segundos")
            return False
        except httpx.ConnectError:
            logger.error("🔌 Erro de conexão: Não foi possível conectar ao OpenRouter")
            return False
        except Exception as e:
            logger.error(f"💥 Erro inesperado no teste: {str(e)}")
            return False

    def _call_openrouter_api(self, payload: Dict[str, Any]) -> str:
        """Faz chamada para API OpenRouter com fallback robusto"""
        
        # Verificação inicial da API Key
        if not self.api_key:
            error_msg = "❌ **Erro de Configuração**: OPENROUTER_API_KEY não encontrada. "
            error_msg += "Configure a variável de ambiente no Render (Settings → Environment Variables)."
            logger.error(error_msg)
            return error_msg
        
        # Teste de conexão detalhado
        connection_ok = self._test_api_connection()
        if not connection_ok:
            error_msg = "🔌 **Erro de Conexão**: Não foi possível conectar ao serviço de IA. "
            error_msg += "Verifique: 1) API Key válida, 2) Conexão com internet, 3) Status do OpenRouter."
            logger.error(error_msg)
            return error_msg
        
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
                        timeout=25.0
                    )
                    
                    logger.info(f"📥 Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result['choices'][0]['message']['content'].strip()
                        logger.info(f"✅ Resposta recebida do {current_model}")
                        self.current_model_index = model_index
                        return content
                    
                    elif response.status_code == 404:
                        logger.warning(f"❌ Modelo {current_model} não encontrado (404)")
                        break  # Mudar para próximo modelo
                    
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
                            time.sleep(BACKOFF_FACTOR)
                            continue
                
                except httpx.TimeoutException:
                    logger.warning(f"⏰ Timeout na tentativa {attempt + 1}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(BACKOFF_FACTOR)
                        continue
                
                except Exception as e:
                    logger.error(f"💥 Erro na tentativa {attempt + 1}: {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(BACKOFF_FACTOR)
                        continue
            
            logger.info(f"❌ Modelo {current_model} falhou, tentando próximo...")
        
        error_msg = "🔴 **Todos os modelos falharam**: Nenhum modelo OpenRouter disponível no momento. "
        error_msg += "Tente novamente mais tarde ou verifique https://status.openrouter.ai"
        logger.error(error_msg)
        return error_msg

    def _prepare_payload(self, system_prompt: str, chat_history: List[Dict[str, str]], user_message: str, temperature: float = 0.7, max_tokens: int = 400) -> Dict[str, Any]:
        """Prepara o payload para a API"""
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system", 
                "content": system_prompt
            })
        
        # Limitar histórico para evitar tokens excessivos
        for message in chat_history[-4:]:
            role = message.get("role")
            content = message.get("content", "")
            if role in ["user", "assistant"] and content.strip():
                messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "messages": messages,
            "model": self.available_models[self.current_model_index],
            "temperature": max(0.3, min(temperature, 0.9)),
            "max_tokens": min(max_tokens, 500),
            "stream": False
        }
        
        logger.info(f"📝 Payload preparado: {len(messages)} mensagens, {max_tokens} tokens")
        return payload

    def generate_response(self, bot_data: Any, ai_config: Dict[str, Any], user_message: str, chat_history: List[Dict[str, str]]) -> str:
        """Gera resposta usando IA"""
        try:
            if hasattr(bot_data, 'to_dict'):
                bot_dict = bot_data.to_dict()
            else:
                bot_dict = bot_data
            
            bot_name = bot_dict.get('name', 'Unknown')
            logger.info(f"🤖 Gerando resposta para '{bot_name}': {user_message[:50]}...")
            
            temperature = min(ai_config.get('temperature', 0.7), 0.9)
            max_tokens = min(ai_config.get('max_output_tokens', 400), 500)
            
            payload = self._prepare_payload(
                system_prompt=bot_dict['system_prompt'],
                chat_history=chat_history,
                user_message=user_message,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response = self._call_openrouter_api(payload)
            
            # Log do resultado
            if response.startswith("❌") or response.startswith("🔴") or response.startswith("🔌"):
                logger.error(f"❌ Falha na geração de resposta para {bot_name}")
            else:
                logger.info(f"✅ Resposta gerada com sucesso para {bot_name}")
                
            return response
            
        except Exception as e:
            logger.error(f"💥 Erro crítico em generate_response: {str(e)}")
            return f"🔴 **Erro Interno**: {str(e)}"