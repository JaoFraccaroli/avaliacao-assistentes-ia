import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


class IAFalsa:
    """Substitui o modelo de verdade: devolve respostas prontas, sem precisar do Ollama."""

    def __init__(self, respostas=None, padrao="Não tenho essa informação.", nome="ia-falsa"):
        self.respostas = respostas or {}
        self.padrao = padrao
        self.nome = nome
        self.chamadas = []

    def responder(self, sistema, mensagem):
        self.chamadas.append((sistema, mensagem))
        pergunta = mensagem.split("PERGUNTA:\n", 1)[-1]
        return self.respostas.get(pergunta, self.padrao)
