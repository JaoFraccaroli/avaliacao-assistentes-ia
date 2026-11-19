"""Documentos que ficam SÓ no seu computador (nunca vão para o GitHub).

Analogia: é a estante particular do mestre. O repositório público tem o resumo das
regras abertas (SRD 5.2); na pasta `documentos_locais` você coloca o seu livro em PDF
e as anotações da sua campanha. O modo de conversa lê as duas estantes; a avaliação
automática e o GitHub Actions usam só a pública, para os resultados serem iguais em
qualquer máquina.

Formatos:
- `.md`: dividido pelos títulos `## `, como os documentos do projeto;
- `.txt`: dividido por parágrafos (linha em branco);
- `.pdf`: dividido em pedaços de ~180 palavras por página (precisa de `pip install pypdf`).
  O texto extraído fica guardado num cache ao lado do PDF, para não ler o livro de novo
  toda vez que a conversa abre.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from motor.busca import Trecho, dividir_em_trechos

PALAVRAS_POR_PEDACO = 180
IGNORADOS = {"leia-me.md"}


def _pedacos(texto: str, tamanho: int = PALAVRAS_POR_PEDACO) -> list[str]:
    palavras = texto.split()
    return [" ".join(palavras[i:i + tamanho]) for i in range(0, len(palavras), tamanho)]


def _paginas_do_pdf(arquivo: Path) -> list[str]:
    cache = arquivo.with_name(f".{arquivo.name}.cache.json")
    marca = f"{arquivo.stat().st_size}-{int(arquivo.stat().st_mtime)}"
    if cache.exists():
        try:
            dados = json.loads(cache.read_text(encoding="utf-8"))
            if dados.get("marca") == marca:
                return dados["paginas"]
        except (ValueError, KeyError):
            pass
    from pypdf import PdfReader  # só é preciso quando há PDF na pasta

    paginas = [(pagina.extract_text() or "") for pagina in PdfReader(str(arquivo)).pages]
    try:
        cache.write_text(json.dumps({"marca": marca, "paginas": paginas}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass  # sem cache, só fica mais lento
    return paginas


def trechos_do_pdf(arquivo: Path) -> list[Trecho]:
    trechos = []
    for numero, texto in enumerate(_paginas_do_pdf(arquivo), start=1):
        texto = re.sub(r"\s+", " ", texto).strip()
        for pedaco in _pedacos(texto):
            trechos.append(Trecho(arquivo.name, f"página {numero}", pedaco))
    return trechos


def trechos_do_txt(arquivo: Path) -> list[Trecho]:
    blocos = [b.strip() for b in re.split(r"\n\s*\n", arquivo.read_text(encoding="utf-8")) if b.strip()]
    return [Trecho(arquivo.name, f"parte {i}", b) for i, b in enumerate(blocos, start=1)]


def carregar(pasta: Path) -> tuple[list[Trecho], list[str]]:
    """Devolve os trechos da pasta e avisos (ex.: PDF sem o pypdf instalado)."""
    trechos: list[Trecho] = []
    avisos: list[str] = []
    if not pasta.is_dir():
        return trechos, avisos
    for arquivo in sorted(pasta.iterdir()):
        nome = arquivo.name.lower()
        if nome in IGNORADOS or nome.startswith("."):
            continue
        if nome.endswith(".md"):
            trechos += dividir_em_trechos(arquivo.name, arquivo.read_text(encoding="utf-8"))
        elif nome.endswith(".txt"):
            trechos += trechos_do_txt(arquivo)
        elif nome.endswith(".pdf"):
            try:
                trechos += trechos_do_pdf(arquivo)
            except ImportError:
                avisos.append(f"{arquivo.name} ignorado: para ler PDF, rode `pip install pypdf`.")
            except Exception as erro:  # PDF protegido ou corrompido não pode derrubar a conversa
                avisos.append(f"{arquivo.name} ignorado: não consegui ler o PDF ({erro.__class__.__name__}).")
    return trechos, avisos
