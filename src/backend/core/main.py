import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, request

from .my_vanna_class import MyVanna  # sua função que instancia o Vanna

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s]: %(message)s"
)

def init_vanna():
    global vn
    vn = MyVanna.vanna_configs()
    
    if vn is None:
        raise RuntimeError("Não foi possível Inicializar o Vanna")
    
    if not vn.esta_treinado():
        vn.tratamento_init()
        logging.info("Treinamento encerrado com sucesso")

@asynccontextmanager
async def on_startup(app: FastAPI):
    init_vanna()
    yield

app = FastAPI(lifespan=on_startup)

@app.post('/pergunta', response_model= json)
def pesquisa(pergunta: json):
    try:
        body = request.json()
        pergunta = body.get("pergunta")
        
        sql = vn.generate_sql(question = pergunta)
        return sql
    except Exception as e:
        logging.exception(f"Erro Inesperado: {e}")

if __name__ == "__main__":
    init_vanna()
    
    pergunta = "Qual o valor médio de compra dos clientes por mês?"
    
    pesquisa(pergunta)