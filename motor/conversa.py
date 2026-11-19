"""Conversa com memória curta: entende perguntas de continuação, como "e quanto custa?".

Analogia: um atendente de verdade não esquece o que você disse há 10 segundos.
Se você pergunta do Orion Pro 12 e depois "e a garantia dele?", ele sabe de qual
aparelho você está falando. Sem isso, cada mensagem seria um cliente novo.

Como funciona:
- A mensagem atual é usada sozinha na busca quando ela já basta.
- Se ela parece uma continuação (curta, começa com "e", fala "ele", "isso", traz só o
  CPF...) ou a
  busca não acha nada, a mensagem anterior do cliente entra junto na busca.
- As últimas trocas vão para a IA como contexto, só para ela entender a pergunta.
  As proteções (pedido + CPF, assunto, nomes inventados) continuam no código.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from motor.busca import normalizar, palavras

REFERENCIAS = {
    "ele", "ela", "eles", "elas", "dele", "dela", "deles", "delas", "nele", "nela", "isso", "disso",
    "nisso", "esse", "essa", "desse", "dessa", "nesse", "nessa", "aquele", "aquela", "mesmo", "mesma",
    "tambem", "outro", "outra",
}
TROCAS_LEMBRADAS = 2


def parece_continuacao(mensagem: str) -> bool:
    texto = normalizar(mensagem).strip()
    soltas = set(re.findall(r"[a-z]+", texto))
    # mensagem com número de pedido ou CPF solto ("meu cpf é ...") completa a anterior
    tem_numero = bool(re.search(r"\d{5}|\d{3}\.\d{3}", mensagem))
    return (texto.startswith(("e ", "e o", "e a", "e se", "mas ")) or bool(soltas & REFERENCIAS)
            or len(palavras(mensagem)) <= 2 or tem_numero)


@dataclass
class Troca:
    pergunta: str
    resposta: str
    consulta: str


@dataclass
class Conversa:
    assistente: object
    modelo: object
    trocas: list[Troca] = field(default_factory=list)

    def consulta_para(self, mensagem: str) -> str:
        if not self.trocas:
            return mensagem
        if parece_continuacao(mensagem) or not self.assistente.trechos(mensagem):
            return f"{self.trocas[-1].pergunta} {mensagem}"
        return mensagem

    def historico(self) -> str:
        return "\n".join(
            f"Cliente: {t.pergunta}\nAssistente: {t.resposta}" for t in self.trocas[-TROCAS_LEMBRADAS:]
        )

    def enviar(self, mensagem: str) -> Troca:
        consulta = self.consulta_para(mensagem)
        resposta = self.assistente.responder(self.modelo, mensagem, consulta, self.historico())
        troca = Troca(mensagem, resposta, consulta)
        self.trocas.append(troca)
        return troca

    def limpar(self) -> None:
        self.trocas.clear()
