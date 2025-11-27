import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuração da página
st.set_page_config(page_title="Consultor Inteligente de Vendas", layout="wide")
sns.set_style("whitegrid")

# Título Principal
st.title("💼 Consultor Inteligente de Negócios")
st.write("Analise seus dados passados e simule o futuro do seu negócio.")

# Criação de Abas para separar "Análise de Arquivo" das "Simulações"
aba1, aba2 = st.tabs(["📊 Dashboard de Vendas (Excel)", "🧠 Simulador Estratégico (Calculadora)"])

# ==============================================================================
# ABA 1: O DASHBOARD DE VENDAS (Seu código original melhorado)
# ==============================================================================
with aba1:
    st.header("Análise de Dados Históricos")
    
    # Barra lateral de metas (agora específica para esta aba)
    with st.expander("⚙️ Configurar Metas de Lucro para o Gráfico"):
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

    arquivo_upload = st.file_uploader("Arraste seu relatorio_vendas.xlsx aqui", type=["xlsx"])

    if arquivo_upload is not None:
        tabela = pd.read_excel(arquivo_upload)
        
        # Tratamento de erro se não tiver categoria
        if "Categoria" not in tabela.columns:
            tabela["Categoria"] = "Geral"
            st.warning("⚠️ Coluna 'Categoria' não encontrada. Usando 'Geral'.")
        
        # Cálculos básicos
        tabela["Faturamento"] = tabela["Vendas"] * tabela["Preço"]
        tabela["Lucro"] = tabela["Faturamento"] - (tabela["Custo"] * tabela["Vendas"])
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Faturamento Total", f"R$ {tabela['Faturamento'].sum():,.2f}")
        col2.metric("Lucro Total", f"R$ {tabela['Lucro'].sum():,.2f}")
        col3.metric("Total Vendido (Qtd)", int(tabela['Vendas'].sum()))
        
        st.divider()
        
        # Assistente Virtual
        st.subheader("🤖 Diagnóstico Automático")
        for index, linha in tabela.iterrows():
            produto = linha["Produto"]
            categoria = linha["Categoria"]
            lucro = linha["Lucro"]
            faturamento = linha["Faturamento"]
            meta = metas_por_categoria.get(categoria, meta_geral)
            
            if faturamento > 0:
                margem_real = lucro / faturamento
                if lucro < 0:
                    st.error(f"🔴 **{produto}**: Prejuízo de R$ {lucro:.2f}!")
                elif margem_real < meta:
                    st.warning(f"⚠️ **{produto}**: Margem de {margem_real:.1%} (Abaixo da meta de {meta:.0%})")
                else:
                    st.success(f"✅ **{produto}**: Margem Saudável de {margem_real:.1%}")

        # Visualização Gráfica
        st.subheader("Performance Visual")
        fig, ax = plt.subplots(figsize=(10, 4))
        cores = ['red' if l < 0 else 'green' for l in tabela['Lucro']]
        sns.barplot(data=tabela, x="Produto", y="Lucro", palette=cores, ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Aguardando upload do arquivo Excel...")

# ==============================================================================
# ABA 2: O SIMULADOR ESTRATÉGICO (O pedido dos áudios!)
# ==============================================================================
with aba2:
    st.header("Ferramentas de Decisão Financeira")
    st.write("Simule cenários e descubra a verdade sobre seus números.")
    
    col_esq, col_dir = st.columns(2)

    # --- FERRAMENTA 1: MARKUP vs MARGEM REAL (O "Choque de Realidade") ---
    with col_esq:
        st.subheader("🔍 A Ilusão do Lucro (Markup vs Margem)")
        st.caption("Você acha que ganha X, mas na verdade ganha Y.")
        
        custo_produto = st.number_input("Custo de Compra (R$)", value=50.0)
        markup_aplicado = st.number_input("Quanto você adiciona em cima? (%)", value=30.0)
        imposto = st.number_input("Impostos sobre venda (%)", value=5.0)
        
        # Cálculos
        preco_venda = custo_produto * (1 + markup_aplicado/100)
        valor_imposto = preco_venda * (imposto/100)
        lucro_liquido = preco_venda - valor_imposto - custo_produto
        margem_real = (lucro_liquido / preco_venda) * 100
        
        st.divider()
        st.write(f"🏷️ Preço Final de Venda: **R$ {preco_venda:.2f}**")
        
        # Comparativo Visual
        col_a, col_b = st.columns(2)
        col_a.metric(label="O que você ACHOU que ganharia", value=f"{markup_aplicado}%")
        col_b.metric(label="Sua Margem REAL (No bolso)", value=f"{margem_real:.1f}%", delta=f"{margem_real - markup_aplicado:.1f}%")
        
        if margem_real < 10:
            st.error("🚨 Cuidado! Sua margem real está perigosamente baixa.")
        else:
            st.info(f"De cada R$ 100,00 vendidos, sobram R$ {margem_real:.2f} limpos.")

    # --- FERRAMENTA 2: PONTO DE EQUILÍBRIO (Break-even) ---
    with col_dir:
        st.subheader("⚖️ Ponto de Equilíbrio")
        st.caption("Quantas unidades vender só para pagar as contas?")
        
        custo_fixo = st.number_input("Custo Fixo Mensal (Aluguel, Luz, Salários)", value=5000.0)
        
        # Usando os dados da simulação ao lado ou novos
        st.write("--- Dados do Produto ---")
        preco_unitario = st.number_input("Preço Médio de Venda (R$)", value=preco_venda, disabled=True)
        custo_variavel = st.number_input("Custo Variável Unitário (Produto + Imposto)", value=custo_produto + valor_imposto, disabled=True)
        
        # Cálculo
        margem_contribuicao = preco_unitario - custo_variavel
        
        if margem_contribuicao <= 0:
            st.error("Erro: Você perde dinheiro em cada venda! Aumente o preço.")
        else:
            qtd_equilibrio = custo_fixo / margem_contribuicao
            faturamento_equilibrio = qtd_equilibrio * preco_unitario
            
            st.divider()
            st.metric("Meta Mínima de Vendas (Qtd)", f"{int(qtd_equilibrio)} unidades")
            st.write(f"Isso gera um faturamento de **R$ {faturamento_equilibrio:,.2f}** apenas para pagar os R$ {custo_fixo:,.2f} de custo fixo.")
            
            # Barrinha visual
            progresso = min(100, int((margem_contribuicao/preco_unitario)*100))
            st.progress(progresso)
            st.caption(f"Cada produto contribui com R$ {margem_contribuicao:.2f} para pagar o aluguel.")
