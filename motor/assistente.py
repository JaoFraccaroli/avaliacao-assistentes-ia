"""Assistente que responde com base em documentos (RAG simples)."""
from __future__ import annotations

from pathlib import Path

from motor.busca import Buscador, Trecho
from motor.cliente_llm import ModeloDeLinguagem


class AssistenteComDocumentos:
    # Resposta fixa quando a pergunta não tem NADA a ver com os documentos
    # (a busca não encontra nenhum trecho): nem chega a perguntar à IA.
    FORA_DO_ASSUNTO = "Desculpe, só posso ajudar com assuntos relacionados aos documentos que conheço."

    def __init__(self, nome: str, pasta_documentos: Path, instrucoes: str, quantidade_trechos: int = 3):
        self.nome = nome
        self.instrucoes = instrucoes.strip()
        self.quantidade_trechos = quantidade_trechos
        self.buscador = Buscador.da_pasta(pasta_documentos)

    def resposta_direta(self, pergunta: str) -> str | None:
        """Respostas decididas pelo CÓDIGO, sem consultar a IA. None = deixa a IA responder."""
        if not self.trechos(pergunta):
            return self.FORA_DO_ASSUNTO
        return None

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
        # Versão 2 tinha um lembrete aqui com uma frase pronta ("Não encontrei essa informação.").
        # Os modelos pequenos passaram a copiar a frase até quando a resposta estava nos documentos
        # (qwen2.5:1.5b: fatos da loja caíram de 86% para 36%). Removido na versão 3.
        mensagem += f"PERGUNTA:\n{pergunta}"
        return self.instrucoes, mensagem

    def responder(self, modelo: ModeloDeLinguagem, pergunta: str) -> str:
        direta = self.resposta_direta(pergunta)
        if direta is not None:
            return direta
        sistema, mensagem = self.montar(pergunta)
        return modelo.responder(sistema, mensagem)
