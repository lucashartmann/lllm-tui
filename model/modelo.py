import math
import re
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import ollama
from tools import TOOLS_MAP, TOOLS_SCHEMA

class Modelo:

    def __init__(self):
        self.modelo = ""
        self.embedding_model = "nomic-embed-text"
        self.ultima_metrica = {}
        self.ultimo_contexto_stats = {}

    def set_modelo(self, modelo):
        self.modelo = modelo

    def deletar(self, modelo):
        try:
            ollama.delete(modelo)
            return True
        except Exception as e:
            print(f"ERRO! Modelo.deletar {e}")
            return False

    def descarregar_modelo(self):
        try:
            ollama.generate(
                model=self.modelo,
                prompt="",
                keep_alive=0
            )
            return True
        except Exception as e:
            print(e)
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

    def obter_max_retry_sintaxe(self) -> int:
        nome = str(self.modelo or "").lower()
        match = re.search(r"(\d+(?:\.\d+)?)b", nome)
        if not match:
            return 1

        try:
            tamanho_b = float(match.group(1))
        except Exception:
            return 1

        return 2 if tamanho_b <= 3.0 else 1

    def _show_model_info(self):
        try:
            if not self.modelo:
                return {}
            info = ollama.show(self.modelo)
            return info if isinstance(info, dict) else {}
        except Exception as e:
            print(f"ERRO! Modelo._show_model_info {e}")
            return {}
        
    def _show_model_info2(self, modelo):
        try:
            if not modelo:
                return {}
            info = ollama.show(modelo)
            # info["name"] = modelo
            return self.extrair_info_modelo(info)
        except Exception as e:
            print(f"ERRO! Modelo._show_model_info {e}")
            return {}
        
    def extrair_info_modelo(self, info):
        try:
         
            modelinfo = info.get("modelinfo", {})
            details = info.get("details", {})
            capabilities = info.get("capabilities", [])

            data = {
                "contexto": self.pegar_valor_por_sufixo(modelinfo, "context_length"),
                "parametros": details.parameter_size if hasattr(details, "parameter_size") else None,
                "quantizacao": details.quantization_level if hasattr(details, "quantization_level") else None,
                "completion": "completion" in capabilities,
                "insert": "insert" in capabilities,
                "arquitetura": modelinfo.get("general.architecture"),
                "embedding": self.pegar_valor_por_sufixo(modelinfo, "embedding_length"),
                "layers": self.pegar_valor_por_sufixo(modelinfo, "block_count"),
                "capabilidades": capabilities,
            }

            return data

        except Exception as e:
            print(f"Erro ao extrair info: {e}")
            return {}
        


    @staticmethod
    def estimar_tokens(texto: str) -> int:
        if not texto:
            return 0
        return max(1, int(len(texto) / 4))

    def obter_limite_contexto(self, padrao: int = 4096) -> int:
        info = self._show_model_info()

        candidatos = []

        model_info = info.get("model_info", {}) if isinstance(
            info, dict) else {}
        for key, value in model_info.items():
            key_lower = str(key).lower()
            if any(k in key_lower for k in ["context", "num_ctx", "max_position", "seq_length"]):
                try:
                    candidatos.append(int(value))
                except Exception:
                    pass

        parameters = info.get("parameters", "")
        if isinstance(parameters, str):
            for match in re.findall(r"(?:num_ctx|context_length|max_context)\s+(\d+)", parameters, flags=re.IGNORECASE):
                try:
                    candidatos.append(int(match))
                except Exception:
                    pass

        options = info.get("options", {}) if isinstance(info, dict) else {}
        if isinstance(options, dict):
            for key in ["num_ctx", "context_length", "max_context"]:
                if key in options:
                    try:
                        candidatos.append(int(options[key]))
                    except Exception:
                        pass

        validos = [c for c in candidatos if c > 256]
        if validos:
            return max(validos)
        return padrao

 

    def gerar_embedding(self, texto: str, embedding_model: Optional[str] = None) -> Optional[List[float]]:
        model_name = embedding_model or self.embedding_model
        candidatos = [model_name]
        if model_name != self.embedding_model:
            candidatos.append(self.embedding_model)

        for nome_modelo in candidatos:
            try:
                resposta = ollama.embed(model=nome_modelo, input=texto)
                embeddings = resposta.get("embeddings", []) if isinstance(
                    resposta, dict) else []
                if embeddings and isinstance(embeddings[0], list):
                    return embeddings[0]
            except Exception:
                pass

            try:
                resposta = ollama.embeddings(model=nome_modelo, prompt=texto)
                if isinstance(resposta, dict) and isinstance(resposta.get("embedding"), list):
                    return resposta["embedding"]
            except Exception:
                pass

        return None

    @staticmethod
    def _similaridade_cosseno(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return -1.0

        produto = sum(a * b for a, b in zip(v1, v2))
        norma_1 = math.sqrt(sum(a * a for a in v1))
        norma_2 = math.sqrt(sum(b * b for b in v2))
        if norma_1 == 0 or norma_2 == 0:
            return -1.0
        return produto / (norma_1 * norma_2)
    
    def enviar_mensagem_com_ferramentas(self, mensagem, tools=TOOLS_SCHEMA):
        try:
            messages = [
                {"role": "user", "content": mensagem}
            ]

            while True:
                response = ollama.chat(
                    model=self.modelo,
                    messages=messages,
                    tools=tools
                )

                msg = response["message"]

             
                if "tool_calls" in msg:
                    messages.append(msg)

                    for call in msg["tool_calls"]:
                        name = call["function"]["name"]
                        args = call["function"]["arguments"]

                        print(f"[TOOL CALL] {name} -> {args}")
                        
                        if name == "web_search":
                            result = TOOLS_MAP[name](**args)

                            messages.append({
                                "role": "tool",
                                "content": str(result)
                            })

                            messages.append({
                                "role": "user",
                                "content": "Agora abra um dos links usando browse_page."
                            })

                            
                        
                        else:

                            result = TOOLS_MAP[name](**args)

                            messages.append({
                                "role": "tool",
                                "content": str(result)
                            })
                    continue
                             

                return msg["content"]

        except Exception as e:
            print(f"ERRO! {e}")
            return None


    def enviar_mensagem(self, mensagem, caminho_image=None, on_chunk: Optional[Callable[[str], None]] = None, tools=TOOLS_SCHEMA):
        if tools:
            return self.enviar_mensagem_com_ferramentas(mensagem, tools=tools)
        try:
            acumulado = ""
            ultima_parte = None
            if not caminho_image:
                resposta = ollama.chat(
                    model=self.modelo,
                    messages=[{'role': 'user', 'content': f'{mensagem}'}],
                    stream=True,
                    tools=tools,
                )
                
                msg = resposta["message"]
                if "tool_calls" in msg:
                    for call in msg["tool_calls"]:
                        name = call["function"]["name"]
                        args = call["function"]["arguments"]

                        print(f"[TOOL CALL] {name} -> {args}")

                        result = TOOLS_MAP[name](**args)


                        messages.append(msg)
                        messages.append({
                            "role": "tool",
                            "content": str(result)
                        })

                        continue
                
            else:
                imagens = caminho_image if isinstance(
                    caminho_image, list) else [caminho_image]
                resposta = ollama.chat(
                    model=self.modelo,
                    messages=[
                        {'role': 'user', 'content': f'{mensagem}', 'images': imagens}],
                    stream=True,
                    tools=tools,
                )

            for parte in resposta:
                ultima_parte = parte
                conteudo = ""

                if isinstance(parte, dict):
                    message = parte.get("message", {})
                    if isinstance(message, dict):
                        conteudo = message.get("content", "") or ""
                else:
                    message_obj = getattr(parte, "message", None)
                    if message_obj is not None:
                        conteudo = getattr(message_obj, "content", "") or ""

                if conteudo:
                    acumulado += conteudo
                    if on_chunk:
                        on_chunk(acumulado)

            self.ultima_metrica = self._extrair_metricas_ollama(ultima_parte)

            return acumulado
        except Exception as e:
            print(f"ERRO! Modelo.enviar_mensagem {e}")
            self.ultima_metrica = {}
            return None

    @staticmethod
    def _extrair_metricas_ollama(parte) -> dict:
        if not parte:
            return {}

        campos = [
            "prompt_eval_count",
            "eval_count",
            "prompt_eval_duration",
            "eval_duration",
            "total_duration",
        ]

        metricas = {}
        if isinstance(parte, dict):
            for campo in campos:
                valor = parte.get(campo)
                if valor is not None:
                    metricas[campo] = valor
            return metricas

        for campo in campos:
            valor = getattr(parte, campo, None)
            if valor is not None:
                metricas[campo] = valor
        return metricas
