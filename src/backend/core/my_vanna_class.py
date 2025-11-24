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
    
    """
    Classe principal de integração entre o Vanna, o banco vetorial Chroma
    e a API da OpenAI.

    Esta classe herda de `ChromaDB_VectorStore` e `OpenAI_Chat`, fornecendo
    métodos utilitários para:

    - Ler arquivos de treinamento (DDL, Q&A, documentação e prompt);
    - Treinar o Vanna com diferentes tipos de dados;
    - Configurar o prompt SQL padrão;
    - Orquestrar o processo de inicialização e treinamento;
    - Verificar se a base vetorial já foi treinada;
    - Conectar ao banco SQLite configurado.

    A instância deve ser inicializada com um dicionário de configuração
    contendo, no mínimo, as chaves `openai.api_key`, `openai.model`,
    `path` e `chroma.persist_directory`.
    """
    
    def __init__(self, config=None):
        
        """
        Inicializa a instância do MyVanna com as configurações fornecidas.

        Parameters
        ----------
        config : dict
            Dicionário de configuração contendo parâmetros para conexão
            com a OpenAI e com o ChromaDB. Deve incluir, por exemplo:
            - ``config['openai']['api_key']``: chave da API OpenAI;
            - ``config['openai']['model']``: modelo a ser utilizado;
            - ``config['path']``: diretório base de dados;
            - ``config['chroma']['persist_directory']``: diretório de
              persistência do banco vetorial Chroma.

        Raises
        ------
        ValueError
            Se `config` for None.
        """
        
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
        
        """
        Lê um arquivo de treinamento serializado (pickle) e retorna seu conteúdo.

        Parameters
        ----------
        nome_arquivo : str
            Nome do arquivo de treinamento (por exemplo, ``'qa.pkl'``).
        path_arquivo : str
            Caminho do diretório onde o arquivo está armazenado.

        Returns
        -------
        Any
            Objeto desserializado a partir do arquivo (por exemplo,
            uma lista de dicionários, uma string SQL, uma lista de textos, etc.).

        Raises
        ------
        FileNotFoundError
            Se o arquivo não for encontrado no caminho informado.
        ValueError
            Se o arquivo for lido, mas estiver vazio ou com conteúdo inválido.
        Exception
            Para erros inesperados de leitura ou desserialização.

        Notes
        -----
        - O método assume que o arquivo foi serializado com `pickle.dump`.
        - Em caso de erro, a exceção é registrada no log e `None` é retornado.
        """
        
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

        Parameters
        ----------
        ddl_sql : str, optional
            Comando SQL que retorna um DataFrame com a coluna ``sql``
            contendo os DDLs das tabelas (por exemplo, uma consulta
            em ``sqlite_master``). Se for None, o método lança um erro.

        Returns
        -------
        None
            O resultado do treinamento é registrado no banco vetorial
            interno, sem retorno explícito.

        Raises
        ------
        ValueError
            Se `ddl_sql` for None.
        Exception
            Para erros inesperados durante a execução do SQL ou do treino.

        Notes
        -----
        - O método executa `self.run_sql(ddl_sql)` e espera que o DataFrame
          resultante possua uma coluna chamada ``'sql'``.
        - Cada DDL não vazio é enviado individualmente para
          `self.train(ddl=ddl)`.
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
        
        """
        Treina o Vanna com pares de pergunta e SQL (Q&A).

        Parameters
        ----------
        qa : list of dict
            Lista de dicionários, onde cada item deve conter as chaves:
            - ``'question'``: texto da pergunta em linguagem natural;
            - ``'sql'``: consulta SQL correspondente.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            Se `qa` for None.
        Exception
            Para erros inesperados durante o treinamento.

        Notes
        -----
        - Cada item da lista é enviado para `self.train(question=..., sql=...)`.
        """
        
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
        
        """
        Treina o Vanna com documentação textual livre.

        Parameters
        ----------
        docs : list, optional
            Lista de textos (strings) com descrições, documentação de tabelas,
            explicações de negócio, etc. Se for None, o método lança um erro.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            Se `docs` for None.
        Exception
            Para erros inesperados durante o treinamento.

        Notes
        -----
        - Cada item da lista é enviado para `self.train(documentation=doc)`.
        """
        
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
        
        """
        Define o prompt padrão utilizado na geração de SQL pelo Vanna.

        Parameters
        ----------
        prompt : str
            Texto do prompt a ser utilizado como preâmbulo na geração de SQL.
            Normalmente contém instruções de estilo, regras de negócio e
            contexto sobre o banco de dados.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            Se `prompt` for None.
        Exception
            Para erros inesperados ao atualizar a configuração.
        """
        
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
        
        """
        Orquestra o fluxo completo de treinamento inicial do Vanna.

        Este método:
        1. Lê os arquivos de DDL, Q&A, documentação e prompt (pkl),
           usando `leitura_arquivos_treinamento`;
        2. Chama os métodos de treinamento correspondentes:
           `treinar_ddl`, `treinar_qa`, `treinar_doc` e `definir_prompt`.

        Parameters
        ----------
        path_arquivos_treinamento : str, optional
            Caminho base onde os arquivos de treinamento estão armazenados.
            Se None, utiliza `self.path_arquivos_treinamento`.
        nome_arquivo_ddl_sql : str, optional
            Nome do arquivo com a query de DDL (pickle). Se None, utiliza
            `self.nome_arquivo_ddl`.
        nome_arquivo_qa : str, optional
            Nome do arquivo com os pares pergunta-SQL (pickle). Se None,
            utiliza `self.nome_arquivo_qa`.
        nome_arquivo_docs : str, optional
            Nome do arquivo com a lista de documentações (pickle). Se None,
            utiliza `self.nome_arquivo_docs`.
        nome_arquivo_prompt : str, optional
            Nome do arquivo com o prompt padrão (pickle). Se None,
            utiliza `self.nome_arquivo_prompt`.

        Returns
        -------
        None

        Raises
        ------
        Exception
            Para erros inesperados no processo de leitura ou treinamento.

        Notes
        -----
        - Caso algum dos nomes de arquivo seja definido como None explicitamente,
          a etapa correspondente é simplesmente ignorada.
        """
        
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
        Cria e inicializa uma instância de ``MyVanna`` com configuração padrão,
        conectando ao SQLite e ao banco vetorial Chroma.

        Parameters
        ----------
        model_name : str, optional
            Nome do modelo OpenAI a ser usado.
            Default: ``"gpt-3.5-turbo"``.
        set_db_path : str, optional
            Caminho base do diretório de dados (onde está o SQLite e o Chroma).
            Default: diretório `DATA_DIR`.
        chroma_dir : str, optional
            Nome ou caminho do diretório de persistência do ChromaDB.
            Default: ``"chroma.sqlite3"``.
        bd_path : str, optional
            Nome do arquivo de banco SQLite local.
            Default: ``"db_olist.sqlite"``.

        Returns
        -------
        MyVanna or None
            Instância já conectada ao SQLite e configurada para uso
            com o ChromaDB, ou None em caso de falha.

        Raises
        ------
        EnvironmentError
            Se a variável de ambiente ``OPENAI_API_KEY`` não estiver definida.
        FileNotFoundError
            Se o arquivo de banco de dados SQLite não for encontrado.
        Exception
            Para outros erros inesperados.

        Notes
        -----
        - Este método de classe é o ponto de entrada recomendado para criar
          a instância em produção.
        - A conexão com o SQLite é feita via `vn.connect_to_sqlite(url=...)`.
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
        
        """
        Verifica se a base vetorial do Vanna já foi treinada.

        A verificação é feita em dois passos:

        1. Confere se o arquivo/diretório de persistência do Chroma existe;
        2. Confere se o diretório base de dados (`self.set_db_path`) contém
           exatamente 5 itens (heurística definida para indicar que o
           treinamento já ocorreu).

        Returns
        -------
        bool
            ``True`` se a base de treinamento for considerada existente e
            completa, ``False`` caso contrário.

        Raises
        ------
        Exception
            Para erros inesperados ao acessar o sistema de arquivos.

        Notes
        -----
        - Caso algum critério não seja atendido, uma mensagem é registrada
          no log explicando o motivo.
        """
        
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