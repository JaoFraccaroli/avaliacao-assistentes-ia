"""Pasta documentos_locais: o livro e as anotações do mestre, só no computador de quem usa."""
from pathlib import Path

import motor.documentos_locais as locais
from assistentes.dnd.assistente import AssistenteDnd
from conftest import RAIZ


def test_le_md_e_txt_e_ignora_o_leia_me(tmp_path):
    (tmp_path / "LEIA-ME.md").write_text("## Instruções\nnão é documento", encoding="utf-8")
    (tmp_path / "campanha.md").write_text("## Taverna do Grifo\nA dona se chama Bia.\n## Vilão\nO Barão Cinza.", encoding="utf-8")
    (tmp_path / "notas.txt").write_text("Sessão 1: o grupo chegou.\n\nSessão 2: acharam o mapa.", encoding="utf-8")
    trechos, avisos = locais.carregar(tmp_path)
    assert [t.titulo for t in trechos] == ["Taverna do Grifo", "Vilão", "parte 1", "parte 2"]
    assert avisos == []


def test_pdf_vira_pedacos_com_o_numero_da_pagina(tmp_path, monkeypatch):
    (tmp_path / "livro.pdf").write_bytes(b"%PDF falso")
    paginas = ["palavra " * 400, "outra página curta"]
    monkeypatch.setattr(locais, "_paginas_do_pdf", lambda arquivo: paginas)
    trechos, _ = locais.carregar(tmp_path)
    assert [t.titulo for t in trechos] == ["página 1", "página 1", "página 1", "página 2"]
    assert all(len(t.texto.split()) <= locais.PALAVRAS_POR_PEDACO for t in trechos)


def test_pdf_sem_pypdf_vira_aviso_e_nao_derruba_a_conversa(tmp_path, monkeypatch):
    (tmp_path / "livro.pdf").write_bytes(b"%PDF falso")

    def sem_pypdf(arquivo):
        raise ImportError("pypdf")

    monkeypatch.setattr(locais, "_paginas_do_pdf", sem_pypdf)
    trechos, avisos = locais.carregar(tmp_path)
    assert trechos == [] and "pip install pypdf" in avisos[0]


def test_pasta_que_nao_existe_nao_e_erro(tmp_path):
    assert locais.carregar(tmp_path / "nao_existe") == ([], [])


def test_nome_que_so_existe_no_livro_local_nao_e_barrado(monkeypatch):
    from motor.busca import Trecho
    monkeypatch.setattr("motor.assistente.carregar_locais", lambda pasta: (
        [Trecho("livro.pdf", "página 275", "Desintegrar: um raio fino e verde...")], []))
    assert AssistenteDnd(usar_documentos_locais=True).nome_desconhecido("Qual o dano da magia Desintegrar?") is None
    assert AssistenteDnd().nome_desconhecido("Qual o dano da magia Desintegrar?") == "Desintegrar"


def test_avaliacao_nao_usa_documentos_locais():
    from motor.avaliar import criar_assistente
    assert criar_assistente("dnd").trechos_locais == []


def test_git_ignora_a_pasta_local_menos_o_leia_me():
    regras = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    assert "assistentes/*/documentos_locais/*" in regras
    assert "!assistentes/*/documentos_locais/LEIA-ME.md" in regras
    assert (RAIZ / "assistentes" / "dnd" / "documentos_locais" / "LEIA-ME.md").exists()
