"""Leitura da planilha e cálculos do dashboard (sem Streamlit, para poder testar)."""

import pandas as pd

# Nomes aceitos na planilha -> nome usado no dashboard
SINONIMOS = {
    "Quantidade": "Vendas", "Qtd": "Vendas",
    "Preco_Unitario": "Preço", "Preço_Unitário": "Preço", "Preco": "Preço",
    "Custo_Unitario": "Custo", "Custo_Unitário": "Custo",
}
OBRIGATORIAS = ["Produto", "Vendas", "Preço", "Custo"]
NUMERICAS = ["Vendas", "Preço", "Custo"]


class PlanilhaInvalida(ValueError):
    """Erro com mensagem pronta para mostrar ao usuário."""


def ler_planilha(arquivo, nome: str) -> pd.DataFrame:
    """Lê CSV (vírgula ou ponto e vírgula) ou Excel."""
    if nome.lower().endswith(".csv"):
        tabela = pd.read_csv(arquivo, sep=None, engine="python")
    else:
        tabela = pd.read_excel(arquivo)
    return preparar(tabela)


def preparar(tabela: pd.DataFrame) -> pd.DataFrame:
    """Padroniza colunas, valida e calcula faturamento, lucro e margem."""
    tabela = tabela.copy()
    tabela.columns = tabela.columns.astype(str).str.strip()
    tabela = tabela.rename(columns=SINONIMOS)

    faltando = [c for c in OBRIGATORIAS if c not in tabela.columns]
    if faltando:
        raise PlanilhaInvalida(
            "A planilha precisa das colunas: " + ", ".join(OBRIGATORIAS)
            + ". Faltando: " + ", ".join(faltando)
            + ". Colunas encontradas: " + ", ".join(tabela.columns) + "."
        )
    for c in NUMERICAS:
        valores = pd.to_numeric(tabela[c], errors="coerce")
        ruins = tabela.loc[valores.isna() & tabela[c].notna(), c]
        if len(ruins):
            raise PlanilhaInvalida(
                f"A coluna '{c}' tem valores que não são números (ex.: '{ruins.iloc[0]}' na linha {ruins.index[0] + 2})."
            )
        tabela[c] = valores.fillna(0)

    if "Categoria" not in tabela.columns:
        tabela["Categoria"] = "Geral"

    tabela["Faturamento"] = tabela["Vendas"] * tabela["Preço"]
    tabela["Lucro"] = tabela["Faturamento"] - tabela["Custo"] * tabela["Vendas"]
    tabela["Margem_Perc"] = (tabela["Lucro"] / tabela["Faturamento"].where(tabela["Faturamento"] > 0) * 100).fillna(0)
    return tabela


def coluna_de_data(tabela: pd.DataFrame):
    """Primeira coluna que parece data, já convertida; None se não houver."""
    for col in tabela.columns:
        if "data" in col.lower() or "date" in col.lower():
            tabela[col] = pd.to_datetime(tabela[col], dayfirst=True, errors="coerce")
            if tabela[col].notna().any():
                return col
    return None


def precificar(custo: float, markup: float, imposto: float) -> dict:
    """Preço de venda a partir do custo e do markup (%), descontando impostos (%)."""
    preco = custo * (1 + markup / 100)
    val_imposto = preco * imposto / 100
    lucro = preco - val_imposto - custo
    return {
        "preco": preco, "imposto": val_imposto, "lucro": lucro,
        "margem": lucro / preco * 100 if preco > 0 else 0,
    }


def ponto_de_equilibrio(preco: float, custo_variavel: float, custo_fixo: float):
    """Unidades para pagar os custos (arredondado para cima) ou None se cada venda dá prejuízo."""
    mc = preco - custo_variavel
    if mc <= 0:
        return None
    import math
    qtd = custo_fixo / mc
    return {"margem_contribuicao": mc, "quantidade": qtd, "unidades": math.ceil(qtd), "receita": qtd * preco}
