import streamlit as st
import requests

api_url = "https://ia-sql-dataviz.onrender.com/pergunta"

def front():
    
    """
    Renderiza a interface principal do aplicativo Streamlit.

    A função realiza os seguintes passos:

    1. Define o título da aplicação ("Bem vindo ao Text-to-SQL");
    2. Exibe instruções básicas de uso em formato de lista;
    3. Mostra um exemplo de pergunta em linguagem natural;
    4. Cria um campo de texto para o usuário digitar sua própria pergunta;
    5. (Trecho omitido neste arquivo) Envia a pergunta para a API usando
       ``requests`` (método HTTP POST, geralmente) e aguarda a resposta;
    6. Processa o retorno da API, fazendo um pequeno tratamento de string
       para limpar caracteres de escape e quebras de linha;
    7. Em caso de sucesso, exibe uma mensagem de sucesso e o SQL gerado
       em um bloco de código com destaque de sintaxe;
    8. Em caso de erro HTTP ou exceção inesperada, exibe uma mensagem de erro
       amigável no Streamlit.

    Notes
    -----
    - Esta função não retorna nenhum valor; ela apenas manipula o estado
      da página Streamlit (componentes de entrada/saída).
    - O trecho representado por ``...`` neste arquivo deve conter a lógica
      de envio da requisição (por exemplo, ``requests.post(api_url, json={...})``)
      e o manuseio do objeto ``response`` antes do bloco que já existe com
      ``response.text``, ``sql_bruto`` e ``sql_limpo``.
    """
    
    st.title("Bem vindo ao Text-to-SQL")
    
    st.markdown("""
                1. Faça sua pergunta sobre os dados aqui.
                2. Depois aperte no botão enviar e aguarde pela sua resposta."""
                )
    
    st.markdown("Faça o ranking dos 10 melhores vendedores por valor total de venda?")
    
    pergunta = st.text_input("Digite sua Pergunta")
    
    if st.button("Enviar mensagem"):
        if not pergunta.strip():
            st.warning("Digite uma pergunta válida.")
        else:
            with st.spinner("Consultando a API..."):
                try:
                    payload = {"pergunta":pergunta}
                    response = requests.post(api_url, json = payload)
                    response.raise_for_status()
                    
                    sql_bruto = response.text
                    sql_limpo = sql_bruto.strip('"').replace('\\n', '\n').replace('\\', '')
                    
                    st.success("Sucesso!")
                    st.write("Resposta da API:")
                    st.code(sql_limpo, language='sql')
                    
                except requests.exceptions.HTTPError as err:
                    st.error(f"Erro na requisição: {err}")
                except Exception as e:
                    st.error(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    
    front()