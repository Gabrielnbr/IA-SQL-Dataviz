import logging
from fastapi import FastAPI
from my_vanna_class import MyVanna

vn = MyVanna.vanna_configs()
app = FastAPI()
log = logging.getLogger(__name__)



if __name__ == "__main__":
    
    pergunta = "Qual o valor médio de venda por mês? Ordene pela data de forma crescente."
    
    resposta = pesquisa(pergunta=pergunta)