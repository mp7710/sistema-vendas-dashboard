import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuração da página
st.set_page_config(page_title="Consultor Inteligente de Vendas", layout="wide", page_icon="💼")
sns.set_style("whitegrid")

# Título Principal
st.title("💼 Consultor Inteligente de Negócios")
st.write("Analise seus dados passados e simule o futuro do seu negócio.")

# Criação de Abas
aba1, aba2 = st.tabs(["📊 Dashboard de Vendas (Arquivo)", "🧠 Simulador Estratégico (Calculadora)"])

# ==============================================================================
# ABA 1: O DASHBOARD DE VENDAS
# ==============================================================================
with aba1:
    st.header("Análise de Dados Históricos")
    
    # Barra lateral
    with st.sidebar:
        st.header("🎛️ Painel de Controle")
        # ACEITA CSV E EXCEL
        arquivo_upload = st.file_uploader("📂 Carregar Planilha", type=["xlsx", "csv"])
        
        with st.expander("⚙️ Configurar Metas"):
            meta_eletronicos = st.slider("Meta Eletrônicos (%)", 10, 50, 10) / 100
            meta_moda = st.slider("Meta Moda (%)", 20, 80, 50) / 100
            meta_servicos = st.slider("Meta Serviços (%)", 50, 100, 80) / 100
            meta_geral = st.slider("Meta Geral (%)", 10, 50, 20) / 100

    metas_por_categoria = {
        "Eletronicos": meta_eletronicos,
        "Moda": meta_moda,
        "Servicos": meta_servicos,
        "Geral": meta_geral
    }

    if arquivo_upload is not None:
        # ---------------------------------------------------------
        # LEITURA INTELIGENTE (CSV OU EXCEL)
        # ---------------------------------------------------------
        try:
            if arquivo_upload.name.endswith('.csv'):
                try:
                    tabela = pd.read_csv(arquivo_upload)
                except:
                    arquivo_upload.seek(0)
                    tabela = pd.read_csv(arquivo_upload, sep=';')
            else:
                tabela = pd.read_excel(arquivo_upload)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")
            st.stop()

        # ---------------------------------------------------------
        # TRADUTOR DE COLUNAS (O SEGREDO PARA A PLANILHA NOVA)
        # ---------------------------------------------------------
        # Remove espaços extras nos nomes das colunas
        tabela.columns = tabela.columns.str.strip()
        
        # Dicionário de tradução: "Nome Novo" -> "Nome Padrão"
        mapa_colunas = {
            "Quantidade": "Vendas",
            "Preco_Unitario": "Preço",
            "Custo_Unitario": "Custo",
            "Preco": "Preço" 
        }
        
        # Renomeia as colunas automaticamente se encontrar os nomes novos
        tabela = tabela.rename(columns=mapa_colunas)
        
        # ---------------------------------------------------------
        # VALIDAÇÃO
        # ---------------------------------------------------------
        colunas_necessarias = ["Vendas", "Preço", "Custo", "Produto"]
        faltantes = [col for col in colunas_necessarias if col not in tabela.columns]
        
        if faltantes:
            st.error(f"❌ O arquivo não tem as colunas padrão nem as novas compatíveis.")
            st.warning(f"Colunas que faltam (ou estão com nome diferente): {', '.join(faltantes)}")
            st.stop()

        # Tratamento de categoria (Se não tiver, cria Geral)
        if "Categoria" not in tabela.columns:
            tabela["Categoria"] = "Geral"
            st.warning("⚠️ Classificando tudo como 'Geral' (coluna Categoria não encontrada).")
        
        # Limpeza de dados na coluna Categoria
        if tabela["Categoria"].dtype == 'object':
            tabela["Categoria"] = tabela["Categoria"].str.strip()

        # Cálculos
        tabela["Faturamento"] = tabela["Vendas"] * tabela["Preço"]
        tabela["Lucro"] = tabela["Faturamento"] - (tabela["Custo"] * tabela["Vendas"])
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Faturamento Total", f"R$ {tabela['Faturamento'].sum():,.2f}")
        col2.metric("Lucro Total", f"R$ {tabela['Lucro'].sum():,.2f}")
        col3.metric("Total Vendido (Qtd)", int(tabela['Vendas'].sum()))
        
        st.divider()
        
        # Assistente Virtual Inteligente (Agrupado por produto)
        st.subheader("🤖 Diagnóstico Automático")
        
        # Agrupa por produto para somar vendas repetidas
        analise_produto = tabela.groupby(["Produto", "Categoria"]).agg({
            "Faturamento": "sum",
            "Lucro": "sum"
        }).reset_index()

        for index, linha in analise_produto.iterrows():
            produto = linha["Produto"]
            categoria = linha["Categoria"]
            lucro = linha["Lucro"]
            faturamento = linha["Faturamento"]
            meta = metas_por_categoria.get(categoria, meta_geral)
            
            if faturamento > 0:
                margem_real = lucro / faturamento
                if lucro < 0:
                    st.error(f"🔴 **{produto}**: Prejuízo acumulado de R$ {lucro:.2f}!")
                elif margem_real < meta:
                    st.warning(f"⚠️ **{produto}**: Margem de {margem_real:.1%} (Meta: {meta:.0%})")
                else:
                    st.success(f"✅ **{produto}**: Margem Saudável de {margem_real:.1%}")

        # Visualização Gráfica
        st.subheader("Performance Visual")
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # Agrupa dados para o gráfico ficar limpo (soma vendas do mesmo produto)
        grafico_dados = tabela.groupby("Produto")[["Lucro"]].sum().reset_index()
        
        cores = ['red' if l < 0 else 'green' for l in grafico_dados['Lucro']]
        sns.barplot(data=grafico_dados, x="Produto", y="Lucro", palette=cores, ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Aguardando upload do arquivo (Excel ou CSV)...")

# ==============================================================================
# ABA 2: SIMULADOR ESTRATÉGICO
# ==============================================================================
with aba2:
    st.header("Ferramentas de Decisão Financeira")
    col_esq, col_dir = st.columns(2)

    # --- MARKUP vs MARGEM ---
    with col_esq:
        st.subheader("🔍 Markup vs Margem Real")
        custo_produto = st.number_input("Custo de Compra (R$)", value=50.0)
        markup_aplicado = st.number_input("Quanto você adiciona em cima? (%)", value=30.0)
        imposto = st.number_input("Impostos sobre venda (%)", value=5.0)
        
        preco_venda = custo_produto * (1 + markup_aplicado/100)
        valor_imposto = preco_venda * (imposto/100)
        lucro_liquido = preco_venda - valor_imposto - custo_produto
        margem_real = (lucro_liquido / preco_venda) * 100
        
        st.divider()
        st.write(f"🏷️ Preço Final: **R$ {preco_venda:.2f}**")
        
        col_a, col_b = st.columns(2)
        col_a.metric("Você ACHOU que ganharia", f"{markup_aplicado}%")
        col_b.metric("Margem REAL (No bolso)", f"{margem_real:.1f}%", delta=f"{margem_real - markup_aplicado:.1f}%")
        
        if margem_real < 10:
            st.error("🚨 Margem perigosamente baixa!")
        else:
            st.info(f"Sobra R$ {lucro_liquido:.2f} limpos por venda.")

    # --- PONTO DE EQUILÍBRIO ---
    with col_dir:
        st.subheader("⚖️ Ponto de Equilíbrio")
        custo_fixo = st.number_input("Custo Fixo Mensal (Aluguel, Luz...)", value=5000.0)
        
        preco_unitario = st.number_input("Preço Médio (R$)", value=preco_venda, disabled=True)
        custo_variavel = st.number_input("Custo Variável (Prod + Imposto)", value=custo_produto + valor_imposto, disabled=True)
        
        margem_contribuicao = preco_unitario - custo_variavel
        
        if margem_contribuicao <= 0:
            st.error("Preço insuficiente para pagar custos variáveis!")
        else:
            qtd_equilibrio = custo_fixo / margem_contribuicao
            fat_equilibrio = qtd_equilibrio * preco_unitario
            
            st.divider()
            st.metric("Vendas Necessárias (Qtd)", f"{int(qtd_equilibrio)} un")
            st.caption(f"Faturamento necessário: R$ {fat_equilibrio:,.2f}")
            
            progresso = min(100, int((margem_contribuicao/preco_unitario)*100))
            st.progress(progresso)
            st.caption(f"Margem de Contribuição: R$ {margem_contribuicao:.2f} por item")

# ==============================================================================
# RODAPÉ COM SUA ASSINATURA MP
# ==============================================================================
with st.sidebar:
    st.markdown("---")
    st.markdown("""
        <style>
        .logo-container {
            display: flex; justify-content: center; align-items: center;
            background-color: #0E1117; border: 2px solid #4B4B4B;
            border-radius: 12px; width: 80px; height: 80px; margin: auto;
            margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .logo-text {
            font-family: 'Helvetica', sans-serif; font-weight: bold;
            font-size: 35px; color: #FFFFFF; margin: 0; line-height: 1;
        }
        </style>
        <div class="logo-container"><p class="logo-text">MP</p></div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='text-align: center'>", unsafe_allow_html=True)
    st.markdown("Desenvolvido por:")
    st.markdown("**Maurílio Pereira Santana Oliveira Nunes**")
    st.caption("📧 mauriliopnunes77@gmail.com")
    st.markdown("</div>", unsafe_allow_html=True)
