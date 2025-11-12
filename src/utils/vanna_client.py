import os
import sqlite3
from my_vanna_class import MyVanna

def app_init():
    vn = MyVanna(
        config={
            'openai': {
                'api_key': os.getenv('OPENAI_API_KEY'), # TEM QUE VER COMO FUNCIONA EM PRODUÇÃO, QUAL ARQUIVO DE CONFIG DEVE SER PASSADO.
                'model': 'gpt-3.5-turbo'
            },
            'chroma': {
                'persist_directory': 'chroma-db'
            }
        }
    )
    
    vn.connect_to_sqlite( url = "../data/db_olist.sqlite")
    
    consulta_dll = """
                SELECT
                    name, sql
                FROM
                    sqlite_master
                WHERE type = 'table'
                ORDER BY
                    name;
    """
    ddl_olist = vn.run_sql(consulta_dll)
    
    treinamento = 0
    for _, row in ddl_olist.iterrows():
        tbl, ddl = row['name'], row['sql']
        if isinstance (ddl, str) and ddl.strip():
            vn.train(ddl = ddl)
            treinamento += 1
            print(f'DDL registrado: {ddl}')
    print(f'[ok] Tabelas treinadas: {treinamento}')

