from openai import OpenAI
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore

from typing import Dict, List
from pathlib import Path
import logging
import pickle
import os

log = logging.getLogger(__name__)

# === Caminhos base, independentes de onde o app roda (local/Render) ===
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
TRAIN_DIR = BACKEND_DIR / "arquivos_treinamento"
DB_OLIST_PATH = DATA_DIR / "db_olist.sqlite"

class MyVanna( ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        
        if config is None:
            raise ValueError("config não pode ser None. Use MyVanna.vanna_configs() para criar a instância ou passe a config dentro dos parâmetros de inicialização.")
        
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)
        self.client = OpenAI(api_key=config['openai']['api_key'])
        
        self.path_arquivos_treinamento = str(TRAIN_DIR)
        self.nome_arquivo_ddl = "consulta_ddl.pkl"
        self.nome_arquivo_qa = "qa.pkl"
        self.nome_arquivo_docs = "documentations.pkl"
        self.nome_arquivo_prompt = "prompt.pkl"
        
        self.model_name = "gpt-3.5-turbo"
        self.set_db_path = str(DATA_DIR)
        self.chroma_dir = "chroma.sqlite3"
        self.bd_path = "db_olist.sqlite"
    
        
    def leitura_arquivos_treinamento(self,
                                    nome_arquivo: str,
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

    def treinar_ddl(self,
                    ddl_sql: str | None = None
                    ) -> None:
        """
        Treina o Vanna com os DDLs das tabelas do SQLite.
        Retorna a contagem de objetos treinados.
        """
        try:
            if ddl_sql is None:
                raise ValueError("Não foi passado nenhuma query para treinamento")
            
            df_ddl = self.run_sql(ddl_sql)
            n = 0
            for _, row in df_ddl.iterrows():
                ddl = (row["sql"] or "").strip()
                if ddl:
                    self.train(ddl=ddl)
                    n+=1
            
            log.info(f"Treinamento DDL concluído: {n} objetos adicionados")
        
        except ValueError as e:
            log.error(f"Erro nos parâmetros: {e}", exc_info=True)
        except Exception as e:
            log.error(f"Erro inesperado ao treinar com ddl: {e}", exc_info=True)

    def treinar_qa(self,
                qa: List[Dict[str,str]]
                ) -> None:
        
        try:
            if qa is None:
                raise ValueError("O 'qa' passado não corresponde ao valor esperado: 'List[Dict[str,str]]'")
            
            for q in qa:
                self.train(question=q["question"], sql=q["sql"])
                
            log.info("Treinamento de Perguntas e Respostas realizado com sucesso.")
        except Exception as e:
            log.exception(f"Erro Inesperado ao treinar com Question e Query: {e}")

    def treinar_doc(self,
                    docs: List | None = None
                    ) -> None:
        try:
            if docs is None:
                raise ValueError("O 'docs' passado não corresponde ao valor esperado: 'List'")
            for doc in docs:
                self.train(documentation = doc)
            
            log.info("Treinamento de Documentação realizado com sucesso.")
            
        except Exception as e:
            log.exception(f"Erro Inesperado ao tentar treinar com documentation: {e}")

    def definir_prompt(self,
                    prompt: str
                    ) -> None:
        try:
            if prompt is None:
                raise ValueError("O 'docs' passado não corresponde ao valor esperado: 'str'")
            self.config['sql_prompt_preamble'] = prompt
            
            log.info("Prompt inserido com sucesso.")
        except Exception as e:
            log.exception(f"Erro Inesperado ao tentar definir o prompt: {e}")

    def tratamento_init(self,
                        path_arquivos_treinamento: str | None = None,
                        nome_arquivo_ddl_sql: str | None = None,
                        nome_arquivo_qa: str | None = None,
                        nome_arquivo_docs: str | None = None,
                        nome_arquivo_prompt: str | None = None,
                    ) -> None:
        
        path       = self.path_arquivos_treinamento if path_arquivos_treinamento is None else path_arquivos_treinamento
        nome_ddl   = self.nome_arquivo_ddl          if nome_arquivo_ddl_sql      is None else nome_arquivo_ddl_sql
        nome_qa    = self.nome_arquivo_qa           if nome_arquivo_qa           is None else nome_arquivo_qa
        nome_docs  = self.nome_arquivo_docs         if nome_arquivo_docs         is None else nome_arquivo_docs
        nome_prompt= self.nome_arquivo_prompt       if nome_arquivo_prompt       is None else nome_arquivo_prompt
        
        try:
            if nome_ddl is not None:
                self.treinar_ddl(
                    ddl_sql=self.leitura_arquivos_treinamento(
                        nome_ddl,
                        path,
                    ),
                )

            if nome_qa is not None:
                self.treinar_qa(
                    qa=self.leitura_arquivos_treinamento(
                        nome_qa,
                        path,
                    ),
                )

            if nome_docs is not None:
                self.treinar_doc(
                    docs=self.leitura_arquivos_treinamento(
                        nome_docs,
                        path,
                    ),
                )

            if nome_prompt is not None:
                self.definir_prompt(
                    prompt=self.leitura_arquivos_treinamento(
                        nome_prompt,
                        path,
                    ),
                )

        except Exception as e:
            log.exception(f"Erro desconhecido no treinamento: {e}")
    
    @classmethod
    def vanna_configs(cls,
                        model_name: str | None = None,
                        set_db_path: str | None = None,
                        chroma_dir: str | None = None,
                        bd_path: str | None = None
                        ) -> None:
    
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
        mn   = "gpt-3.5-turbo"    if model_name  is None else model_name
        sdbp = str(DATA_DIR)      if set_db_path is None else set_db_path
        cd   = "chroma.sqlite3"   if chroma_dir  is None else chroma_dir
        bdp  = "db_olist.sqlite"  if bd_path     is None else bd_path
        
        
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise EnvironmentError("Variável OPENAI_API_KEY não definida no ambiente")
            
            vn = MyVanna(
                config={
                    'path' : sdbp,
                    'openai': {
                        'api_key': api_key,
                        'model': mn
                    },
                    'chroma': {
                        'persist_directory': cd
                    }
                }
            )
            
            full_path_olist = sdbp+"/"+bdp
            vn.connect_to_sqlite(url=full_path_olist)
            log.info(f"Conexão com SQLite estabelecida com sucesso: {full_path_olist}")
            log.info(f"Conexão com Croma estabelecida com sucesso: {cd}")
            
            return vn
        
        except EnvironmentError as e:
            log.error(f"Erro de ambiente: {e}", exc_info=True)
        except FileNotFoundError as e:
            log.error(f"Banco de dados não encontrado: {e}", exc_info=True)
        except Exception as e:
            log.error(f"Falha inesperada ao inicializar o Vanna: {e}", exc_info=True)
        return None
    
    def esta_treinado(self):
        
        try:
            chroma_path = Path(self.set_db_path) / self.chroma_dir
            
            if not chroma_path.exists():
                log.warning(f"O arquivo {chroma_path} não existe.")
                return False
            
            pasta = Path(self.set_db_path)
            
            if not (len(list(pasta.iterdir())) == 5):
                log.warning(f"O caminho {pasta}  existe, mas ainda não ocorreu o treinamento.")
                return False
            
            log.info("Base Chroma - Vanna já treinada")
            return True
        except Exception as e:
            log.exception(f"Erro Inesperado: {e}")

if __name__ == "__main__":
    
    vn = MyVanna.vanna_configs()
    
    if not vn.esta_treinado():
        vn.tratamento_init()
        log.info("Treinamento encerrado com sucesso")