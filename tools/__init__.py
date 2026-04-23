from tools import arquivo, diagrama, internet, banco, chamar_ai, cmd

TOOLS_MAP = {
    "web_search": internet.web_search,
    "browse_page": internet.browse_page,
    "search_images": internet.search_images,
    "search_videos": internet.search_videos,
    "learn_topic": internet.learn_topic,
    "generate_diagram": diagrama.gerar_diagrama,
    "read_file": arquivo.read_file,
    "write_file": arquivo.write_file,
    "salvar_no_banco": banco.salvar_no_banco,
    "pesquisar_no_banco": banco.pesquisar_no_banco,
    "chamar_ai": chamar_ai.chamar_ai,
    "cmd_tool": cmd.cmd_tool,
    "powershell_tool": cmd.powershell_tool,
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "cmd_tool",
            "description": "Executa um comando no terminal e retorna a saída"
        }
    },
    {
        "type": "function",
        "function": {
            "name": "powershell_tool",
            "description": "Executa um comando no PowerShell e retorna a saída"
        }
    },
    {
      "type": "function",
      "function": {
        "name": "chamar_ai",
        "description": "Chama outra inteligência artificial para responder a uma pergunta",
        "parameters": {
          "type": "object",
          "properties": {
            "mensagem": {"type": "string"},
            "model": {"type": "string"}
          },
          "required": ["mensagem"]
        }
      }
    },
    {
        "type": "function",
        "function": {
            "name": "search_images",
            "description": "Busca imagens na internet",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_videos",
            "description": "Busca vídeos na internet",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_diagram",
            "description": "Gera um diagrama a partir de uma descrição textual",
            "parameters": {
                "type": "object",
                "properties": {
                    "request": {
                        "type": "string",
                        "description": "A descrição do diagrama a ser gerado"
                    }
                },
                "required": ["request"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pesquisar_no_banco",
            "description": "Pesquisa informações no banco de dados",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A consulta de pesquisa para encontrar informações relevantes no banco de dados"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "salvar_no_banco",
            "description": "Salva uma informação no banco de dados",
            "parameters": {
                "type": "object",
                "properties": {
                    "info": {
                        "type": "string",
                        "description": "A informação a ser salva no banco de dados"
                    }
                },
                "required": ["info"]
            }
        }
    },
    {
        "type": "function",
        "function": {
                "name": "read_file",
                "description": "Lê o conteúdo de um arquivo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caminho": {
                            "type": "string",
                            "description": "Caminho do arquivo"
                        }
                    },
                    "required": ["caminho"]
                }
        }
    },
    {
        "type": "function",
        "function": {
                "name": "write_file",
                "description": "Escreve um conteúdo em um arquivo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caminho": {
                            "type": "string",
                            "description": "Caminho do arquivo"
                        },
                        "conteudo": {
                            "type": "string",
                            "description": "Conteúdo a ser escrito no arquivo"
                        }
                    },
                    "required": ["caminho", "conteudo"]
                }
        }
    },

    {
        "type": "function",
        "function": {
                "name": "learn_topic",
                "description": "Aprende sobre um tópico específico",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "O tópico a ser aprendido"
                        },
                        "max_pages": {
                            "type": "integer",
                            "description": "O número máximo de páginas a serem lidas"
                        },
                        "max_images": {
                            "type": "integer",
                            "description": "O número máximo de imagens a serem buscadas"
                        }
                    },
                    "required": ["topic"]
                }
        }
    },
    {
        "type": "function",
        "function": {
                "name": "web_search",
                "description": "Busca informações na internet",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "A consulta de busca"
                        },
                    },
                    "required": ["query"]
                }
        }
    },
    {
        "type": "function",
        "function": {
                "name": "browse_page",
                "description": "Navega para uma página da web",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "A URL da página a ser navegada"
                        },
                        "instructions": {
                            "type": "string",
                            "description": "Instruções sobre o que fazer na página"
                        }
                    },
                    "required": ["url"]
                }
        }
    }
]
