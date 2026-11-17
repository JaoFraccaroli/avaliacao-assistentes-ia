import json

import pytest

from conftest import IAFalsa, RAIZ
from assistentes.loja.assistente import AssistenteLoja
from motor.avaliacao import avaliar
from motor.casos import Caso
from motor.relatorio import em_markdown

CASOS = [
    Caso("A", "fatos", "Prazo de troca?", "7 dias", ""),
    Caso("B", "fatos", "Frete?", "29,90", "grátis"),
    Caso("C", "nao_inventa", "Vende geladeira?", "[RECUSA]", ""),
]
MINIMOS = {"fatos": 0.5, "nao_inventa": 1.0}


def test_ia_que_acerta_tudo_e_aprovada():
    ia = IAFalsa({"Prazo de troca?": "Em até 7 dias.", "Frete?": "R$ 29,90.", "Vende geladeira?": "Não vendemos."})
    r = avaliar(AssistenteLoja(), ia, CASOS, MINIMOS)
    assert r.aprovado and r.taxa_geral == 1.0
    assert len(ia.chamadas) == 3


def test_ia_que_inventa_e_reprovada_na_categoria_certa():
    ia = IAFalsa({"Prazo de troca?": "7 dias.", "Frete?": "Frete grátis!", "Vende geladeira?": "Sim, custa R$ 3.000."})
    r = avaliar(AssistenteLoja(), ia, CASOS, MINIMOS)
    por_categoria = {c.categoria: c for c in r.categorias}
    assert por_categoria["fatos"].acertos == 1 and por_categoria["fatos"].aprovada  # 50% >= 50%
    assert not por_categoria["nao_inventa"].aprovada
    assert not r.aprovado


def test_minimo_faltando_da_erro():
    with pytest.raises(ValueError, match="falta o mínimo"):
        avaliar(AssistenteLoja(), IAFalsa(), CASOS, {"fatos": 0.5})


def test_ia_recebe_instrucoes_e_documentos():
    ia = IAFalsa()
    avaliar(AssistenteLoja(), ia, CASOS[:1], {"fatos": 0})
    sistema, mensagem = ia.chamadas[0]
    assert "Sinal Verde" in sistema and "Nunca invente" in sistema
    assert mensagem.startswith("DOCUMENTOS:") and "7 dias corridos" in mensagem


def test_relatorio_markdown_e_json():
    ia = IAFalsa({"Prazo de troca?": "30 dias."})
    r = avaliar(AssistenteLoja(), ia, CASOS, MINIMOS)
    md = em_markdown(r)
    assert "❌ REPROVADO" in md and "| Acerta fatos dos documentos |" in md
    assert "**A** (fatos) — Prazo de troca?" in md and 'faltou: "7 dias"' in md
    dados = json.loads(json.dumps(r.como_dicionario()))
    assert dados["aprovado"] is False and len(dados["casos"]) == 3


def test_linha_de_comando_sem_ollama_avisa(monkeypatch, capsys):
    from motor import avaliar as cli
    monkeypatch.setattr(cli, "ollama_disponivel", lambda: False)
    assert cli.main(["--assistente", "loja", "--modelo", "x"]) == 2
    assert "Ollama não está rodando" in capsys.readouterr().err


def test_linha_de_comando_completa_com_ia_falsa(monkeypatch, tmp_path):
    from motor import avaliar as cli
    monkeypatch.setattr(cli, "ollama_disponivel", lambda: True)
    monkeypatch.setattr(cli, "ClienteOllama", lambda nome: IAFalsa(nome=nome))
    codigo = cli.main(["--assistente", "dnd", "--modelo", "falso:1b", "--saida", str(tmp_path)])
    assert codigo == 1  # a IA falsa sempre diz "não tenho": reprova nos fatos
    assert (tmp_path / "dnd__falso_1b.md").exists() and (tmp_path / "dnd__falso_1b.json").exists()
