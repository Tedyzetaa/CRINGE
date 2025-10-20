📚 Bots RPG (Role-Playing Game)

Este projeto implementa uma API de backend que gerencia diferentes bots (NPCs) para uma experiência de Role-Playing Game (RPG) interativa. O principal foco é garantir que as respostas dos bots sejam contextuais, seguindo o histórico completo da conversa para construir narrativas coerentes e avançar os cenários de forma dinâmica.

⚙️ Funcionalidades da API

1. Modelos de Dados (Pydantic)

AIConfig: Define a configuração do modelo de IA (temperatura, tokens).

Bot: O modelo completo de um bot, incluindo ID, persona, prompt de sistema e configurações de IA.

BotIn: O modelo de entrada para criação de novos bots.

ChatMessage: Representa uma mensagem individual na conversa (role e text).

BotChatRequest: Contém o ID do bot e o histórico completo de mensagens (messages).

2. Gerenciamento de Bots

POST /bots/: Cria um novo bot e o adiciona ao banco de dados simulado (MOCK_BOTS_DB).

GET /bots/: Lista todos os bots disponíveis.

GET /bots/{bot_id}: Retorna os detalhes de um bot específico.

PUT /bots/import: Importa uma lista de bots a partir de um arquivo/payload.

3. Integração e Contexto (Feature Principal)

3.8 Versão Anterior: Simulação de Respostas Automáticas

Anteriormente, a rota de chat utilizava simulações com listas de respostas predefinidas para os bots, resultando em interações que, embora variadas, careciam de coerência e continuidade de cenário.

3.9 Atualização: Geração Estritamente Contextual e RPG Avançado (VERSÃO ATUAL)

A lógica de chat foi totalmente reescrita para garantir que a resposta do bot seja gerada exclusivamente com base no contexto completo da conversa e no prompt de sistema.

Mecanismo:

Payload Completo: A função _prepare_gemini_payload empacota o histórico completo (messages) e o Prompt de Sistema (system_prompt) do bot em um formato compatível com a API de LLM (como Gemini).

Foco em RPG: O system_prompt de cada bot contém Regras Obrigatórias que forçam o LLM a:

Referenciar o contexto da conversa.

Usar o formato de RPG (descrição de ação/cenário seguido por diálogo).

Garantir que a resposta EVOLUA o cenário ou a cena em andamento, respondendo ativamente à última fala do usuário.

Remoção de Respostas Fixas: Nenhuma resposta automática ou randomizada é usada na rota de chat, garantindo que a resposta final seja uma criação totalmente contextualizada do LLM (simulada na implementação atual).

🧑‍💻 Bots Ativos

Nome

Gênero

Personalidade

Regra Específica

Pimenta (Pip)

Feminino

Caótica, curiosa, emocional.

Deve incluir a voz de Professor Cartola (sarcástico) em suas respostas.

Zimbrak

Masculino

Inventor, surreal, calmo.

Usa metáforas mecânicas/engrenagens.

Luma

Feminino

Guardiã silenciosa, poética.

Foca em palavras perdidas e entrelinhas.

Tiko

Indefinido

Caótico, cômico, nonsense.

Mistura piadas com filosofia absurda.