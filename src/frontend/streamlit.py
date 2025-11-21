import streamlit as st
import requests

api_url = "https://ia-sql-dataviz.onrender.com/pergunta"

def front():
    st.title("Bem vindo ao Text-to-SQL")
    
    text_area = """
                1. Faça sua pergunta sobre os dados aqui.
                2. Depois aperte no botão enviar e aguarde pela sua resposta."""
    
    pergunta = st.text_area(text_area)
    
    
    
    if st.button("Enviar mensagem"):
        try:
            payload = {"pergunta":pergunta}
            response = requests.post(api_url, json = payload)
            response.raise_for_status()
            
            st.success("Sucesso!")
            st.write("Resposta da API:")
            st.json(response.json()) # Mostra o JSON formatado
                
        except requests.exceptions.HTTPError as err:
            st.error(f"Erro na requisição: {err}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    front()