import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Analytics Pro MP - Master", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# CSS para melhorar o visual dos KPIs
st.markdown("""
<style>
    [data-testid="stMetricValue"] {font-size: 22px; color: #3b82f6;}
    .stTabs [data-baseweb="tab-list"] {gap: 10px;}
    .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap; background-color: #f1f5f9; border-radius: 4px;}
    .stTabs [aria-selected="true"] {background-color: #e2e8f0; border-bottom: 2px solid #3b82f6;}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. MOTOR DE DADOS (ETL + CÁLCULOS)
# ==============================================================================
@st.cache_data
def carregar_dados(arquivo):
    try:
        # Leitura Inteligente
        if arquivo.name.endswith('.csv'):
            try:
                df = pd.read_csv(arquivo)
            except:
                df = pd.read_csv(arquivo, sep=';')
        else:
            df = pd.read_excel(arquivo)
            
        # 1. Normalização de Nomes de Colunas
        df.columns = df.columns.str.strip().str.lower()
        mapa_colunas = {
            "quantidade": "Vendas", "qtd": "Vendas", "quant": "Vendas",
            "preco_unitario": "Preço", "preco": "Preço", "valor_unitario": "Preço", "vlr_unit": "Preço",
            "custo_unitario": "Custo", "custo": "Custo",
            "data_venda": "Data", "data": "Data", "date": "Data", "dia": "Data",
            "produto": "Produto", "descricao": "Produto", "sku": "Produto",
            "categoria": "Categoria", "grupo": "Categoria"
        }
        df = df.rename(columns=mapa_colunas)
        
        # 2. Tratamento de Tipos
        cols_num = ['Vendas', 'Preço', 'Custo']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data']).sort_values('Data')
            
        # 3. Cálculos Financeiros (Transacional)
        if 'Vendas' in df.columns and 'Preço' in df.columns:
            df["Faturamento"] = df["Vendas"] * df["Preço"]
            if 'Custo' in df.columns:
                df["Lucro"] = df["Faturamento"] - (df["Custo"] * df["Vendas"])
                # Margem linha a linha
                df["Margem_Perc"] = df.apply(lambda x: (x["Lucro"]/x["Faturamento"]*100) if x["Faturamento"]>0 else 0, axis=1)
        
        # Cria Categoria Geral se não existir
        if 'Categoria' not in df.columns:
            df['Categoria'] = 'Geral'
            
        return df
    except Exception as e:
        return f"Erro Crítico: {str(e)}"

def processar_estoque_avancado(df_vendas, margem_seguranca=1.2):
    """
    Motor Lógico: Calcula Estoque Simulado, PEPS, ABC e Cobertura.
    """
    # Agregação por Produto
    estoque = df_vendas.groupby(['Produto', 'Categoria']).agg({
        'Vendas': 'sum',
        'Preço': 'mean',          # Preço Médio Praticado
        'Margem_Perc': 'mean',    # Margem Média Praticada
        'Custo': ['mean', 'first', 'last'], # Mean=Médio, First=Antigo, Last=Recente (PEPS)
        'Data': ['min', 'max']    # Para calcular velocidade de venda
    }).reset_index()
    
    # Ajuste de Nomes (Flatten MultiIndex)
    estoque.columns = [
        'Produto', 'Categoria', 'Total_Vendido', 
        'Preco_Medio', 'Margem_Media', 
        'Custo_Medio', 'Custo_Antigo_PEPS', 'Custo_Recente_PEPS', 
        'Data_Inicio', 'Data_Fim'
    ]
    
    # 1. Simulação de Estoque Físico
    estoque['Estoque_Inicial_Sim'] = (estoque['Total_Vendido'] * margem_seguranca).astype(int)
    estoque['Estoque_Atual'] = (estoque['Estoque_Inicial_Sim'] - estoque['Total_Vendido']).clip(lower=0)
    
    # 2. Valoração Financeira (PEPS vs Médio)
    estoque['Valor_Total_PEPS'] = estoque['Estoque_Atual'] * estoque['Custo_Recente_PEPS']
    estoque['Valor_Total_Medio'] = estoque['Estoque_Atual'] * estoque['Custo_Medio']
    
    # 3. Classificação ABC (Pareto)
    estoque = estoque.sort_values('Valor_Total_PEPS', ascending=False)
    estoque['Acumulado_Valor'] = estoque['Valor_Total_PEPS'].cumsum()
    estoque['Perc_Acumulado'] = estoque['Acumulado_Valor'] / estoque['Valor_Total_PEPS'].sum()
    
    def get_abc(p):
        if p <= 0.80: return 'A'      # 80% do valor
        elif p <= 0.95: return 'B'    # +15% do valor
        else: return 'C'              # Resto (5%)
    estoque['Classe_ABC'] = estoque['Perc_Acumulado'].apply(get_abc)
    
    # 4. Logística (Cobertura e Ruptura)
    dias_totais = (estoque['Data_Fim'].max() - estoque['Data_Inicio'].min()).days
    if dias_totais < 1: dias_totais = 1
    
    estoque['Venda_Diaria'] = estoque['Total_Vendido'] / dias_totais
    estoque['Dias_Cobertura'] = estoque.apply(
        lambda x: (x['Estoque_Atual'] / x['Venda_Diaria']) if x['Venda_Diaria'] > 0 else 999, axis=1
    )
    
    # Status Visual
    estoque['Status_Ruptura'] = estoque['Dias_Cobertura'].apply(
        lambda x: '🔴 Crítico (<7d)' if x < 7 else ('🟡 Alerta (<15d)' if x < 15 else '🟢 Ok')
    )
    
    return estoque

# ==============================================================================
# 3. INTERFACE DO USUÁRIO
# ==============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3094/3094851.png", width=50)
    st.title("Painel de Controle")
    st.info("Importe o histórico de vendas para gerar a inteligência.")
    
    arquivo_upload = st.file_uploader("Arquivo de Dados (CSV/Excel)", type=["csv", "xlsx"])
    
    st.markdown("---")
    st.write("⚙️ **Configuração de Simulação**")
    nivel_seguranca = st.slider("Nível de Reposição (Estoque Inicial)", 1.0, 2.5, 1.3, 
                               help="1.3 = Estoque era 30% maior que as vendas do período.")

if arquivo_upload:
    df_raw = carregar_dados(arquivo_upload)
    
    if isinstance(df_raw, str): # Erro
        st.error(df_raw)
    else:
        # Processamento Principal
        df_completo = processar_estoque_avancado(df_raw, nivel_seguranca)
        
        # Estrutura de Abas
        aba_bi, aba_estoque, aba_sim = st.tabs([
            "📊 BI de Vendas & Estratégia", 
            "📦 Controladoria & Logística", 
            "🧠 Simulador & Pricing"
        ])
        
        # ----------------------------------------------------------------------
        # ABA 1: BI DE VENDAS
        # ----------------------------------------------------------------------
        with aba_bi:
            st.markdown("### 📈 Performance Comercial")
            
            # Big Numbers
            k1, k2, k3, k4 = st.columns(4)
            fat = df_raw['Faturamento'].sum()
            luc = df_raw['Lucro'].sum()
            margem_global = (luc/fat*100) if fat > 0 else 0
            
            k1.metric("Faturamento Total", f"R$ {fat:,.2f}")
            k2.metric("Lucro Líquido", f"R$ {luc:,.2f}")
            k3.metric("Margem Global", f"{margem_global:.1f}%")
            k4.metric("Total Transações", f"{len(df_raw)}")
            
            st.divider()
            
            # Gráficos Linha 1
            g1, g2 = st.columns([2, 1])
            
            with g1:
                st.subheader("Evolução Temporal")
                if 'Data' in df_raw.columns:
                    # Agrupa por Mês para limpar o visual
                    df_temp = df_raw.set_index('Data').resample('ME')['Faturamento'].sum().reset_index()
                    fig_line = px.line(df_temp, x='Data', y='Faturamento', markers=True, title="Faturamento Mensal", line_shape='spline')
                    fig_line.update_traces(line_color='#3b82f6', line_width=3)
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.warning("Coluna de Data não encontrada para gráfico temporal.")
            
            with g2:
                st.subheader("Mix por Categoria")
                fig_pie = px.pie(df_raw, values='Faturamento', names='Categoria', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)

            # Matriz Estratégica
            st.subheader("🎯 Matriz de Estratégia: Preço vs Margem")
            st.caption("Onde estão seus produtos? Bolhas grandes = Mais vendas.")
            
            fig_scat = px.scatter(
                df_completo, 
                x='Preco_Medio', y='Margem_Media', 
                size='Total_Vendido', color='Categoria',
                hover_name='Produto',
                title="Posicionamento de Produto",
                labels={'Preco_Medio': 'Preço Médio (R$)', 'Margem_Media': 'Margem (%)'}
            )
            # Linhas de referência
            fig_scat.add_hline(y=20, line_dash="dash", line_color="gray", annotation_text="Meta Margem 20%")
            st.plotly_chart(fig_scat, use_container_width=True)

        # ----------------------------------------------------------------------
        # ABA 2: CONTROLADORIA (ESTOQUE, ABC, PEPS)
        # ----------------------------------------------------------------------
        with aba_estoque:
            st.markdown("### 🏭 Gestão de Estoque & Custos")
            
            # KPIs Logísticos
            c1, c2, c3 = st.columns(3)
            val_estoque = df_completo['Valor_Total_PEPS'].sum()
            ruptura = len(df_completo[df_completo['Status_Ruptura'].str.contains('Crítico')])
            itens_a = len(df_completo[df_completo['Classe_ABC'] == 'A'])
            
            c1.metric("Valor Estoque (PEPS)", f"R$ {val_estoque:,.2f}", help="Calculado pelo Custo da Última Reposição")
            c2.metric("Risco de Ruptura (<7d)", ruptura, delta_color="inverse")
            c3.metric("Itens Classe A", itens_a, help="Representam 80% do valor do estoque")
            
            st.divider()
            
            # ABC e Cobertura
            col_abc, col_cob = st.columns([3, 2])
            
            with col_abc:
                st.markdown("#### 📦 Curva ABC (Pareto)")
                # Gráfico ABC Colorido
                fig_abc = px.scatter(
                    df_completo, 
                    x='Total_Vendido', y='Valor_Total_PEPS',
                    color='Classe_ABC',
                    color_discrete_map={'A': '#ef4444', 'B': '#f59e0b', 'C': '#10b981'},
                    hover_name='Produto',
                    log_x=True, # Escala logarítmica ajuda a ver melhor se tiver muita disparidade
                    title="Importância Financeira (Y) vs Giro (X)",
                    labels={'Total_Vendido': 'Giro (Log)', 'Valor_Total_PEPS': 'R$ Parado em Estoque'}
                )
                st.plotly_chart(fig_abc, use_container_width=True)
                
            with col_cob:
                st.markdown("#### 🚨 Top Alertas de Ruptura")
                # Filtra apenas quem tem estoque mas vai acabar logo
                df_rup = df_completo[(df_completo['Estoque_Atual'] > 0)].sort_values('Dias_Cobertura').head(10)
                
                fig_bar = px.bar(
                    df_rup, 
                    x='Dias_Cobertura', y='Produto', 
                    orientation='h',
                    color='Dias_Cobertura',
                    color_continuous_scale=['#ef4444', '#f59e0b', '#10b981'],
                    text_auto='.1f',
                    title="Dias Restantes de Estoque"
                )
                fig_bar.add_vline(x=7, line_dash="dash", line_color="red")
                st.plotly_chart(fig_bar, use_container_width=True)

            # Tabela Analítica
            with st.expander("📋 Ver Tabela de Estoque Detalhada"):
                st.dataframe(
                    df_completo[['Produto', 'Classe_ABC', 'Estoque_Atual', 'Custo_Recente_PEPS', 'Valor_Total_PEPS', 'Status_Ruptura']],
                    column_config={
                        "Valor_Total_PEPS": st.column_config.NumberColumn("Valor Total", format="R$ %.2f"),
                        "Custo_Recente_PEPS": st.column_config.NumberColumn("Custo Unit (PEPS)", format="R$ %.2f"),
                    },
                    use_container_width=True, hide_index=True
                )

        # ----------------------------------------------------------------------
        # ABA 3: SIMULADOR (INTEGRADO)
        # ----------------------------------------------------------------------
        with aba_sim:
            st.markdown("### 🛠️ Calculadora de Viabilidade & Break-even")
            st.caption("Selecione um produto da sua lista para puxar os custos reais e simular novos preços.")
            
            s1, s2 = st.columns([1, 2])
            
            with s1:
                st.markdown("#### Parâmetros")
                produtos_lista = df_completo['Produto'].unique()
                prod_sel = st.selectbox("Escolher Produto", produtos_lista)
                
                # Puxa dados do produto escolhido
                dados_p = df_completo[df_completo['Produto'] == prod_sel].iloc[0]
                custo_real = float(dados_p['Custo_Recente_PEPS'])
                preco_real = float(dados_p['Preco_Medio'])
                
                st.markdown("---")
                novo_custo = st.number_input("Custo Unitário (R$)", value=custo_real)
                novo_preco = st.number_input("Preço de Venda (R$)", value=preco_real)
                imposto = st.number_input("Impostos (%)", value=10.0)
                custo_fixo = st.number_input("Custo Fixo Rateado (R$)", value=1500.0, help="Quanto este produto precisa pagar do aluguel/luz?")
                
            with s2:
                st.markdown("#### Resultado da Simulação")
                
                # Cálculos
                val_imposto = novo_preco * (imposto/100)
                margem_contrib = novo_preco - novo_custo - val_imposto
                
                # Métricas Unitárias
                k_s1, k_s2, k_s3 = st.columns(3)
                
                if margem_contrib > 0:
                    pto_equilibrio = custo_fixo / margem_contrib
                    lucratividade = (margem_contrib / novo_preco) * 100
                    
                    k_s1.metric("Margem Contrib.", f"R$ {margem_contrib:.2f}")
                    k_s2.metric("Lucratividade", f"{lucratividade:.1f}%")
                    k_s3.metric("Break-even (Qtd)", f"{int(pto_equilibrio)} un")
                    
                    st.success(f"Você precisa vender **{int(pto_equilibrio)} unidades** para começar a lucrar.")
                    
                    # Gráfico Break-even
                    x_vals = list(range(0, int(pto_equilibrio * 2) + 2, max(1, int(pto_equilibrio//10))))
                    y_rec = [x * novo_preco for x in x_vals]
                    y_custo = [custo_fixo + (novo_custo + val_imposto) * x for x in x_vals]
                    
                    fig_be = go.Figure()
                    fig_be.add_trace(go.Scatter(x=x_vals, y=y_rec, name='Receita', line=dict(color='#10b981', width=3)))
                    fig_be.add_trace(go.Scatter(x=x_vals, y=y_custo, name='Custo Total', line=dict(color='#ef4444', width=3)))
                    fig_be.add_vline(x=pto_equilibrio, line_dash="dot", annotation_text="Equilíbrio")
                    
                    fig_be.update_layout(title="Curva de Ponto de Equilíbrio", height=350, xaxis_title="Quantidade", yaxis_title="Reais (R$)")
                    st.plotly_chart(fig_be, use_container_width=True)
                    
                else:
                    st.error("🚨 Preço insuficiente! A Margem de Contribuição é negativa. Você perde dinheiro a cada venda.")
                    st.metric("Prejuízo por Unidade", f"R$ {margem_contrib:.2f}")

else:
    # Tela de Boas-vindas (Vazia)
    st.markdown("""
    <div style="text-align: center; margin-top: 50px;">
        <h2>👋 Bem-vindo ao Analytics Pro Master</h2>
        <p style="color: gray;">Sua central de inteligência de vendas e estoque.</p>
        <p>Utilize a barra lateral para carregar seu arquivo Excel ou CSV.</p>
    </div>
    """, unsafe_allow_html=True)
