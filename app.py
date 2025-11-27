import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página (Wide mode para usar a tela toda)
st.set_page_config(page_title="Consultor Pro", layout="wide", page_icon="🚀")

# CSS para deixar o visual mais limpo (remove margens excessivas)
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
</style>
""", unsafe_allow_html=True)

# Título
st.title("🚀 Consultor de Negócios 2.0")
st.markdown("---")

# Abas
aba1, aba2 = st.tabs(["📊 Dashboard Interativo", "🧠 Simulador de Lucro"])

# ==============================================================================
# ABA 1: DASHBOARD VISUAL
# ==============================================================================
with aba1:
    # --- BARRA LATERAL (FILTROS) ---
    with st.sidebar:
        st.header("🎛️ Filtros & Upload")
        arquivo_upload = st.file_uploader("📂 Carregar Planilha", type=["xlsx"])
        st.write("---")
        st.write("Configuração de Metas:")
        meta_geral = st.slider("Meta de Margem Geral (%)", 0, 100, 20) / 100

    if arquivo_upload is not None:
        tabela = pd.read_excel(arquivo_upload)
        
        # Tratamento básico
        if "Categoria" not in tabela.columns:
            tabela["Categoria"] = "Geral"
        
        tabela["Faturamento"] = tabela["Vendas"] * tabela["Preço"]
        tabela["Lucro"] = tabela["Faturamento"] - (tabela["Custo"] * tabela["Vendas"])
        tabela["Margem"] = (tabela["Lucro"] / tabela["Faturamento"]) * 100
        
        # --- LINHA 1: CARTÕES DE MÉTRICAS (KPIs) ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Faturamento Total", f"R$ {tabela['Faturamento'].sum():,.2f}")
        col2.metric("Lucro Total", f"R$ {tabela['Lucro'].sum():,.2f}")
        
        # Margem Média com cor dinâmica
        margem_media = tabela["Margem"].mean()
        col3.metric("Margem Média", f"{margem_media:.1f}%", delta=f"{margem_media - (meta_geral*100):.1f}%")
        col4.metric("Total Vendas", int(tabela['Vendas'].sum()))
        
        st.markdown("---")

        # --- LINHA 2: GRÁFICOS INTERATIVOS ---
        col_g1, col_g2 = st.columns([2, 1]) # Coluna esquerda mais larga

        with col_g1:
            st.subheader("💰 Lucro por Produto")
            # Gráfico de Barras Interativo
            fig_bar = px.bar(tabela, x="Produto", y="Lucro", color="Lucro",
                             color_continuous_scale=["red", "yellow", "green"],
                             text_auto='.2s', title="Quem está dando dinheiro?")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_g2:
            st.subheader("🍕 Faturamento por Categoria")
            # Gráfico de Rosca (Donut Chart)
            fig_pie = px.pie(tabela, values="Faturamento", names="Categoria", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- LINHA 3: TABELA INTELIGENTE ---
        st.subheader("📋 Detalhes dos Produtos")
        # Dataframe com formatação visual
        st.dataframe(
            tabela[["Produto", "Categoria", "Vendas", "Faturamento", "Lucro", "Margem"]],
            column_config={
                "Faturamento": st.column_config.NumberColumn(format="R$ %.2f"),
                "Lucro": st.column_config.NumberColumn(format="R$ %.2f"),
                "Margem": st.column_config.ProgressColumn(
                    "Margem Real", format="%.1f%%", min_value=-10, max_value=100
                ),
            },
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("👈 Faça o upload da planilha na barra lateral para começar.")

# ==============================================================================
# ABA 2: SIMULADOR VISUAL (VELOCÍMETRO E GRÁFICO DE PONTO DE EQUILÍBRIO)
# ==============================================================================
with aba2:
    col_sim1, col_sim2 = st.columns(2)

    # --- SIMULADOR 1: VELOCÍMETRO DE MARGEM ---
    with col_sim1:
        st.header("🔍 Calculadora de Realidade")
        custo = st.number_input("Custo do Produto (R$)", value=50.0)
        markup = st.number_input("Markup Aplicado (%)", value=30.0)
        imposto = st.number_input("Imposto (%)", value=10.0)
        
        preco = custo * (1 + markup/100)
        lucro_liq = preco - (preco * imposto/100) - custo
        margem_real = (lucro_liq / preco) * 100
        
        st.write(f"Preço de Venda: **R$ {preco:.2f}**")
        
        # Gráfico de Velocímetro (Gauge Chart)
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = margem_real,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Sua Margem Real"},
            delta = {'reference': markup, 'increasing': {'color': "green"}},
            gauge = {
                'axis': {'range': [-10, 50]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [-10, 0], 'color': "red"},
                    {'range': [0, 10], 'color': "orange"},
                    {'range': [10, 50], 'color': "lightgreen"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0}}))
        
        st.plotly_chart(fig_gauge, use_container_width=True)
        if margem_real < 10:
            st.error(f"Perigo! Você acha que ganha {markup}%, mas ganha só {margem_real:.1f}%!")

    # --- SIMULADOR 2: PONTO DE EQUILÍBRIO VISUAL ---
    with col_sim2:
        st.header("⚖️ Ponto de Equilíbrio")
        custo_fixo = st.number_input("Custo Fixo (Aluguel, etc)", value=5000.0)
        
        margem_contribuicao = preco - (custo + (preco * imposto/100))
        
        if margem_contribuicao > 0:
            qtd_equilibrio = int(custo_fixo / margem_contribuicao)
            
            # Criando dados para o gráfico de linhas
            x_vals = list(range(0, int(qtd_equilibrio * 1.5), 10)) # Eixo X: Quantidade
            y_custos = [custo_fixo + (custo + (preco * imposto/100))*x for x in x_vals]
            y_receitas = [preco * x for x in x_vals]
            
            # Gráfico de Linhas (Break-even)
            fig_break = go.Figure()
            fig_break.add_trace(go.Scatter(x=x_vals, y=y_receitas, name='Receita (Entrada)', line=dict(color='green')))
            fig_break.add_trace(go.Scatter(x=x_vals, y=y_custos, name='Custos Totais', line=dict(color='red')))
            
            # Marca o ponto de cruzamento
            fig_break.add_vline(x=qtd_equilibrio, line_width=1, line_dash="dash", line_color="white")
            fig_break.update_layout(title="Onde suas contas se pagam", xaxis_title="Quantidade Vendida", yaxis_title="Dinheiro (R$)")
            
            st.plotly_chart(fig_break, use_container_width=True)
            
            st.success(f"Você precisa vender **{qtd_equilibrio} unidades** para sair do zero a zero.")
        else:
            st.error("Preço muito baixo! Você nunca pagará os custos fixos assim.")
