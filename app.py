import json
import os
from datetime import datetime
import streamlit as st

ARQUIVO_DADOS = "sistema_gamer.json"

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "caixa": 0.0,
        "investimentos": [],
        "estoque": [],
        "gastos_diarios": [],
        "historico_caixa": []
    }

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

dados = carregar_dados()

st.set_page_config(page_title="Gerenciador PC Gamer & Finanças", page_icon="💻", layout="wide")

st.sidebar.title("🎮 Menu Principal")
menu = st.sidebar.radio("Navegação", [
    "📊 Painel Geral", 
    "📦 Controle de Estoque", 
    "💰 Caixa", 
    "📈 Investimentos", 
    "🍔 Gastos Diários"
])

st.sidebar.markdown("---")
st.sidebar.metric(label="💰 Caixa Atual", value=f"R$ {dados['caixa']:.2f}")

if menu == "📊 Painel Geral":
    st.title("📊 Painel Geral de Controle - Loja PC Gamer")
    
    saldo_caixa = dados["caixa"]
    total_investido = sum(i["valor"] for i in dados["investimentos"])
    total_gastos = sum(g["valor"] for g in dados["gastos_diarios"])
    custo_estoque = sum(p["qtd"] * p["custo"] for p in dados["estoque"])
    venda_estoque = sum(p["qtd"] * p["venda"] for p in dados["estoque"])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Saldo em Caixa", f"R$ {saldo_caixa:.2f}")
    col2.metric("Estoque (Custo)", f"R$ {custo_estoque:.2f}")
    col3.metric("Estoque (Venda)", f"R$ {venda_estoque:.2f}")
    
    col4, col5 = st.columns(2)
    col4.metric("Total Investido", f"R$ {total_investido:.2f}")
    col5.metric("Gastos Pessoais", f"R$ {total_gastos:.2f}")

elif menu == "📦 Controle de Estoque":
    st.title("📦 Controle de Estoque de Peças")
    
    tab1, tab2, tab3 = st.tabs(["📋 Listar Peças", "➕ Cadastrar Peça", "🛒 Vender / Baixa"])
    
    with tab1:
        st.subheader("Peças no Estoque")
        if not dados["estoque"]:
            st.info("Nenhuma peça cadastrada.")
        else:
            st.dataframe(dados["estoque"], use_container_width=True)
            
    with tab2:
        st.subheader("Cadastrar Nova Peça")
        with st.form("form_peca"):
            nome = st.text_input("Nome da Peça (ex: RTX 4060)")
            categoria = st.text_input("Categoria (GPU, CPU, RAM...)")
            qtd = st.number_input("Quantidade", min_value=1, step=1)
            custo = st.number_input("Preço de Custo Unitário (R$)", min_value=0.0, format="%.2f")
            venda = st.number_input("Preço de Venda Unitário (R$)", min_value=0.0, format="%.2f")
            
            submitted = st.form_submit_button("Cadastrar Peça")
            if submitted and nome:
                dados["estoque"].append({
                    "nome": nome,
                    "categoria": categoria,
                    "qtd": int(qtd),
                    "custo": float(custo),
                    "venda": float(venda)
                })
                salvar_dados(dados)
                st.success("Peça cadastrada com sucesso!")
                st.rerun()
                
    with tab3:
        st.subheader("Vender Peça")
        if not dados["estoque"]:
            st.info("Estoque vazio.")
        else:
            nomes_pecas = [p['nome'] for p in dados["estoque"]]
            escolha_peca = st.selectbox("Selecione a Peça", nomes_pecas)
            peca_obj = next(p for p in dados["estoque"] if p['nome'] == escolha_peca)
            
            qtd_venda = st.number_input("Quantidade Vendida", min_value=1, max_value=peca_obj["qtd"], step=1)
            if st.button("Confirmar Venda"):
                peca_obj["qtd"] -= int(qtd_venda)
                valor_total = int(qtd_venda) * peca_obj["venda"]
                dados["caixa"] += valor_total
                
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                dados["historico_caixa"].append({
                    "data": data_atual,
                    "tipo": "ENTRADA (Venda de Peça)",
                    "descricao": f"Venda de {qtd_venda}x {peca_obj['nome']}",
                    "valor": valor_total
                })
                salvar_dados(dados)
                st.success(f"Venda realizada! R$ {valor_total:.2f} adicionados ao caixa.")
                st.rerun()

