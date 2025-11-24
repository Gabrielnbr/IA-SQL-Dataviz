import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from .my_vanna_class import MyVanna  # sua função que instancia o Vanna

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s]: %(message)s"
)

def init_vanna():
    
    """
    Inicializa a instância global do Vanna.

    Esta função é responsável por:

    - Criar uma instância de ``MyVanna`` usando o método de classe
      ``MyVanna.vanna_configs()``;
    - Armazenar a instância em uma variável global (``vn``) para ser
      reutilizada pelos endpoints da API;
    - Registrar logs de sucesso ou erro na inicialização.

    Returns
    -------
    MyVanna or None
        - Instância inicializada de ``MyVanna`` se tudo correr bem;
        - ``None`` em caso de falha (por exemplo, problemas com a
          variável de ambiente, conexão com o SQLite, etc.).

    Notes
    -----
    - Esta função é usada tanto no contexto da aplicação FastAPI
      (via ``lifespan``) quanto quando o módulo é executado diretamente
      (bloco ``if __name__ == "__main__":``).
    """
    
    global vn
    vn = MyVanna.vanna_configs()
    
    if vn is None:
        raise RuntimeError("Não foi possível Inicializar o Vanna")
    
    if not vn.esta_treinado():
        vn.tratamento_init()
        logging.info("Treinamento encerrado com sucesso")

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    """
    Gerencia o ciclo de vida (startup/shutdown) da aplicação FastAPI.

    Na inicialização da aplicação:

    - Chama ``init_vanna()`` para garantir que a instância global do Vanna
      esteja pronta para uso pelos endpoints.

    No encerramento da aplicação:

    - Permite executar lógicas de limpeza (caso necessário no futuro).

    Parameters
    ----------
    app : fastapi.FastAPI
        Instância da aplicação FastAPI.

    Yields
    ------
    None
        O controle é devolvido ao FastAPI após a inicialização, e retomado
        automaticamente no momento do shutdown.
    """
    logging.info("Iniciando aplicação FastAPI (lifespan).")
    init_vanna()
    try:
        yield
    finally:
        logging.info("Encerrando aplicação FastAPI (lifespan).")

app = FastAPI(lifespan=lifespan)

@app.post('/pergunta')
async def pesquisa(request: Request):
    
    """
    Endpoint que recebe uma pergunta em linguagem natural
    e retorna o SQL gerado pelo Vanna.

    Espera receber um JSON no corpo da requisição com o formato:

    .. code-block:: json

        {
            "pergunta": "Texto da pergunta em linguagem natural"
        }

    O endpoint:

    1. Lê o corpo da requisição;
    2. Extrai o campo ``pergunta``;
    3. Usa ``vn.generate_sql(question=pergunta)`` para gerar a consulta SQL;
    4. Retorna um JSON com o SQL gerado ou uma mensagem de erro.

    Parameters
    ----------
    request : fastapi.Request
        Objeto de requisição HTTP recebido pelo FastAPI.

    Returns
    -------
    dict
        Em caso de sucesso:
            ``{"sql": "<consulta_sql_gerada>"}``
        Em caso de erro de entrada:
            ``{"erro": "mensagem explicando o problema"}``
        Em caso de exceção interna:
            ``{"erro": "Erro interno ao processar a pergunta."}``

    Notes
    -----
    - Caso a instância global ``vn`` não esteja inicializada por algum motivo,
      o endpoint tenta chamar ``init_vanna()`` como fallback.
    """
    
    try:
        body = await request.json()
        pergunta = body.get("pergunta")
        
        if not pergunta:
            logging.warning("Campo 'pergunta' ausente ou vazio no corpo da requisição.")
            return {"erro": "Campo 'pergunta' é obrigatório no JSON de entrada."}
        
        if vn is None:
            logging.warning("Instância do Vanna não inicializada. Tentando inicializar.")
            init_vanna()
        
        if vn is None:
            logging.error("Não foi possível inicializar o Vanna.")
            return {"erro": "Erro ao inicializar o Vanna."}
        
        sql = vn.generate_sql(question = pergunta)
        return sql
    
    except json.JSONDecodeError:
        logging.exception("Erro ao decodificar o JSON da requisição.")
        return {"erro": "Corpo da requisição não é um JSON válido."}
    
    except Exception as e:
        logging.exception(f"Erro inesperado ao gerar SQL: {e}")
        return {"erro": f"Erro interno ao processar a pergunta. \n {e}"}

if __name__ == "__main__":
    init_vanna()
    
    pergunta = "Qual o valor médio de compra dos clientes por mês?"
    
    pesquisa(pergunta)