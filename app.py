import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAÇÃO E CACHE
# ==============================================================================
st.set_page_config(page_title="Analytics Pro MP - Controladoria", layout="wide", page_icon="🏭")

@st.cache_data
def carregar_dados(arquivo):
    try:
        if arquivo.name.endswith('.csv'):
            df = pd.read_csv(arquivo)
        else:
            df = pd.read_excel(arquivo)
            
        # Normalização
        df.columns = df.columns.str.strip().str.lower()
        mapa = {
            "quantidade": "Vendas", "qtd": "Vendas",
            "preco_unitario": "Preço", "preco": "Preço", "valor": "Preço",
            "custo_unitario": "Custo", "custo": "Custo",
            "data_venda": "Data", "date": "Data",
            "produto": "Produto", "categoria": "Categoria"
        }
        df = df.rename(columns=mapa)
        
        # Tipagem e Ordenação (Essencial para PEPS)
        cols_num = ['Vendas', 'Preço', 'Custo']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'])
            df = df.sort_values('Data') # Ordena do mais antigo para o mais novo
            
        # Cálculos Base
        if 'Vendas' in df.columns and 'Preço' in df.columns:
            df["Faturamento"] = df["Vendas"] * df["Preço"]
            if 'Custo' in df.columns:
                df["Lucro"] = df["Faturamento"] - (df["Custo"] * df["Vendas"])
            
        return df
    except Exception as e:
        return str(e)

# Função Processamento Avançado (ABC + PEPS)
def processar_controladoria(df_vendas, margem_seguranca=1.2):
    # Agrupa por produto
    # Para PEPS, precisamos do Custo do PRIMEIRO registro e do ÚLTIMO registro
    estoque = df_vendas.groupby(['Produto', 'Categoria']).agg({
        'Vendas': 'sum',
        'Preço': 'mean',
        'Custo': ['mean', 'first', 'last'], # Mean=Média Ponderada, First=Antigo, Last=Recente
        'Data': ['min', 'max']
    }).reset_index()
    
    # Ajuste dos nomes das colunas (MultiIndex)
    estoque.columns = [
        'Produto', 'Categoria', 'Total_Vendido', 
        'Preco_Medio', 'Custo_Medio', 'Custo_Antigo_PEPS', 'Custo_Recente_PEPS', 
        'Data_Inicio', 'Data_Fim'
    ]
    
    # 1. Simulação de Quantidade em Estoque
    estoque['Estoque_Inicial_Simulado'] = (estoque['Total_Vendido'] * margem_seguranca).astype(int)
    estoque['Estoque_Atual'] = estoque['Estoque_Inicial_Simulado'] - estoque['Total_Vendido']
    estoque['Estoque_Atual'] = estoque['Estoque_Atual'].clip(lower=0) # Evita negativo
    
    # 2. Métodos de Valoração (Média vs PEPS)
    # Custo Médio: Valoriza pelo histórico total
    estoque['Valor_Estoque_Medio'] = estoque['Estoque_Atual'] * estoque['Custo_Medio']
    # PEPS: Assume que o que sobrou são os itens mais novos (Custo Recente)
    estoque['Valor_Estoque_PEPS'] = estoque['Estoque_Atual'] * estoque['Custo_Recente_PEPS']
    
    # 3. Classificação ABC (Baseado no Valor PEPS)
    estoque = estoque.sort_values('Valor_Estoque_PEPS', ascending=False)
    estoque['Acumulado_Valor'] = estoque['Valor_Estoque_PEPS'].cumsum()
    estoque['Percentual_Acumulado'] = estoque['Acumulado_Valor'] / estoque['Valor_Estoque_PEPS'].sum()
    
    def definir_classe(p):
        if p <= 0.80: return 'A'
        elif p <= 0.95: return 'B'
        else: return 'C'
        
    estoque['Classe_ABC'] = estoque['Percentual_Acumulado'].apply(definir_classe)
    
    return estoque

# ==============================================================================
# 2. INTERFACE
# ==============================================================================
with st.sidebar:
    st.markdown("## 🏭 Parâmetros")
    arquivo_upload = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx"])
    margem = st.slider("Simulação de Estoque Inicial", 1.0, 2.5, 1.3)

