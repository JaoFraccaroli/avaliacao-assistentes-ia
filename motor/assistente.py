"""Assistente que responde com base em documentos (RAG simples)."""
from __future__ import annotations

from pathlib import Path

from motor.busca import Buscador, Trecho
from motor.cliente_llm import ModeloDeLinguagem


class AssistenteComDocumentos:
    def __init__(self, nome: str, pasta_documentos: Path, instrucoes: str, quantidade_trechos: int = 3):
        self.nome = nome
        self.instrucoes = instrucoes.strip()
        self.quantidade_trechos = quantidade_trechos
        self.buscador = Buscador.da_pasta(pasta_documentos)

    def contexto_extra(self, pergunta: str) -> str:
        """Informações que o próprio código acrescenta (ex.: dados de um pedido verificado)."""
        return ""

    def trechos(self, pergunta: str) -> list[Trecho]:
        return self.buscador.buscar(pergunta, self.quantidade_trechos)

    def montar(self, pergunta: str) -> tuple[str, str]:
        partes = [f"[{t.fonte} - {t.titulo}]\n{t.texto}" for t in self.trechos(pergunta)]
        documentos = "\n\n".join(partes) if partes else "(nenhum trecho encontrado sobre isso)"
        extra = self.contexto_extra(pergunta)
        mensagem = f"DOCUMENTOS:\n{documentos}\n\n"
        if extra:
            mensagem += f"{extra}\n\n"
        mensagem += f"PERGUNTA:\n{pergunta}"
        return self.instrucoes, mensagem

    def responder(self, modelo: ModeloDeLinguagem, pergunta: str) -> str:
        sistema, mensagem = self.montar(pergunta)
        return modelo.responder(sistema, mensagem)
