import os
import logging
from typing import Optional
from my_vanna_class import MyVanna

# TODO: Mover a configuração do log para o inicializador init.py
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s]: %(message)s"
)

# 1. Código funcional? OK
# 2. Garantir verificabilidade dos erros? Ok
def vanna_init(model_name: str = "gpt-3.5-turbo",
               set_db_path: str = "src\data",
               chroma_dir: str = "chroma-db",
               bd_path: str = "\db_olist.sqlite"
               ) -> Optional[MyVanna]:
    
    """
    Inicializa a instância do MyVanna com configuração padrão e conexão ao SQLite.

    Parameters
    ----------
    model_name : str
        Nome do modelo OpenAI a ser usado (default: gpt-3.5-turbo)
    chroma_dir : str
        Diretório de persistência do banco vetorial Chroma.
    bd_path : str
        Caminho do banco SQLite local.

    Returns
    -------
    MyVanna | None
        Retorna a instância inicializada do MyVanna ou None em caso de falha.
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("Variável OPENAI_API_KEY não definida no ambiente")
        
        vn = MyVanna(
            config={
                'path' : set_db_path,
                'openai': {
                    'api_key': api_key,
                    'model': model_name
                },
                'chroma': {
                    'persist_directory': chroma_dir
                }
            }
        )
        
        full_path_olist = set_db_path+bd_path        
        vn.connect_to_sqlite(url=full_path_olist)
        logging.info(f"Conexão com SQLite estabelecida com sucesso: {full_path_olist}")
        logging.info(f"Conexão com Croma estabelecida com sucesso: {chroma_dir}")
        
        return vn
    
    except EnvironmentError as e:
        logging.error(f"Erro de ambiente: {e}", exc_info=True)
    except FileNotFoundError as e:
        logging.error(f"Banco de dados não encontrado: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"Falha inesperada ao inicializar o Vanna: {e}", exc_info=True)
    return None


if __name__ == "__main__":
    vn = vanna_init()
    if vn:
        print("Vanna iniciado com sucesso.")
    else:
        print("Erro ao tentar inicializar Vanna")