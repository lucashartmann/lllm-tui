from typing import Optional
import ollama
from database import shelve
from model import modelo

def _resolve_model(model: Optional[str] = None) -> str:
    candidate = (model or "").strip()
    if candidate:
        return candidate

    try:
        listed = ollama.list()
        models = getattr(listed, "models", [])
        if models:
            first = getattr(models[0], "model", "")
            if first:
                return first
    except Exception:
        pass

    raise ValueError("Nenhum modelo Ollama configurado para gerar diagrama")


def chamar_ai(mensagem, model: Optional[str] = None):
    print(f"Mensagem recebida para chamar_ai: '{mensagem}' com modelo: '{model}'")
    modelos = modelo.Modelo.listar_nome_modelos()
    if shelve.carregar_modelo():
        model_name = shelve.carregar_modelo()
    else:
        model_name = _resolve_model(model)
    resposta = ollama.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": f"Você é um assistente que pode chamar outras inteligências artificiais para responder a perguntas. Os modelos disponíveis são: {', '.join(modelos)}. Para chamar um modelo, responda com o formato: 'chamar [nome do modelo]: [mensagem para o modelo]'."},
            {"role": "user", "content": mensagem},
        ]
    )
    
    resposta_content = resposta["message"]["content"]
    
    if resposta_content.startswith("chamar"):
        try:
            _, rest = resposta_content.split(" ", 1)
            model_name, model_message = rest.split(":", 1)
            model_name = model_name.strip()
            model_message = model_message.strip()
            
            if model_name in modelos:
                print(f"Chamando modelo '{model_name}' com mensagem: '{model_message}'")
                resposta_modelo = enviar_mensagem_com_ferramentas(model_name, f"Você é um modelo chamado {model_name}. Responda à seguinte mensagem: {model_message}")
                
                return resposta_modelo
            else:
                return f"Modelo '{model_name}' não encontrado."
        except Exception as e:
            return f"Erro ao processar a chamada: {str(e)}"
    else:
        return resposta_content
   
   
def enviar_mensagem_com_ferramentas(self, modelo, mensagem, tools=None):
        from tools import TOOLS_MAP, TOOLS_SCHEMA
        tools = TOOLS_SCHEMA
        try:
            messages = [{"role": "system", "content": mensagem}]
            max_steps = 8
            steps = 0
            links_ultima_busca = []

            while steps < max_steps:
                steps += 1

                response = ollama.chat(
                    model=modelo,
                    messages=messages,
                    tools=tools
                )

                msg = response["message"]
                tool_calls = msg.get("tool_calls")

                if not tool_calls:
                    fallback_tool_call = self._extrair_tool_call_de_conteudo(
                        msg.get("content"))
                    if fallback_tool_call:
                        tool_calls = [{
                            "id": f"fallback_{steps}",
                            "function": {
                                "name": fallback_tool_call["name"],
                                "arguments": fallback_tool_call["arguments"],
                            }
                        }]
                        msg = {
                            **msg,
                            "tool_calls": tool_calls,
                            "content": "",
                        }

                if tool_calls:
                    messages.append(msg)

                    for idx, call in enumerate(tool_calls, start=1):
                        name = call["function"]["name"]
                        args = self._normalizar_args_tool(
                            call["function"].get("arguments", {})
                        )
                        tool_call_id = call.get("id", f"call_{steps}_{idx}")

                        print(f"[TOOL CALL] {name} -> {args}")
                        tool_fn = TOOLS_MAP[name]

                        if name == "web_search":

                            result = tool_fn(**args)
                            links_ultima_busca = self._extrair_links_de_texto(
                                str(result)
                            )

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": str(result)
                            })

                            messages.append({
                                "role": "user",
                                "content": "Agora abra os links mais relevantes usando browse_page."
                            })

                        elif name == "browse_page":
                            url = str(args.get("url", "")).strip()
                            if not self._url_valida_para_browse(url):
                                fallback = next(
                                    (u for u in links_ultima_busca if self._url_valida_para_browse(
                                        u)),
                                    None,
                                )
                                if fallback:
                                    args["url"] = fallback
                                    if not args.get("instructions"):
                                        args["instructions"] = "Extraia os fatos principais relevantes para a pergunta do usuario."
                                else:
                                    result = "Erro: URL invalida para browse_page e nenhuma URL valida foi encontrada na ultima busca."
                                    messages.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call_id,
                                        "content": str(result)
                                    })
                                    continue

                            result = tool_fn(**args)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": str(result)
                            })

                        elif name == "generate_diagram":
                            args["request"] = str(args.get("request") or mensagem)
                            args["model"] = str(modelo or "")
                         
                            result = tool_fn(**args)
                            
                            print("[FINAL TOOL RESULT]")
                            print(result)

                            return result

                        else:

                            result = tool_fn(**args)

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": str(result)
                            })
                    continue

                return msg["content"]
            return "Erro: limite de execuções atingido"

        except Exception as e:
            print(f"ERRO! {e}")
            return None