if arquivo_upload:
    df_raw = carregar_dados(arquivo_upload)
    
    if isinstance(df_raw, str):
        st.error(f"Erro: {df_raw}")
    else:
        df_control = processar_controladoria(df_raw, margem)
        
        st.title("📊 Controladoria de Estoque: ABC & PEPS")
        
        # --- RESUMO DE VALORAÇÃO ---
        st.markdown("### 💰 Valoração do Estoque")
        col1, col2, col3 = st.columns(3)
        
        val_medio = df_control['Valor_Estoque_Medio'].sum()
        val_peps = df_control['Valor_Estoque_PEPS'].sum()
        delta_val = val_peps - val_medio
        
        col1.metric("Valoração Custo Médio", f"R$ {val_medio:,.2f}", help="Custo ponderado histórico")
        col2.metric("Valoração PEPS/FIFO", f"R$ {val_peps:,.2f}", 
                   delta=f"R$ {delta_val:,.2f}", 
                   help="Considera que o estoque atual vale o preço da última reposição (Mais realista para reposição)")
        
        # Contagem ABC
        contagem = df_control['Classe_ABC'].value_counts()
        col3.metric("Mix de Produtos", f"{len(df_control)} SKUs", f"A: {contagem.get('A',0)} | B: {contagem.get('B',0)} | C: {contagem.get('C',0)}")

        st.divider()

        # --- ANÁLISE ABC ---
        st.subheader("📦 Curva ABC (Pareto)")
        c1, c2 = st.columns([2, 1])
        
        with c1:
            # Gráfico de Dispersão ABC
            fig_abc = px.scatter(
                df_control, 
                x='Total_Vendido', 
                y='Valor_Estoque_PEPS',
                color='Classe_ABC',
                size='Estoque_Atual',
                hover_name='Produto',
                color_discrete_map={'A': '#ef4444', 'B': '#f59e0b', 'C': '#10b981'},
                title="Matriz ABC: Importância Financeira vs Giro",
                labels={'Total_Vendido': 'Volume de Saída (Giro)', 'Valor_Estoque_PEPS': 'Valor Armazenado (R$)'}
            )
            # Linha de corte visual (apenas ilustrativa)
            st.plotly_chart(fig_abc, use_container_width=True)
            st.caption("Eixo Y: Dinheiro parado no estoque. Eixo X: O quanto o produto gira.")

        with c2:
            st.markdown("#### Distribuição de Valor")
            df_abc_sum = df_control.groupby('Classe_ABC')['Valor_Estoque_PEPS'].sum().reset_index()
            fig_pie = px.pie(df_abc_sum, names='Classe_ABC', values='Valor_Estoque_PEPS', 
                             color='Classe_ABC',
                             color_discrete_map={'A': '#ef4444', 'B': '#f59e0b', 'C': '#10b981'},
                             hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            st.info("💡 **Classe A:** Poucos itens que representam 80% do valor. Devem ter contagem rigorosa e estoque de segurança baixo.")

        st.divider()

        # --- TABELA DETALHADA ---
        with st.expander("📋 Ver Tabela Analítica (PEPS vs Médio)", expanded=True):
            st.dataframe(
                df_control[['Produto', 'Classe_ABC', 'Estoque_Atual', 'Custo_Medio', 'Custo_Recente_PEPS', 'Valor_Estoque_PEPS']],
                column_config={
                    "Custo_Medio": st.column_config.NumberColumn("Custo Médio", format="R$ %.2f"),
                    "Custo_Recente_PEPS": st.column_config.NumberColumn("Custo Reposição (PEPS)", format="R$ %.2f"),
                    "Valor_Estoque_PEPS": st.column_config.NumberColumn("Total (PEPS)", format="R$ %.2f"),
                    "Classe_ABC": st.column_config.TextColumn("Classe", width="small"),
                },
                hide_index=True,
                use_container_width=True
            )

else:
    st.info("Aguardando arquivo de dados...")

    st.markdown("Maurílio Pereira Santana Oliveira Nunes")

    st.caption("📧 mauriliopnunes77@gmail.com")

