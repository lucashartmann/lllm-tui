import sqlite3
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


def embed(text):
    return np.array(
        ollama.embeddings(model=EMBED_MODEL, prompt=text)["embedding"]
    )


def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def find_relevant(all_chunks, query, top_k=5):
    query_emb = embed(query)
    scored = []

    for i, item in enumerate(all_chunks):
        emb = embed(item["chunk"])
        score = cosine(query_emb, emb)
        scored.append((i, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [all_chunks[i] for i, _ in scored[:top_k]]



def gerar_embedding(text):
    return embed(text)


def salvar_no_banco(info):
    embedding = gerar_embedding(info).astype(np.float32).tobytes()

    with sqlite3.connect("banco.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO informacoes (conteudo, embedding) VALUES (?, ?)",
            (info, embedding),
        )
        conn.commit()


def pesquisar_no_banco(query, top_k=5):
    query_emb = gerar_embedding(query)

    resultados = []

    with sqlite3.connect("banco.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT conteudo, embedding FROM informacoes")

        for conteudo, emb_blob in cursor.fetchall():
            emb = np.frombuffer(emb_blob, dtype=np.float32)
            score = cosine(query_emb, emb)
            resultados.append((conteudo, score))

    resultados.sort(key=lambda x: x[1], reverse=True)

    return [r[0] for r in resultados[:top_k]]
