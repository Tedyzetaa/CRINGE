# services/ai_client.py

import os
import json
import httpx
import time
from typing import Dict, Any, List

# Configurações de Retry/Backoff
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5

# O cliente é inicializado aqui, lendo a variável de ambiente
HF_API_TOKEN = os.getenv("HUGGINGFACE_API_KEY")
HF_API_BASE_URL = os.getenv("HF_API_BASE_URL", "https://api-inference.huggingface.co/models/")

class AIClient:
    """
    Cliente dedicado para comunicação com a API da Hugging Face.
    Encapsula lógica de chamadas HTTP, retries e tratamento de erros.
    """

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.api_url = f"{HF_API_BASE_URL}{model_id}"
        self.headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        # Usamos um cliente síncrono
        self.http_client = httpx.Client(timeout=60.0)

        if not HF_API_TOKEN:
            print("AVISO: HUGGINGFACE_API_KEY não está configurada. As chamadas à API falharão.")

    def _call_hf_api(self, payload: Dict[str, Any]) -> str:
        """
        Faz a chamada para a API da Hugging Face com retries.
        """
        for attempt in range(MAX_RETRIES):
            try:
                response = self.http_client.post(self.api_url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                if not result or 'generated_text' not in result[0]:
                    raise ValueError("Resposta da API da Hugging Face incompleta ou malformada.")
                
                generated_text = result[0]['generated_text']
                
                # Lógica de limpeza para Zephyr/ChatML: Remove o prompt repetido e tags.
                clean_text = generated_text.split("</s>")[-1].strip()
                
                if clean_text.startswith("<|assistant|>"):
                    clean_text = clean_text.replace("<|assistant|>", "", 1).strip()
                
                return clean_text if clean_text else generated_text

            except httpx.HTTPStatusError as e:
                if response.status_code in (429, 503) and attempt < MAX_RETRIES - 1:
                    wait_time = BACKOFF_FACTOR * (2 ** attempt)
                    print(f"Aviso HF: API congestionada ({response.status_code}). Tentando novamente em {wait_time:.2f}s...")
                    time.sleep(wait_time)
                    continue
                
                raise Exception(f"Erro na API da Hugging Face ({response.status_code}): {response.text}") from e

            except (httpx.RequestError, ValueError, IndexError) as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = BACKOFF_FACTOR * (2 ** attempt)
                    print(f"Aviso HF: Erro de rede/dados ({e}). Tentando novamente em {wait_time:.2f}s...")
                    time.sleep(wait_time)
                    continue
                
                raise Exception(f"Falha ao se comunicar com a API da Hugging Face após {MAX_RETRIES} tentativas: {e}") from e

        raise Exception("Erro desconhecido ao chamar a API da Hugging Face.")

    def _prepare_hf_payload(self, system_prompt: str, chat_history: List[Dict[str, str]], user_message: str) -> Dict[str, Any]:
        """Prepara a carga útil (payload) no formato de chat requerido pelo modelo."""
        
        system_prefix = f"<|system|>{system_prompt}</s>"
        
        history_str = ""
        for message in chat_history:
            role = message.get("role")
            content = message.get("content", "")
            if role == "user":
                history_str += f"<|user|>{content}</s>"
            elif role == "assistant":
                history_str += f"<|assistant|>{content}</s>"

        new_message_str = f"<|user|>{user_message}</s>"
        response_start_tag = "<|assistant|>"

        full_prompt = system_prefix + history_str + new_message_str + response_start_tag
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.9,
                "top_p": 0.95,
                "do_sample": True,
                "return_full_text": True 
            }
        }
        return payload

    def generate_response(self, system_prompt: str, chat_history: List[Dict[str, str]], user_message: str) -> str:
        """Função principal para gerar a resposta."""
        payload = self._prepare_hf_payload(system_prompt, chat_history, user_message)
        return self._call_hf_api(payload)
