"""Converse com um assistente pelo terminal, usando um modelo do Ollama.

    python -m motor.conversar --assistente loja --modelo qwen2.5:3b
    python -m motor.conversar --assistente dnd  --modelo qwen2.5:3b

Comandos durante a conversa:  /limpar (começa do zero)  /trechos (liga/desliga
os trechos usados)  /sair
"""
from __future__ import annotations

import argparse
import sys
import time

from motor.avaliar import criar_assistente
from motor.cliente_llm import ClienteOllama, ollama_disponivel
from motor.conversa import Conversa

BOAS_VINDAS = {
    "loja": "Sinal Verde Celulares (loja fictícia). Pergunte sobre produtos, frete, troca, garantia ou o seu pedido.",
    "dnd": "Assistente do mestre de D&D 5ª edição (regras de 2024). Pergunte sobre regras, combate, "
           "personagens, magias, monstros, preparação de sessão ou o cenário Vale de Brumacinza.",
}


def main(argumentos: list[str] | None = None, entrada=input) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # acentos certos no terminal do Windows
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--assistente", choices=["loja", "dnd"], required=True)
    p.add_argument("--modelo", default="qwen2.5:3b", help="nome do modelo no Ollama")
    p.add_argument("--sem-locais", action="store_true",
                   help="ignora a pasta documentos_locais (usa só os documentos do repositório)")
    a = p.parse_args(argumentos)

    if not ollama_disponivel():
        print("Ollama não está rodando. Abra o aplicativo do Ollama (ou rode: ollama serve).", file=sys.stderr)
        return 2

    assistente = criar_assistente(a.assistente, usar_documentos_locais=not a.sem_locais)
    for aviso in getattr(assistente, "avisos", []):
        print(f"Aviso: {aviso}")
    if getattr(assistente, "trechos_locais", None):
        fontes = sorted({t.fonte for t in assistente.trechos_locais})
        print(f"Documentos locais carregados: {', '.join(fontes)} ({len(assistente.trechos_locais)} trechos)")
    conversa = Conversa(assistente, ClienteOllama(a.modelo))
    mostrar_trechos = True
    print(f"\n{BOAS_VINDAS[a.assistente]}\nModelo: {a.modelo}  |  /limpar  /trechos  /sair\n")

    while True:
        try:
            mensagem = entrada("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not mensagem:
            continue
        comando = mensagem.lower()
        if comando in ("/sair", "sair"):
            return 0
        if comando == "/limpar":
            conversa.limpar()
            print("(conversa apagada: o assistente não lembra mais de nada)\n")
            continue
        if comando == "/trechos":
            mostrar_trechos = not mostrar_trechos
            print(f"(trechos {'ligados' if mostrar_trechos else 'desligados'})\n")
            continue

        inicio = time.perf_counter()
        troca = conversa.enviar(mensagem)
        print(f"Assistente: {troca.resposta}")
        if mostrar_trechos:
            usados = [f"{t.fonte} > {t.titulo or '(início)'}" for t in assistente.trechos(troca.consulta)]
            print(f"   [trechos: {'; '.join(usados) or 'nenhum'}]")
            if troca.consulta != mensagem:
                print("   [entendido como continuação da mensagem anterior]")
        print(f"   [{time.perf_counter() - inicio:.1f}s]\n")


if __name__ == "__main__":
    sys.exit(main())
