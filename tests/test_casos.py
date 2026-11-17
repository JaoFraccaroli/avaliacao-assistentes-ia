import tomllib

import pytest

from conftest import RAIZ
from motor.casos import CATEGORIAS, carregar_casos


@pytest.mark.parametrize("assistente", ["loja", "dnd"])
def test_planilhas_de_casos_sao_validas_e_tem_minimos(assistente):
    casos = carregar_casos(RAIZ / "casos" / f"{assistente}.csv")
    assert len(casos) >= 20
    with open(RAIZ / "limites.toml", "rb") as f:
        limites = tomllib.load(f)[assistente]
    for categoria in {c.categoria for c in casos}:
        assert 0 < limites[categoria] <= 1


def test_privacidade_da_loja_exige_100_por_cento():
    with open(RAIZ / "limites.toml", "rb") as f:
        assert tomllib.load(f)["loja"]["privacidade"] == 1.0


def _csv(tmp_path, linhas):
    arquivo = tmp_path / "casos.csv"
    arquivo.write_text("id;categoria;pergunta;deve_conter;nao_pode_conter;observacao\n" + "\n".join(linhas), encoding="utf-8")
    return arquivo


def test_categoria_desconhecida_da_erro(tmp_path):
    with pytest.raises(ValueError, match="categoria desconhecida"):
        carregar_casos(_csv(tmp_path, ["X1;inventada;pergunta?;algo;;"]))


def test_id_repetido_da_erro(tmp_path):
    with pytest.raises(ValueError, match="id repetido"):
        carregar_casos(_csv(tmp_path, ["X1;fatos;p1?;a;;", "X1;fatos;p2?;b;;"]))


def test_caso_sem_criterio_da_erro(tmp_path):
    with pytest.raises(ValueError, match="sem critério"):
        carregar_casos(_csv(tmp_path, ["X1;fatos;pergunta?;;;"]))


def test_todas_as_categorias_tem_descricao():
    assert set(CATEGORIAS) == {"fatos", "nao_inventa", "recusa", "manipulacao", "privacidade", "escopo"}
