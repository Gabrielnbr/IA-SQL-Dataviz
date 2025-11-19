from __future__ import annotations
from typing import Dict, List
from pathlib import Path
import logging
import pickle

log = logging.getLogger(__name__)


def leitura_arquivos_treinamento(nome_arquivo: str,
                                 path_arquivo: str
                                 ):
    try:
        full_path = Path(path_arquivo) / nome_arquivo
        
        with open(full_path, "rb") as f:
            arquivo = pickle.load(f)
        
        log.info(f"Arquivo no dir {full_path} lido com sucesso.")
        
        if not arquivo: # arquivo =
            raise ValueError("O arquivo foi lido, mas está vazio (sem informações).")
        
        return arquivo
    
    except FileNotFoundError as e:
        log.error(f"Arquivo não encontrado no diretório informado: {path_arquivo} \n Verifique o caminho novamente: {e}",
                  exc_info=True)
    except ValueError as e:
        log.error(f"Conteúdo inválido do arquivo de treinamento. {e} ",
                  exc_info=True)
    except Exception as e:
        log.exception(f"Erro inesperado ao tentar ler o arquivo: {e}")

def treinar_ddl(vn,
                ddl_sql: str | None = None
                ) -> None:
    """
    Treina o Vanna com os DDLs das tabelas do SQLite.
    Retorna a contagem de objetos treinados.
    """
    try:
        if ddl_sql is None:
            raise ValueError("Não foi passado nenhuma query para treinamento")
        
        df_ddl = vn.run_sql(ddl_sql)
        n = 0
        for _, row in df_ddl.iterrows():
            ddl = (row["sql"] or "").strip()
            if ddl:
                vn.train(ddl=ddl)
                n+=1
        
        log.info(f"Treinamento DDL concluído: {n} objetos adicionados")
    
    except ValueError as e:
        log.error(f"Erro nos parâmetros: {e}", exc_info=True)
    except Exception as e:
        log.error(f"Erro inesperado ao treinar com ddl: {e}", exc_info=True)

def treinar_qa(vn,
               qa: List[Dict[str,str]]
               ) -> None:
    
    try:
        if qa is None:
            raise ValueError("O 'qa' passado não corresponde ao valor esperado: 'List[Dict[str,str]]'")
        
        for q in qa:
            vn.train(question=q["question"], sql=q["sql"])
            
        log.info("Treinamento de Perguntas e Respostas realizado com sucesso.")
    except Exception as e:
        log.exception(f"Erro Inesperado ao treinar com Question e Query: {e}")

def treinar_doc(vn,
                docs: List | None = None
                ) -> None:
    try:
        if docs is None:
            raise ValueError("O 'docs' passado não corresponde ao valor esperado: 'List'")
        for doc in docs:
            vn.train(documentation = doc)
        
        log.info("Treinamento de Documentação realizado com sucesso.")
        
    except Exception as e:
        log.exception(f"Erro Inesperado ao tentar treinar com documentation: {e}")

def definir_prompt(vn,
                   prompt: str
                   ) -> None:
    try:
        if prompt is None:
            raise ValueError("O 'docs' passado não corresponde ao valor esperado: 'str'")
        vn.config['sql_prompt_preamble'] = prompt
        
        log.info("Prompt inserido com sucesso.")
    except Exception as e:
        log.exception(f"Erro Inesperado ao tentar definir o prompt: {e}")

def tratamento_init(vn,
                    path_arquivos_treinamento: str,
                    nome_arquivo_ddl_sql: str | None = None,
                    nome_arquivo_qa: str | None = None,
                    nome_arquivo_docs: str | None = None,
                    nome_arquivo_prompt: str | None = None,
                ) -> None:
    try:
        if nome_arquivo_ddl_sql is not None:
            treinar_ddl(
                vn=vn,
                ddl_sql=leitura_arquivos_treinamento(
                    nome_arquivo_ddl_sql,
                    path_arquivos_treinamento,
                ),
            )

        if nome_arquivo_qa is not None:
            treinar_qa(
                vn=vn,
                qa=leitura_arquivos_treinamento(
                    nome_arquivo_qa,
                    path_arquivos_treinamento,
                ),
            )

        if nome_arquivo_docs is not None:
            treinar_doc(
                vn=vn,
                docs=leitura_arquivos_treinamento(
                    nome_arquivo_docs,
                    path_arquivos_treinamento,
                ),
            )

        if nome_arquivo_prompt is not None:
            definir_prompt(
                vn=vn,
                prompt=leitura_arquivos_treinamento(
                    nome_arquivo_prompt,
                    path_arquivos_treinamento,
                ),
            )

    except Exception as e:
        log.exception(f"Erro desconhecido no treinamento: {e}")


if __name__ == "__main__":
    
    from vanna_client import vanna_init
    
    vn = vanna_init()
    
    path_arquivos_treinamento = "src/arquivos_treinamento"
    nome_arquivo_ddl = "consulta_ddl.pkl"
    nome_arquivo_qa = "qa.pkl"
    nome_arquivo_docs = "documentations.pkl"
    nome_arquivo_prompt = "prompt.pkl"
    
    tratamento_init(vn,
                    path_arquivos_treinamento=path_arquivos_treinamento,
                    nome_arquivo_ddl_sql=nome_arquivo_ddl,
                    nome_arquivo_qa=nome_arquivo_qa,
                    nome_arquivo_docs=nome_arquivo_docs,
                    nome_arquivo_prompt=nome_arquivo_prompt
                    )