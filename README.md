# 📈 Dashboard Executivo de Vendas

Dashboard em **Streamlit** para analisar vendas a partir de uma planilha (Excel ou CSV) e simular preço e ponto de equilíbrio.
Feito por Maurílio Pereira Santana Oliveira Nunes.

## O que ele mostra

**Visão Geral (BI)**
- Faturamento, lucro líquido, unidades vendidas e margem média comparada com a meta.
- Matriz preço × margem por produto e radar com os produtos abaixo da meta de margem.
- Ranking de lucro, quantidade ou faturamento (top 20) e participação por categoria.
- Filtro de período automático quando a planilha tem uma coluna de data.

**Simulador de Precificação**
- Preço sugerido a partir do custo, markup e impostos, com a margem real.
- Ponto de equilíbrio: quantas unidades vender para pagar os custos fixos.

## Formato da planilha

| Coluna | Obrigatória | Também aceita | Exemplo |
|---|:---:|---|---|
| `Produto` | ✅ | | Coxinha |
| `Vendas` | ✅ | `Quantidade`, `Qtd` | 12 |
| `Preço` | ✅ | `Preco`, `Preco_Unitario` | 7,00 |
| `Custo` | ✅ | `Custo_Unitario` | 2,40 |
| `Categoria` | | | Salgados (se faltar, vira "Geral") |
| `Data` | | qualquer coluna com "data" ou "date" no nome | 25/12/2026 |

CSV pode usar vírgula ou ponto e vírgula. Se faltar coluna ou tiver texto num campo de número, o dashboard diz qual coluna e qual linha.

Para testar, use a planilha [`exemplo.xlsx`](exemplo.xlsx) (dados fictícios de uma padaria, 60 dias).

## Rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

## Arquivos

| Arquivo | O que é |
|---|---|
| `app.py` | Telas do dashboard |
| `calculos.py` | Leitura da planilha, validação e contas (testável sem Streamlit) |
| `exemplo.xlsx` | Planilha de exemplo |
| `tests/` | Testes dos cálculos |
