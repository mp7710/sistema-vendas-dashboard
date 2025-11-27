import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuração da página
st.set_page_config(page_title="Dashboard de Vendas", layout="wide")
sns.set_style("whitegrid")

# --- BARRA LATERAL (CONFIGURAÇÕES) ---
st.sidebar.title("🎛️ Painel de Controle")
st.sidebar.write("Defina suas metas de lucro aqui:")

# Inputs Interativos
meta_eletronicos = st.sidebar.slider("Meta Eletrônicos (%)", 10, 50, 10) / 100
meta_moda = st.sidebar.slider("Meta Moda (%)", 20, 80, 50) / 100
meta_servicos = st.sidebar.slider("Meta Serviços (%)", 50, 100, 80) / 100
meta_padrao = st.sidebar.slider("Meta Padrão (Outros)", 10, 50, 20) / 100

# Dicionário de metas
metas_por_categoria = {
    "Eletronicos": meta_eletronicos,
    "Moda": meta_moda,
    "Servicos": meta_servicos,
    "Geral": meta_padrao # Adicionei o Geral aqui
}

# --- TÍTULO DO SITE ---
st.title("📊 Gestão Inteligente de Vendas")
st.write("Faça upload da sua planilha para receber a análise.")

# --- UPLOAD DO ARQUIVO ---
arquivo_upload = st.file_uploader("Arraste seu arquivo Excel aqui", type=["xlsx"])

if arquivo_upload is not None:
    # Lê o arquivo
    tabela = pd.read_excel(arquivo_upload)
    
    # --- A MUDANÇA MÁGICA AQUI ---
    # Se não tiver a coluna Categoria, a gente cria ela na marra!
    if "Categoria" not in tabela.columns:
        tabela["Categoria"] = "Geral"
        st.warning("⚠️ Aviso: Não encontrei a coluna 'Categoria'. Classifiquei tudo como 'Geral' para não dar erro.")
    
    # CÁLCULOS
    tabela["Faturamento"] = tabela["Vendas"] * tabela["Preço"]
    tabela["Lucro"] = tabela["Faturamento"] - (tabela["Custo"] * tabela["Vendas"])
    
    # --- MÉTRICAS GERAIS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Faturamento Total", f"R$ {tabela['Faturamento'].sum():,.2f}")
    col2.metric("Lucro Total", f"R$ {tabela['Lucro'].sum():,.2f}")
    col3.metric("Total Vendido (Qtd)", int(tabela['Vendas'].sum()))

    st.divider()

    # --- O ASSISTENTE VIRTUAL ---
    st.subheader("🤖 Análise do Assistente")
    
    for index, linha in tabela.iterrows():
        produto = linha["Produto"]
        categoria = linha["Categoria"]
        lucro = linha["Lucro"]
        faturamento = linha["Faturamento"]
        
        # Busca a meta (se for Geral, usa a meta padrão)
        meta_alvo = metas_por_categoria.get(categoria, meta_padrao)
        
        if faturamento > 0:
            margem_real = lucro / faturamento
            
            if lucro < 0:
                st.error(f"🔴 **{produto}**: Prejuízo de R$ {lucro:.2f}. Reveja custos!")
            elif margem_real < meta_alvo:
                st.warning(f"⚠️ **{produto}**: Margem de {margem_real:.1%} (Meta: {meta_alvo:.0%}).")
            else:
                st.success(f"✅ **{produto}**: Excelente! Margem de {margem_real:.1%}.")

    # --- MOSTRAR TABELA ---
    with st.expander("Ver Tabela Completa"):
        st.dataframe(tabela)

    # --- GRÁFICOS ---
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("Lucro por Produto")
        fig1, ax1 = plt.subplots()
        cores = ['red' if l < 0 else 'green' for l in tabela['Lucro']]
        sns.barplot(data=tabela, x="Produto", y="Lucro", palette=cores, ax=ax1)
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45)
        st.pyplot(fig1)
        
    with col_graf2:
        st.subheader("Vendas por Categoria")
        fig2, ax2 = plt.subplots()
        # Se tudo for "Geral", o gráfico vai mostrar uma fatia só, mas funciona!
        tabela.groupby("Categoria")["Faturamento"].sum().plot.pie(autopct='%1.1f%%', ax=ax2)
        ax2.set_ylabel('')
        st.pyplot(fig2)

else:
    st.info("Aguardando upload do arquivo...")
# --- ADICIONE ISTO NO FINAL DO SEU ARQUIVO APP.PY ---

st.divider() # Uma linha divisória bonita

st.header("🧮 Calculadora de Precificação Inteligente")
st.write("Descubra por quanto você deve vender para ter o lucro desejado.")

# Cria 3 colunas para ficar organizado
col_calc1, col_calc2, col_calc3 = st.columns(3)

with col_calc1:
    custo_prod = st.number_input("Custo do Produto (R$)", min_value=0.0, value=50.0)

with col_calc2:
    margem_desejada = st.number_input("Margem de Lucro Desejada (%)", min_value=1.0, value=30.0) / 100

with col_calc3:
    imposto = st.number_input("Impostos/Taxas (%)", min_value=0.0, value=10.0) / 100

# Botão para calcular
if st.button("Calcular Preço Ideal"):
    # Fórmula: Preço = Custo / (1 - (Margem + Imposto))
    # Essa é a fórmula correta de Markup (formação de preço de venda)
    divisor = 1 - (margem_desejada + imposto)
    
    if divisor <= 0:
        st.error("Erro: A soma de Margem + Imposto não pode passar de 100%!")
    else:
        preco_ideal = custo_prod / divisor
        lucro_liquido = preco_ideal * margem_desejada
        
        st.success(f"💰 Venda por: **R$ {preco_ideal:.2f}**")
        st.info(f"Você vai lucrar livre: **R$ {lucro_liquido:.2f}** por unidade.")