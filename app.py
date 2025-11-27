import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL DA PÁGINA
# ==============================================================================
st.set_page_config(page_title="Analytics Pro MP", layout="wide", page_icon="📈")

# CSS Customizado
st.markdown("""
<style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    [data-testid="stMetricValue"] {font-size: 24px;}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. BARRA LATERAL (FILTROS E UPLOAD)
# ==============================================================================
with st.sidebar:
    # --- LOGO CSS ---
    st.markdown("""
        <style>
        .logo-box {
            display: flex; justify-content: center; align-items: center;
            background: linear-gradient(135deg, #1e293b, #0f172a);
            border-radius: 12px; width: 100%; height: 80px;
            margin-bottom: 20px; border: 1px solid #334155;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .logo-text { color: white; font-weight: 800; font-size: 32px; margin: 0; font-family: 'Arial'; letter-spacing: 2px;}
        </style>
        <div class="logo-box"><p class="logo-text">MP</p></div>
    """, unsafe_allow_html=True)
    
    st.header("🎛️ Painel de Controle")
    arquivo_upload = st.file_uploader("Importar Dados (Excel/CSV)", type=["xlsx", "csv"])
    
    st.markdown("---")
    st.write("🎯 **Metas de Margem**")
    meta_geral = st.slider("Meta Global (%)", 0, 100, 20) / 100

# ==============================================================================
# 3. CORPO PRINCIPAL
# ==============================================================================
st.title("📈 Dashboard Executivo de Vendas")
st.markdown("Visão estratégica e simulação de cenários financeiros.")

aba1, aba2 = st.tabs(["📊 Visão Geral (BI)", "🧠 Simulador de Precificação"])

# VARIÁVEIS GLOBAIS
tabela_filtrada = None
nome_coluna_data = None 

if arquivo_upload is not None:
    # --- LEITURA E TRATAMENTO DOS DADOS ---
    try:
        if arquivo_upload.name.endswith('.csv'):
            try:
                tabela = pd.read_csv(arquivo_upload)
            except:
                arquivo_upload.seek(0)
                tabela = pd.read_csv(arquivo_upload, sep=';')
        else:
            tabela = pd.read_excel(arquivo_upload)
            
        # PADRONIZAÇÃO DE COLUNAS
        tabela.columns = tabela.columns.str.strip()
        mapa = {"Quantidade": "Vendas", "Preco_Unitario": "Preço", "Custo_Unitario": "Custo", "Preco": "Preço"}
        tabela = tabela.rename(columns=mapa)
        
        # CATEGORIA DEFAULT
        if "Categoria" not in tabela.columns:
            tabela["Categoria"] = "Geral"
            
        # CÁLCULOS FINANCEIROS
        tabela["Faturamento"] = tabela["Vendas"] * tabela["Preço"]
        tabela["Lucro"] = tabela["Faturamento"] - (tabela["Custo"] * tabela["Vendas"])
        tabela["Margem_Perc"] = (tabela["Lucro"] / tabela["Faturamento"]) * 100
        
        # --- FILTRO DE DATA AUTOMÁTICO ---
        col_data_encontrada = [col for col in tabela.columns if 'Data' in col or 'date' in col.lower()]
        
        if col_data_encontrada:
            nome_coluna_data = col_data_encontrada[0]
            tabela[nome_coluna_data] = pd.to_datetime(tabela[nome_coluna_data])
            
            data_min = tabela[nome_coluna_data].min()
            data_max = tabela[nome_coluna_data].max()
            
            with st.sidebar:
                st.markdown("---")
                st.header("📅 Filtro de Período")
                data_inicio, data_fim = st.date_input(
                    "Selecione o intervalo",
                    [data_min, data_max],
                    min_value=data_min,
                    max_value=data_max
                )
            
            tabela_filtrada = tabela[
                (tabela[nome_coluna_data].dt.date >= data_inicio) & 
                (tabela[nome_coluna_data].dt.date <= data_fim)
            ]
            tabela_filtrada = tabela_filtrada.sort_values(by=nome_coluna_data, ascending=False)
        else:
            tabela_filtrada = tabela

    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
        st.stop()

# ==============================================================================
# ABA 1: DASHBOARD COM PLOTLY
# ==============================================================================
with aba1:
    if tabela_filtrada is not None:
        # --- LINHA 1: BIG NUMBERS (KPIs) ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        fat_total = tabela_filtrada["Faturamento"].sum()
        lucro_total = tabela_filtrada["Lucro"].sum()
        vendas_total = tabela_filtrada["Vendas"].sum()
        margem_media = tabela_filtrada["Margem_Perc"].mean()
        
        kpi1.metric("💰 Faturamento", f"R$ {fat_total:,.2f}")
        kpi2.metric("💸 Lucro Líquido", f"R$ {lucro_total:,.2f}", delta_color="normal")
        kpi3.metric("📦 Vendas Totais", f"{int(vendas_total)} unidades")
        kpi4.metric("📈 Margem Média", f"{margem_media:.1f}%", 
                   delta=f"{margem_media - (meta_geral*100):.1f}% vs Meta")
        
        # --- NOVIDADE: DETALHAMENTO DE VENDAS (EXPANDER) ---
        with st.expander(f"🔎 Clique para ver o detalhe das {int(vendas_total)} unidades vendidas"):
            st.write("Resumo de quantidade vendida por produto:")
            
            # Cria uma tabela resumida só com Produto e Quantidade
            resumo_qtd = tabela_filtrada.groupby("Produto")[["Vendas"]].sum(numeric_only=True).sort_values("Vendas", ascending=False).reset_index()
            
            # Mostra como tabela visual
            st.dataframe(
                resumo_qtd,
                column_config={
                    "Vendas": st.column_config.ProgressColumn(
                        "Quantidade", 
                        format="%d un", 
                        min_value=0, 
                        max_value=int(resumo_qtd["Vendas"].max())
                    )
                },
                use_container_width=True,
                hide_index=True
            )
        
        st.divider()
        
        # --- LINHA 2: GRÁFICOS AVANÇADOS ---
        g_col1, g_col2 = st.columns([2, 1])
        
        with g_col1:
            # Seletor para mudar o gráfico
            tipo_analise = st.radio(
                "O que você quer analisar no gráfico?",
                ["Lucro (R$)", "Quantidade Vendida (Un)", "Faturamento (R$)"],
                horizontal=True
            )
            
            # Define qual coluna usar baseada na escolha
            coluna_y = "Lucro"
            cor_grafico = "Lucro"
            titulo_grafico = "Ranking de Lucratividade"
            formato_texto = "R$ .2s"

            if tipo_analise == "Quantidade Vendida (Un)":
                coluna_y = "Vendas"
                cor_grafico = "Vendas"
                titulo_grafico = "Produtos Mais Vendidos (Volume)"
                formato_texto = ".0f"
            elif tipo_analise == "Faturamento (R$)":
                coluna_y = "Faturamento"
                cor_grafico = "Faturamento"
                titulo_grafico = "Produtos com Maior Receita"

            # Agrupa dados (numeric_only=True para ignorar datas)
            dados_grafico = tabela_filtrada.groupby("Produto").sum(numeric_only=True).reset_index()
            
            fig_bar = px.bar(
                dados_grafico,
                x="Produto", y=coluna_y, color=cor_grafico,
                color_continuous_scale=["#ef4444", "#fbbf24", "#22c55e"],
                title=titulo_grafico,
                text_auto=formato_texto
            )
            fig_bar.update_layout(xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with g_col2:
            st.subheader("Share por Categoria")
            fig_pie = px.pie(
                tabela_filtrada, values="Faturamento", names="Categoria", 
                hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
            
        # --- LINHA 3: TABELA COMPLETA ---
        st.subheader("📋 Detalhamento de Transações")
        
        config_colunas = {
            "Preço": st.column_config.NumberColumn(format="R$ %.2f"),
            "Custo": st.column_config.NumberColumn(format="R$ %.2f"),
            "Faturamento": st.column_config.NumberColumn(format="R$ %.2f"),
            "Lucro": st.column_config.NumberColumn(format="R$ %.2f"),
            "Vendas": st.column_config.NumberColumn("Qtd", format="%d"),
            "Margem_Perc": st.column_config.ProgressColumn("Margem (%)", format="%.1f%%", min_value=-10, max_value=100)
        }
        
        if nome_coluna_data:
            config_colunas[nome_coluna_data] = st.column_config.DateColumn("Data da Venda", format="DD/MM/YYYY")

        st.dataframe(
            tabela_filtrada, 
            column_config=config_colunas,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("👋 Olá! Carregue sua planilha (Excel ou CSV) na barra lateral para ativar o Dashboard.")

# ==============================================================================
# ABA 2: SIMULADOR
# ==============================================================================
with aba2:
    st.write("### 🛠️ Calculadora de Viabilidade")
    st.caption("Ajuste os parâmetros abaixo para simular a saúde financeira de um novo produto.")
    
    sim_col1, sim_col2 = st.columns(2)
    
    with sim_col1:
        with st.container(border=True):
            st.subheader("1. Precificação & Margem")
            custo = st.number_input("Custo Unitário (R$)", 0.0, 10000.0, 50.0)
            markup = st.number_input("Markup (%)", 0.0, 500.0, 30.0)
            imposto = st.number_input("Impostos (%)", 0.0, 100.0, 5.0)
            
            preco_venda = custo * (1 + markup/100)
            val_imposto = preco_venda * (imposto/100)
            lucro_liq = preco_venda - val_imposto - custo
            margem_real = (lucro_liq / preco_venda) * 100 if preco_venda > 0 else 0
            
            st.markdown("---")
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = margem_real,
                title = {'text': "Margem Real"},
                gauge = {
                    'axis': {'range': [-10, 60]},
                    'bar': {'color': "#3b82f6"},
                    'steps': [
                        {'range': [-10, 0], 'color': "#ef4444"},
                        {'range': [0, 15], 'color': "#f59e0b"},
                        {'range': [15, 60], 'color': "#10b981"}
                    ]
                }
            ))
            fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            st.info(f"Preço Sugerido: **R$ {preco_venda:.2f}** | Lucro Líquido: **R$ {lucro_liq:.2f}**")

    with sim_col2:
        with st.container(border=True):
            st.subheader("2. Ponto de Equilíbrio (Break-even)")
            custo_fixo = st.number_input("Custo Fixo Mensal (R$)", 0.0, 100000.0, 5000.0)
            
            mc = preco_venda - (custo + val_imposto)
            
            if mc > 0:
                qtd_eq = custo_fixo / mc
                
                x = list(range(0, int(qtd_eq * 1.8), 5))
                y_rec = [xi * preco_venda for xi in x]
                y_cus = [custo_fixo + (custo + val_imposto) * xi for xi in x]
                
                fig_be = go.Figure()
                fig_be.add_trace(go.Scatter(x=x, y=y_rec, name="Receita", line=dict(color="#10b981", width=3)))
                fig_be.add_trace(go.Scatter(x=x, y=y_cus, name="Custos", line=dict(color="#ef4444", width=3)))
                fig_be.add_vline(x=qtd_eq, line_dash="dot", annotation_text="Break-even")
                
                fig_be.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), showlegend=True)
                st.plotly_chart(fig_be, use_container_width=True)
                
                st.success(f"Venda **{int(qtd_eq)} unidades** para pagar as contas.")
            else:
                st.error("Preço insuficiente para cobrir custos variáveis!")

# ==============================================================================
# RODAPÉ
# ==============================================================================
with st.sidebar:
    st.markdown("---")
    st.markdown("**Desenvolvido por:**")
    st.markdown("Maurílio Pereira Santana Oliveira Nunes")
    st.caption("📧 mauriliopnunes77@gmail.com")

