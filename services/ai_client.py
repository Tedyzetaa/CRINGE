import os
import httpx
import json
import time
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

# Variáveis de Configuração
# Token da API da Hugging Face lido do ambiente
HF_API_TOKEN = os.getenv("HUGGINGFACE_API_KEY")
# URL Base da API de Inferência da Hugging Face
HF_API_BASE_URL = "https://api-inference.huggingface.co/models"
# Modelo a ser utilizado (o Zephyr-7b-beta é um bom modelo de chat)
HF_MODEL_ID = "HuggingFaceH4/zephyr-7b-beta" 

# Configurações do modelo
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 512

class AIClient:
    """
    Cliente dedicado para comunicação com a API de Inferência da Hugging Face.
    Gerencia autenticação, formatação de payload e retry logic.
    """
    
    def __init__(self, model_id: str = HF_MODEL_ID, api_base_url: str = HF_API_BASE_URL):
        if not HF_API_TOKEN:
            print("AVISO: HUGGINGFACE_API_KEY não está definida. A API de AI não funcionará.")
            
        self.api_url = f"{api_base_url}/{model_id}"
        self.headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}",
            "Content-Type": "application/json"
        }
        self.http_client = httpx.AsyncClient(timeout=30)
        self.model_id = model_id

    def _prepare_hf_payload(
        self, 
        system_prompt: str, 
        user_message: str, 
        chat_history: List[Dict[str, str]], 
        ai_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepara o payload no formato ChatML/Zephyr para a API da Hugging Face.
        """
        # Formato de chat do Zephyr (baseado em ChatML)
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Adiciona histórico (excluindo a última mensagem que é a atual do usuário)
        for msg in chat_history[:-1]:
            # Mapeia roles: 'user' -> user, 'bot' -> assistant
            role = "assistant" if msg["role"] == "bot" else "user"
            messages.append({"role": role, "content": msg["content"]})

        # Adiciona a mensagem atual do usuário
        messages.append({"role": "user", "content": user_message})

        # Prepara a string no formato de chat
        # Ex: <|system|>...</s><|user|>...</s><|assistant|>
        prompt_parts = []
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                prompt_parts.append(f"<|system|>\n{content}</s>")
            elif role == "user":
                prompt_parts.append(f"<|user|>\n{content}</s>")
            elif role == "assistant":
                prompt_parts.append(f"<|assistant|>\n{content}</s>")

        # Adiciona o início do turno do assistente para forçar a resposta da IA
        prompt_parts.append("<|assistant|>\n")
        
        full_prompt = "".join(prompt_parts)

        # Prepara o payload final
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "temperature": ai_config.get("temperature", DEFAULT_TEMPERATURE),
                "max_new_tokens": ai_config.get("max_output_tokens", DEFAULT_MAX_TOKENS),
                "return_full_text": False,  # Retorna apenas a nova resposta gerada
                "use_cache": False,
                "wait_for_model": True
            }
        }
        return payload

    async def _call_hf_api(self, payload: Dict[str, Any], max_retries: int = 3) -> str:
        """
        Faz a chamada à API da Hugging Face com lógica de retry e backoff.
        Trata erros 429 (Rate Limit) e 503 (Serviço Indisponível/Loading).
        """
        if not HF_API_TOKEN:
            raise HTTPException(
                status_code=500,
                detail="Chave HUGGINGFACE_API_KEY não configurada no ambiente."
            )

        for attempt in range(max_retries):
            try:
                response = await self.http_client.post(self.api_url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                # Sucesso (200 OK)
                result = response.json()
                if result and isinstance(result, list) and 'generated_text' in result[0]:
                    # Remove espaços em branco ou tags que sobraram no início/fim
                    return result[0]['generated_text'].strip()
                
                # Estrutura de resposta inesperada
                raise Exception("Resposta da API da Hugging Face com estrutura inválida.")

            except httpx.HTTPStatusError as e:
                # Trata erros específicos que sugerem esperar (429, 503)
                if e.response.status_code in (429, 503) and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Código {e.response.status_code}. Tentativa {attempt + 1}/{max_retries}. Esperando {wait_time}s...")
                    await self.http_client.aclose() # Fecha o cliente antes de esperar
                    time.sleep(wait_time)
                    self.http_client = httpx.AsyncClient(timeout=30) # Cria novo cliente
                    continue
                
                # Outros erros HTTP (400, 401, 404, etc.)
                error_detail = e.response.json().get('error', e.response.text)
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Erro na API da Hugging Face ({e.response.status_code}): {error_detail}"
                )

            except httpx.RequestError as e:
                # Erros de conexão, timeout, etc.
                raise HTTPException(
                    status_code=503,
                    detail=f"Erro de Conexão ou Timeout com a API da Hugging Face: {e}"
                )
            except Exception as e:
                # Erro genérico
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro interno no AI Client: {e}"
                )
        
        # Se esgotar as retries
        raise HTTPException(
            status_code=504,
            detail="A API da Hugging Face excedeu o limite de tentativas. Tente novamente mais tarde."
        )

    async def generate_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        chat_history: List[Dict[str, str]], 
        ai_config: Dict[str, Any]
    ) -> str:
        """
        Gera a resposta da IA chamando o processo completo de preparação e chamada da API.
        """
        
        # 1. Preparar Payload
        payload = self._prepare_hf_payload(system_prompt, user_message, chat_history, ai_config)
        
        # 2. Chamar a API
        ai_response = await self._call_hf_api(payload)
        
        return ai_response

# Instância única do cliente AI para ser usada nas rotas
AI_CLIENT = AIClient()
