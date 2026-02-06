from ollama import chat
from ollama import ChatResponse
from ollama import ListResponse
import ollama

ollama.generate


class Modelo:

    def __init__(self):
        self.modelo = ""
    
    def set_modelo(self, modelo):
        self.modelo = modelo

    def deletar(self, modelo):
        try:
            ollama.delete(modelo)
            return True
        except Exception as e:
            print(f"ERRO! Modelo.deletar {e}")
            return False

    def pull(self, modelo):
        try:
            ollama.pull(modelo)
            return True
        except Exception as e:
            print(f"ERRO! Modelo.pull {e}")
            return False

    def listar_nome_modelos(self):
        lista = []
        try:
            response = ollama.list()
            for modelo in response.models:
                lista.append(modelo.model)
            return lista
        except Exception as e:
            print(f"ERRO! Modelo.listar_nome_modelos {e}")
            return []

    def enviar_mensagem(self, mensagem, caminho_image=None):
        try:
            if not caminho_image:
                resposta = ollama.chat(model=self.modelo, messages=[
                    {'role': 'user', 'content': f'{mensagem}'}])
            else:
                print(caminho_image)
                resposta = ollama.chat(model=self.modelo, messages=[
                    {'role': 'user', 'content': f'{mensagem}', 'images': [caminho_image]}])
            return resposta.message.content
        except Exception as e:
            print(f"ERRO! Modelo.enviar_mensagem {e}")
            return None