elif menu == "💰 Caixa":
    st.title("💰 Controle de Caixa (Entradas e Saídas)")
    
    tab1, tab2, tab3 = st.tabs(["➕ Nova Entrada", "➖ Nova Saída", "📜 Histórico"])
    
    with tab1:
        with st.form("form_entrada"):
            val_ent = st.number_input("Valor da Entrada (R$)", min_value=0.0, format="%.2f")
            desc_ent = st.text_input("Descrição")
            if st.form_submit_button("Adicionar Entrada") and val_ent > 0:
                dados["caixa"] += val_ent
                dados["historico_caixa"].append({
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "tipo": "ENTRADA MANUAL",
                    "descricao": desc_ent,
                    "valor": val_ent
                })
                salvar_dados(dados)
                st.success("Entrada registrada!")
                st.rerun()
                
    with tab2:
        with st.form("form_saida"):
            val_sai = st.number_input("Valor da Saída (R$)", min_value=0.0, format="%.2f")
            desc_sai = st.text_input("Descrição / Pagamento")
            if st.form_submit_button("Registrar Saída") and val_sai > 0:
                dados["caixa"] -= val_sai
                dados["historico_caixa"].append({
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "tipo": "SAÍDA",
                    "descricao": desc_sai,
                    "valor": val_sai
                })
                salvar_dados(dados)
                st.success("Saída registrada!")
                st.rerun()
                
    with tab3:
        if not dados["historico_caixa"]:
            st.info("Nenhuma movimentação.")
        else:
            st.dataframe(dados["historico_caixa"], use_container_width=True)

elif menu == "📈 Investimentos":
    st.title("📈 Controle de Investimentos")
    
    total_inv = sum(i['valor'] for i in dados["investimentos"])
    st.metric("Total Investido", f"R$ {total_inv:.2f}")
    
    tab1, tab2 = st.tabs(["📋 Listar Investimentos", "➕ Novo Investimento"])
    
    with tab1:
        if not dados["investimentos"]:
            st.info("Nenhum investimento cadastrado.")
        else:
            st.dataframe(dados["investimentos"], use_container_width=True)
            
    with tab2:
        with st.form("form_inv"):
            ativo = st.text_input("Ativo (ex: Tesouro, Ações, Cripto)")
            tipo_inv = st.text_input("Tipo (Renda Fixa, Variável...)")
            val_inv = st.number_input("Valor Investido (R$)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Registrar Investimento") and val_inv > 0:
                dados["caixa"] -= val_inv
                dados["historico_caixa"].append({
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "tipo": "SAÍDA (Investimento)",
                    "descricao": f"Aporte em {ativo}",
                    "valor": val_inv
                })
                dados["investimentos"].append({
                    "ativo": ativo,
                    "tipo": tipo_inv,
                    "valor": val_inv,
                    "data": datetime.now().strftime("%d/%m/%Y")
                })
                salvar_dados(dados)
                st.success("Investimento registrado e debitado do caixa!")
                st.rerun()

elif menu == "🍔 Gastos Diários":
    st.title("🍔 Gastos do Dia a Dia (Lazer, Comida, Gasolina)")
    
    total_g = sum(g['valor'] for g in dados["gastos_diarios"])
    st.metric("Total de Gastos", f"R$ {total_g:.2f}")
    
    tab1, tab2 = st.tabs(["📋 Listar Gastos", "➕ Adicionar Gasto"])
    
    with tab1:
        if not dados["gastos_diarios"]:
            st.info("Nenhum gasto registrado.")
        else:
            st.dataframe(dados["gastos_diarios"], use_container_width=True)
            
    with tab2:
        with st.form("form_gasto"):
            cat = st.selectbox("Categoria", ["Comida", "Gasolina", "Lazer", "Contas/Casa", "Outros"])
            desc_g = st.text_input("Descrição (ex: Almoço, Posto)")
            val_g = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Adicionar Gasto") and val_g > 0:
                dados["caixa"] -= val_g
                dados["historico_caixa"].append({
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "tipo": f"SAÍDA ({cat})",
                    "descricao": desc_g,
                    "valor": val_g
                })
                dados["gastos_diarios"].append({
                    "data": datetime.now().strftime("%d/%m/%Y"),
                    "categoria": cat,
                    "descricao": desc_g,
                    "valor": val_g
                })
                salvar_dados(dados)
                st.success("Gasto registrado com sucesso!")
                st.rerun()