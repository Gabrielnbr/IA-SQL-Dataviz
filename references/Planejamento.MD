# Planejamento da Solução

## 1. Problema de Negócio

Os diversos times da empresa precisam tomar decisões mais rápido com dados. Está ocorrendo um gargalo principal: O time de Analista de Dados está sobrecarregado com análises para todas as áreas da empresa. Há muitas pessoas não técnicas "paradas" esperando os dados chegaram para continuar algumas demandas e tomas de decisões mais críticas.
A Empresa precisa se modernizar e tornar-se mais orientado a dados enquanto constrói sua estrutura de Data Warehouses e Data Marts ou Data Lake.

### 1.1. Desafio

Construir uma ferramenta que permita pessoas de negócio - que não tenham domínio técnico de Python, SQL ou ferramentas de Dataviz - consigam consultar os dados com linguagem natural e obtenha respostas confiáveis.

## 2. Ideia SQL com IA

### 2.1. Premissas

1. Um banco de dados só "enxerga" SQL.
   1. O SQL nada mais é do que uma texto muito bem delimitado.
2. As IAs (LLM) conseguem gerar textos.
   1. Essas IAs geram se tiver input bem delimitado e contexto claro.
3. O usuário pode gerar texto e a ferramenta pode ajudar a delimitar esse texto para ser mais claro à IA.

### 2.2. O foco

Tradução da linguagem natural para SQL com suporte da IA.
O Text-to-SQL não é novo já é algo que está sendo desenvolvido.

### 2.3. Fluxo Conceitual

1. Usuário digita a pergunta em linguagem natural.
2. IA interpreta a intenção.
3. IA propõe um SQL coerente com o esquema do banco
4. (Opcional) Validações/ajustes
5. Execução do SQL (somente leitura)
6. Resposta inicial do modelo em tabela + resumo executivo

## 3. Viabilidade

### 3.1. Prós

1. Acelera decisões: usuários acessam dados sem depender de SQL/analistas.
2. Curva de aprendizado baixa: linguagem natural no lugar de sintaxe SQL.
3. Escala: reduz o gargalo do time de dados para perguntas rotineiras.

### 3.2. Contras

1. Alucinações/erros de SQL: modelos podem sugerir tabelas/colunas inexistentes ou joins incorretos. Precisa de validação e logs.
2. Segurança: exigir somente leitura, mascaramento de PII (Dados Sensíveis) e limites de escopo (schemas permitidos).
3. Esquemas complexos: bases grandes, com nomes pouco descritivos, dificultam a geração correta sem bom contexto.
4. Custo/latência: depender de APIs externas pode ter custo/tempo maiores; modelos locais exigem recursos de hardware e ajuste fino.

### 3.3. Medidas mitigadoras

1. RAG/treinamento leve com DDL, diagramas e “exemplos canônicos” de SQL (few-shot).
2. Camada de validação: checagens automáticas (ex.: “apenas SELECT”, limites de LIMIT, bloqueio de DELETE/UPDATE).
3. Observabilidade: salvar prompt, SQL gerado, erro/latência , resultados e feedback do usuário para melhoria contínua.
4. Catálogo de dados: glossário e descrições de colunas/tabelas ajudam muito a precisão.

## 4. Como essa alternativa resolve o problema

1. Remove a barreira técnica: o usuário pergunta em português; a IA gera o SQL.
2. Não precisa esperar um DW completo: funciona agora sobre a fonte disponível (ex.: SQLite com Olist), podendo evoluir depois para outros bancos.
3. Escala com governança: com RAG, prompts de sistema, políticas de segurança e somente leitura, você democratiza com controle.
4. Melhora o foco do time de dados: analistas atuam em análises profundas e qualidade de dados, não em filas de consultas simples.

## 5. LLMs possíveis para testes

1. VANNA
2. LangChain
3. LlamaIndex
4. Defog SQLcODER
5. DB-GPT

## 6. Entrega

Primeira entrega para testes e validações. Um sistema que receba por meio de um chat uma mensagem em linguem natural e retorne a consulta SQL e uma tabela com a consulta realizada.