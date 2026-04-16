import io
import os
from llama_index.llms.ollama import Ollama
from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent
from view.app import App
import ollama
import numpy as np
from config import MODEL

EMBED_MODEL = "nomic-embed-text"

logs = []



def find_relevant(all_chunks, query, top_k=5):
    query_emb = embed(query)
    scored = []

    for i, item in enumerate(all_chunks):
        emb = embed(item["chunk"])
        score = cosine(query_emb, emb)
        scored.append((i, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [all_chunks[i] for i, _ in scored[:top_k]]

def chunk_files(files):
    all_chunks = []
    for path, content in files:
        chunks, positions = chunk_text(content)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "path": path,
                "chunk": chunk,
                "pos": positions[i]
            })
    return all_chunks

def chunk_text(text, size=800, overlap=100):
    chunks = []
    positions = []
    i = 0
    while i < len(text):
        chunk = text[i:i+size]
        chunks.append(chunk)
        positions.append((i, i+len(chunk)))
        i += size - overlap
    return chunks, positions


def embed(text):
    return np.array(
        ollama.embeddings(model=EMBED_MODEL, prompt=text)["embedding"]
    )


def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def find_relevant_chunks(chunks, query, top_k=3):
    query_emb = embed(query)
    pontuacoes = []

    for i, chunk in enumerate(chunks):
        emb = embed(chunk)
        pontuacao = cosine(query_emb, emb)
        pontuacoes.append((i, pontuacao))

    pontuacoes.sort(key=lambda x: x[1], reverse=True)
    return [i for i, _ in pontuacoes[:top_k]]

def summarize_folder(folder):
    files = load_files(folder)
    all_chunks = chunk_files(files)

    top_chunks = find_relevant(all_chunks, "resuma o conteúdo geral", top_k=8)

    context = "\n\n".join([c["chunk"] for c in top_chunks])

    response = ollama.chat(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": f"Faça um resumo geral dos arquivos:\n\n{context}"
        }]
    )

    return response["message"]["content"]


def edit_chunk(chunk, instruction):
    prompt = f"""
Edite o conteúdo abaixo conforme a instrução.

INSTRUÇÃO:
{instruction}

CONTEÚDO:
{chunk}

Retorne APENAS o conteúdo atualizado.
"""

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    
    logs.append(response["message"]["content"])
    print("LOGS DE EDIÇÃO:", logs)
    return response["message"]["content"]


def apply_edits(original, chunks, positions, edited_map):
    result = original
    offset = 0

    for i, (start, end) in enumerate(positions):
        if i in edited_map:
            new_chunk = edited_map[i]
            old_chunk = result[start+offset:end+offset]

            result = (
                result[:start+offset] +
                new_chunk +
                result[end+offset:]
            )

            offset += len(new_chunk) - len(old_chunk)

    return result


def edit_file(path, instruction):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    chunks, positions = chunk_text(content)

    relevant_ids = find_relevant_chunks(chunks, instruction)

    edited = {}
    for i in relevant_ids:
        edited[i] = edit_chunk(chunks[i], instruction)

    new_content = apply_edits(content, chunks, positions, edited)

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
def load_selected(files):
    data = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data.append((path, f.read()))
    return data

def alterar_lista_arquivos(files, instruction):
    all_chunks = chunk_files(files)

    relevant = find_relevant(all_chunks, instruction, top_k=10)

    edited_map = {}

    for item in relevant:
        new = edit_chunk(item["chunk"], instruction)

        path = item["path"]
        if path not in edited_map:
            edited_map[path] = []

        edited_map[path].append((item["pos"], new))


    for path, changes in edited_map.items():
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        offset = 0
        for (start, end), new_chunk in changes:
            content = (
                content[:start+offset] +
                new_chunk +
                content[end+offset:]
            )
            offset += len(new_chunk) - (end - start)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

def load_files(folder):
    files = []
    for root, _, filenames in os.walk(folder):
        for name in filenames:
            path = os.path.join(root, name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    files.append((path, f.read()))
            except:
                pass
    return files

def edit_from_folder(folder, instruction):
    files = load_files(folder)
    all_chunks = chunk_files(files)

    relevant = find_relevant(all_chunks, instruction)

    edited_map = {}

    for item in relevant:
        new = edit_chunk(item["chunk"], instruction)

        path = item["path"]
        if path not in edited_map:
            edited_map[path] = []
        edited_map[path].append((item["pos"], new))

    for path, changes in edited_map.items():
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        offset = 0
        for (start, end), new_chunk in changes:
            content = (
                content[:start+offset] +
                new_chunk +
                content[end+offset:]
            )
            offset += len(new_chunk) - (end - start)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

def get_io_bytes(caminho):
    try:
        if caminho:
            with open(caminho, "rb") as f:
                blob = f.read()
            return io.BytesIO(blob)
    except Exception as e:
        print(e)
        pass


def read_file(caminho: str):
    try:
        if caminho:
            with open(caminho, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        print(e)
        pass
    
def write_file(caminho: str, conteudo: str):
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        return True
    except Exception as e:
        print(e)
        return False
    
def is_audio_file(caminho: str) -> bool:
    audio_extensions = (".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a")
    return caminho.lower().endswith(audio_extensions)

def is_image_file(caminho: str) -> bool:
    image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff")
    return caminho.lower().endswith(image_extensions)

def is_video_file(caminho: str) -> bool:
    video_extensions = (".mp4", ".avi", ".mkv", ".mov", ".flv", ".wmv")
    return caminho.lower().endswith(video_extensions)