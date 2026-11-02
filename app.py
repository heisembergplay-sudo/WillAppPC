from datetime import datetime
import json
import os
import pandas as pd
import streamlit as st

ARQUIVO_DADOS = "sistema_gamer.json"


def carregar_dados():
  if os.path.exists(ARQUIVO_DADOS):
    try:
      with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        dados = json.load(f)
        if "montagens_pcs" not in dados:
          dados["montagens_pcs"] = []
        return dados
    except Exception:
      pass
  return {
      "caixa": 0.0,
      "investimentos": [],
      "estoque": [],
      "gastos_diarios": [],
      "historico_caixa": [],
      "montagens_pcs": [],
  }


def salvar_dados(dados):
  with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=4)


dados = carregar_dados()

st.set_page_config(
    page_title="Gerenciador PC Gamer & Finanças Pro", page_icon="💻", layout="wide"
)

st.sidebar.title("🎮 Menu Principal")
menu = st.sidebar.radio(
    "Navegação",
    [
        "📊 Painel Geral",
        "📦 Controle de Estoque",
        "🖥️ Montagem de PCs",
        "💰 Caixa & Gráficos",
        "📈 Investimentos",
        "🍔 Gastos Diários",
        "⚙️ Dados & Backup",
    ],
)

st.sidebar.markdown("---")
st.sidebar.metric(label="💰 Caixa Atual", value=f"R$ {dados['caixa']:.2f}")

# ==================== 1. PAINEL GERAL ====================
if menu == "📊 Painel Geral":
  st.title("📊 Painel Geral de Controle - Loja & Finanças")

  saldo_caixa = dados["caixa"]
  total_investido = sum(i["valor"] for i in dados["investimentos"])
  total_gastos = sum(g["valor"] for g in dados["gastos_diarios"])
  custo_estoque = sum(p["qtd"] * p["custo"] for p in dados["estoque"])
  venda_estoque = sum(p["qtd"] * p["venda"] for p in dados["estoque"])
  lucro_potencial = venda_estoque - custo_estoque

  col1, col2, col3, col4 = st.columns(4)
  col1.metric("Saldo em Caixa", f"R$ {saldo_caixa:.2f}")
  col2.metric("Estoque (Custo)", f"R$ {custo_estoque:.2f}")
  col3.metric("Estoque (Venda)", f"R$ {venda_estoque:.2f}")
  col4.metric("Lucro Estimado", f"R$ {lucro_potencial:.2f}")

  col5, col6 = st.columns(2)
  col5.metric("Total Investido", f"R$ {total_investido:.2f}")
  col6.metric("Gastos Pessoais", f"R$ {total_gastos:.2f}")

  st.markdown("---")
  st.subheader("📈 Visão Rápida dos Gastos por Categoria")
  if dados["gastos_diarios"]:
    df_gastos = pd.DataFrame(dados["gastos_diarios"])
    gastos_cat = df_gastos.groupby("categoria")["valor"].sum()
    st.bar_chart(gastos_cat)
  else:
    st.info("Cadastre gastos diários para visualizar o gráfico de categorias.")

# ==================== 2. CONTROLE DE ESTOQUE ====================
elif menu == "📦 Controle de Estoque":
  st.title("📦 Controle de Estoque de Peças")

  tab1, tab2, tab3 = st.tabs(
      ["📋 Listar / Excluir Peças", "➕ Cadastrar Peça", "🛒 Vender / Baixa"]
  )

  with tab1:
    st.subheader("Peças no Estoque")
    if not dados["estoque"]:
      st.info("Nenhuma peça cadastrada.")
    else:
      nomes_pecas = [p["nome"] for p in dados["estoque"]]
      peca_para_excluir = st.selectbox(
          "Selecione uma peça para remover do estoque",
          ["-- Selecione --"] + nomes_pecas,
      )

      if peca_para_excluir != "-- Selecione --":
        if st.button("🗑️ Excluir Peça Selecionada", type="primary"):
          dados["estoque"] = [
              p for p in dados["estoque"] if p["nome"] != peca_para_excluir
          ]
          salvar_dados(dados)
          st.success(f"Peça '{peca_para_excluir}' removida com sucesso!")
          st.rerun()

      st.markdown("---")
      st.dataframe(dados["estoque"], use_container_width=True)

  with tab2:
    st.subheader("Cadastrar Nova Peça")
    with st.form("form_peca"):
      nome = st.text_input("Nome da Peça (ex: RTX 4060)")
      categoria = st.text_input("Categoria (GPU, CPU, RAM...)")
      qtd = st.number_input("Quantidade", min_value=1, step=1)
      custo = st.number_input(
          "Preço de Custo Unitário (R$)", min_value=0.0, format="%.2f"
      )
      venda = st.number_input(
          "Preço de Venda Unitário (R$)", min_value=0.0, format="%.2f"
      )

      submitted = st.form_submit_button("Cadastrar Peça")
      if submitted and nome:
        dados["estoque"].append({
            "nome": nome,
            "categoria": categoria,
            "qtd": int(qtd),
            "custo": float(custo),
            "venda": float(venda),
        })
        salvar_dados(dados)
        st.success("Peça cadastrada com sucesso!")
        st.rerun()

  with tab3:
    st.subheader("Vender Peça Avulsa")
    if not dados["estoque"]:
      st.info("Estoque vazio.")
    else:
      nomes_pecas = [p["nome"] for p in dados["estoque"]]
      escolha_peca = st.selectbox("Selecione a Peça", nomes_pecas)
      peca_obj = next(p for p in dados["estoque"] if p["nome"] == escolha_peca)

      qtd_venda = st.number_input(
          "Quantidade Vendida",
          min_value=1,
          max_value=peca_obj["qtd"],
          step=1,
      )
      if st.button("Confirmar Venda"):
        peca_obj["qtd"] -= int(qtd_venda)
        valor_total = int(qtd_venda) * peca_obj["venda"]
        dados["caixa"] += valor_total

        dados["historico_caixa"].append({
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "tipo": "ENTRADA (Venda de Peça)",
            "descricao": f"Venda de {qtd_venda}x {peca_obj['nome']}",
            "valor": valor_total,
        })
        salvar_dados(dados)
        st.success(
            f"Venda realizada! R$ {valor_total:.2f} adicionados ao caixa."
        )
        st.rerun()

# ==================== 3. MONTAGEM DE PCS ====================
elif menu == "🖥️ Montagem de PCs":
  st.title("🖥️ Gestão de PCs Montados para Venda")
  st.markdown(
      "Cadastre os computadores inteiros que você montou para revender (com"
      " suas respectivas configs e preços)."
  )

  tab1, tab2 = st.tabs(["📋 Meus PCs Montados", "➕ Novo PC Montado"])

  with tab1:
    if not dados["montagens_pcs"]:
      st.info("Nenhum PC cadastrado para venda.")
    else:
      pcs_lista = [pc["nome_pc"] for pc in dados["montagens_pcs"]]
      pc_escolhido = st.selectbox(
          "Selecione um PC para gerenciar/vender", ["-- Selecione --"] + pcs_lista
      )

      if pc_escolhido != "-- Selecione --":
        pc_obj = next(
            p for p in dados["montagens_pcs"] if p["nome_pc"] == pc_escolhido
        )
        st.write(f"**Especificações:** {pc_obj['specs']}")
        st.
