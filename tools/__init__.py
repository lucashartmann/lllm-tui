from tools import arquivo, diagrama, internet

TOOLS_MAP = {
    "web_search": internet.web_search,
    "browse_page": internet.browse_page,
    "search_images": internet.search_images,
    "search_videos": internet.search_videos,
    "learn_topic": internet.learn_topic,
    # "generate_diagram": diagrama.generate_diagram,
    "read_file": arquivo.read_file,
    "write_file": arquivo.write_file,
}

TOOLS_SCHEMA = [
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
                        "num_results": {
                            "type": "integer",
                            "description": "O número de resultados a serem retornados"
                        }
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
