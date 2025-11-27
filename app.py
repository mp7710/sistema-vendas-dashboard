import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression

# Configuração visual do Matplotlib/Seaborn
sns.set_style("whitegrid")

# --- ESTRUTURA E LAYOUT DO STREAMLIT ---
st.title("🚀 Consultor de Negócios 2.0")

# Área de Upload na Barra Lateral (Sidebar)
uploaded_file = st.sidebar.file_uploader("Carregar Planilha", type=["xlsx"], 
                                         help="Faça o upload da planilha de vendas (.xlsx)")

# Definição das Abas
tab1, tab2 = st.tabs(["📊 Dashboard Interativo", "🤖 Simulador de Lucro"])

# --- LÓGICA PRINCIPAL (Executa se o arquivo foi carregado) ---
if uploaded_file is not None:
    try:
        # Lê o Excel para um DataFrame
        tabela_original = pd.read_excel(uploaded_file)
        df = tabela_original.copy() # Cria uma cópia para trabalhar
        
        # 1. ENGENHARIA DE RECURSOS (Cálculos de Lucro e Faturamento)
        if "Preco_Unitario" in df.columns and "Custo_Unitario" in df.columns and "Quantidade" in df.columns:
            df["Faturamento"] = df["Quantidade"] * df["Preco_Unitario"]
            df["Custo_Total"] = df["Quantidade"] * df["Custo_Unitario"]
            df["Lucro"] = df["Faturamento"] - df["Custo_Total"]
        else:
            st.error("As colunas essenciais ('Preco_Unitario', 'Custo_Unitario', 'Quantidade') não foram encontradas. Verifique sua planilha.")
            # Sai da execução se as colunas não existirem
            st.stop()
            
        # 2. ANÁLISE (Agrupamento por Produto)
        resumo_por_produto = df.groupby("Produto")[["Lucro", "Quantidade"]].sum().sort_values(by="Lucro", ascending=False)


        # ==========================================================
        # ABAS: 1. DASHBOARD INTERATIVO
        # ==========================================================
        with tab1:
            st.header("Análise Detalhada de Lucro")
            
            # Métrica de Lucro Total
            lucro_total = resumo_por_produto["Lucro"].sum()
            st.metric(label="💰 Lucro Total da Empresa", value=f"R$ {lucro_total:,.2f}")

            # Exibição do Resumo (Tabela)
            st.subheader("Ranking de Lucro por Produto")
            st.dataframe(resumo_por_produto, use_container_width=True)

            # Gráfico de Lucratividade
            st.subheader("Visualização dos Resultados")
            fig, ax = plt.subplots(figsize=(10, 5)) 
            sns.barplot(x=resumo_por_produto.index, y=resumo_por_produto["Lucro"], ax=ax, palette="viridis")
            ax.set_title("Lucro por Categoria de Produto")
            ax.set_ylabel("Lucro (R$)")
            plt.xticks(rotation=45) 
            st.pyplot(fig) # Comando para mostrar gráfico no site


        # ==========================================================
        # ABAS: 2. SIMULADOR DE LUCRO (MACHINE LEARNING)
        # ==========================================================
        with tab2:
            st.header("Previsão de Lucro com Machine Learning")
            st.write("O modelo de Regressão Linear foi treinado para encontrar a tendência entre 'Quantidade Vendida' e 'Lucro Total'.")
            
            # Treinamento da IA
            X = df[["Quantidade"]]
            y = df["Lucro"]
            modelo = LinearRegression()
            modelo.fit(X, y)
            
            # Input do Usuário (Simulador)
            st.subheader("Defina a sua Meta de Vendas")
            qtd_usuario = st.slider("Quantidade de itens que você pretende vender (em um período):", 
                                    min_value=10, max_value=200, value=50, step=10)
            
            # Previsão da IA
            previsao = modelo.predict([[qtd_usuario]])
            
            st.markdown("---")
            st.subheader("Resultado da Previsão")
            st.metric(label=f"Lucro Estimado para {qtd_usuario} Vendas", value=f"R$ {previsao[0]:,.2f}")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar seus dados. Detalhes: {e}")
        st.info("Verifique se as colunas (Preco_Unitario, Custo_Unitario, Quantidade) estão corretas na planilha.")

# Se o arquivo não foi carregado, mostra a mensagem de instrução
else:
    with tab1:
        st.info("⬆️ Faça o upload da sua planilha de vendas na barra lateral esquerda para começar a análise.")
