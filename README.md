<p align="center">
  <a href="https://ollama.com/">
    <img src="https://img.shields.io/badge/ollama-1.0.0-green?logo=ollama&logoColor=white" />
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white" />
  </a>
  <a href="https://www.textualize.io/">
    <img src="https://img.shields.io/badge/framework-Textual-5967FF?logo=textual" />
  </a>
</p>

Todos os programas que eu testei com AI local do Ollama demoravam muito para responder. Então decidi criar um programa que fosse mais rápido e inteligente usando skills e tools.

#### Tools atuais: 

- "web_search" - Modelo decide o que pesquisar na internet 
- "browse_page": Modelo visita páginas relevantes e extrai informações
- "generate_diagram": Modelo gera diagramas do estilo BrModelo ou Astah
- "read_file": Modelo lê arquivos e extrai informações relevantes
- "write_file": Modelo escreve informações em arquivos
- "salvar_no_banco": Modelo decide se uma informação é importante e salva no banco de dados
- "pesquisar_no_banco": Modelo pesquisa informações no banco de dados
- "chamar_ai": Modelo chama outra IA para realizar tarefas específicas
- "cmd_tool": Modelo executa comandos no terminal
- "powershell_tool": Modelo executa comandos no PowerShell

O modelo também pode editar arquivos independente de seu tamanho.

#### Modelos recomendados:
- "qwen2.5-7b"