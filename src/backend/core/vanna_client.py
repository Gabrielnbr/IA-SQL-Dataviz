import os
import logging
from typing import Optional
from .my_vanna_class import MyVanna

def vanna_init(model_name: str = "gpt-3.5-turbo",
               set_db_path: str = "src\data",
               chroma_dir: str = "chroma-db",
               bd_path: str = "\db_olist.sqlite"
               ) -> Optional[MyVanna]:
    
    """
    Inicializa e retorna uma instância configurada de ``MyVanna``.

    Este helper centraliza a lógica de criação da instância do ``MyVanna``,
    incluindo:

    - Leitura da variável de ambiente ``OPENAI_API_KEY``;
    - Definição de modelo, caminhos de dados e diretório do Chroma;
    - Criação da instância por meio de ``MyVanna.vanna_configs(...)``;
    - Tratamento básico de erros com logging.

    Parameters
    ----------
    model_name : str, optional
        Nome do modelo OpenAI a ser utilizado na geração de texto/SQL.
        Por padrão, ``"gpt-3.5-turbo"``.
    set_db_path : str, optional
        Caminho base do diretório de dados onde se encontram:
        - O arquivo de banco SQLite (``bd_path``);
        - Os artefatos do ChromaDB (quando aplicável).
        Default: ``"src\\data"``.
    chroma_dir : str, optional
        Diretório de persistência do banco vetorial ChromaDB.
        Pode ser um nome de pasta ou caminho relativo a ``set_db_path``.
        Default: ``"chroma-db"``.
    bd_path : str, optional
        Caminho (relativo ou absoluto) para o arquivo de banco SQLite a ser
        utilizado pelo Vanna. Default: ``"\\db_olist.sqlite"``.

    Returns
    -------
    MyVanna or None
        - Instância de ``MyVanna`` já conectada ao SQLite e ao Chroma, em caso
          de sucesso.
        - ``None`` se ocorrer algum erro crítico durante a inicialização.

    Notes
    -----
    - Erros de ambiente (por exemplo, ausência de ``OPENAI_API_KEY``),
      problemas de caminho de banco de dados ou falhas inesperadas são
      registrados no log e fazem a função retornar ``None``.
    - Esta função é um wrapper conveniente em torno de
      ``MyVanna.vanna_configs(...)``, ideal para ser usada em pontos de
      entrada da aplicação (por exemplo, em ``main.py`` ou scripts de teste).
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