import io
import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from calculos import PlanilhaInvalida, coluna_de_data, ler_planilha, ponto_de_equilibrio, precificar, preparar  # noqa: E402


def test_calcula_faturamento_lucro_e_margem():
    t = preparar(pd.DataFrame({"Produto": ["A"], "Quantidade": [10], "Preco_Unitario": [20], "Custo_Unitario": [15]}))
    assert t.loc[0, "Faturamento"] == 200
    assert t.loc[0, "Lucro"] == 50
    assert t.loc[0, "Margem_Perc"] == 25
    assert t.loc[0, "Categoria"] == "Geral"


def test_coluna_faltando_diz_qual():
    with pytest.raises(PlanilhaInvalida, match="Faltando: Custo"):
        preparar(pd.DataFrame({"Produto": ["A"], "Vendas": [1], "Preço": [2]}))


def test_texto_em_coluna_numerica_diz_a_linha():
    with pytest.raises(PlanilhaInvalida, match="linha 3"):
        preparar(pd.DataFrame({"Produto": ["A", "B"], "Vendas": [1, "dez"], "Preço": [2, 2], "Custo": [1, 1]}))


def test_faturamento_zero_nao_divide_por_zero():
    t = preparar(pd.DataFrame({"Produto": ["A"], "Vendas": [0], "Preço": [10], "Custo": [5]}))
    assert t.loc[0, "Margem_Perc"] == 0


def test_csv_com_ponto_e_virgula_e_data_brasileira():
    csv = "Data;Produto;Vendas;Preço;Custo\n25/12/2026;Panetone;3;40;20\n"
    t = ler_planilha(io.StringIO(csv), "vendas.csv")
    col = coluna_de_data(t)
    assert col == "Data"
    assert t.loc[0, "Data"].month == 12


def test_planilha_de_exemplo_abre():
    t = ler_planilha(RAIZ / "exemplo.xlsx", "exemplo.xlsx")
    assert len(t) > 0 and coluna_de_data(t) == "Data"


def test_precificacao():
    p = precificar(custo=50, markup=30, imposto=5)
    assert p["preco"] == pytest.approx(65)
    assert p["lucro"] == pytest.approx(65 - 3.25 - 50)


def test_ponto_de_equilibrio_arredonda_para_cima():
    eq = ponto_de_equilibrio(preco=10, custo_variavel=7, custo_fixo=100)
    assert eq["unidades"] == 34  # 33,3 unidades não pagam a conta
    assert ponto_de_equilibrio(preco=5, custo_variavel=6, custo_fixo=100) is None
