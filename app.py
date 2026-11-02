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
        # Garante que novas chaves existam se o JSON for antigo
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
        st.write(f"**Custo Total:** R$ {pc_obj['custo']:.2f}")
        st.write(f"**Preço de Venda:** R$ {pc_obj['venda']:.2f}")
        st.write(f"**Lucro Previsto:** R$ {pc_obj['venda'] - pc_obj['custo']:.2f}")

        col_v, col_e = st.columns(2)
        with col_v:
          if st.button("💰 Vender este PC"):
            dados["caixa"] += pc_obj["venda"]
            dados["historico_caixa"].append({
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "tipo": "ENTRADA (Venda de PC)",
                "descricao": f"Venda do PC: {pc_obj['nome_pc']}",
                "valor": pc_obj["venda"],
            })
            dados["montagens_pcs"] = [
                p
                for p in dados["montagens_pcs"]
                if p["nome_pc"] != pc_escolhido
            ]
            salvar_dados(dados)
            st.success("PC vendido e valor adicionado ao caixa!")
            st.rerun()
        with col_e:
          if st.button("🗑️ Excluir Registro do PC"):
            dados["montagens_pcs"] = [
                p
                for p in dados["montagens_pcs"]
                if p["nome_pc"] != pc_escolhido
            ]
            salvar_dados(dados)
            st.success("Registro removido!")
            st.rerun()

      st.markdown("---")
      st.dataframe(dados["montagens_pcs"], use_container_width=True)

  with tab2:
    with st.form("form_pc"):
      nome_pc = st.text_input(
          "Nome do Setup (ex: PC Gamer Ryzen 5 + RTX 3060)"
      )
      specs = st.text_area(
          "Especificações (Processador, Placa Mãe, Memória, SSD, Fonte...)"
      )
      custo_pc = st.number_input(
          "Custo Total das Peças (R$)", min_value=0.0, format="%.2f"
      )
      venda_pc = st.number_input(
          "Preço de Venda Anunciado (R$)", min_value=0.0, format="%.2f"
      )

      if st.form_submit_button("Cadastrar PC para Venda") and nome_pc:
        dados["montagens_pcs"].append({
            "nome_pc": nome_pc,
            "specs": specs,
            "custo": float(custo_pc),
            "venda": float(venda_pc),
            "data": datetime.now().strftime("%d/%m/%Y"),
        })
        salvar_dados(dados)
        st.success("PC cadastrado com sucesso!")
        st.rerun()

# ==================== 4. CAIXA & GRÁFICOS ====================
elif menu == "💰 Caixa & Gráficos":
  st.title("💰 Controle de Caixa e Gráficos Financeiros")

  tab1, tab2, tab3 = st.tabs(
      ["➕ Entradas/Saídas", "📜 Histórico", "📊 Gráficos de Movimentação"]
  )

  with tab1:
    col_e, col_s = st.columns(2)
    with col_e:
      st.subheader("Nova Entrada Manual")
      with st.form("form_entrada"):
        val_ent = st.number_input(
            "Valor da Entrada (R$)", min_value=0.0, format="%.2f"
        )
        desc_ent = st.text_input("Descrição da Entrada")
        if st.form_submit_button("Adicionar Entrada") and val_ent > 0:
          dados["caixa"] += val_ent
          dados["historico_caixa"].append({
              "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
              "tipo": "ENTRADA MANUAL",
              "descricao": desc_ent,
              "valor": val_ent,
          })
          salvar_dados(dados)
          st.success("Entrada registrada!")
          st.rerun()

    with col_s:
      st.subheader("Nova Saída / Despesa")
      with st.form("form_saida"):
        val_sai = st.number_input(
            "Valor da Saída (R$)", min_value=0.0, format="%.2f"
        )
        desc_sai = st.text_input("Descrição / Pagamento")
        if st.form_submit_button("Registrar Saída") and val_sai > 0:
          dados["caixa"] -= val_sai
          dados["historico_caixa"].append({
              "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
              "tipo": "SAÍDA",
              "descricao": desc_sai,
              "valor": val_sai,
          })
          salvar_dados(dados)
          st.success("Saída registrada!")
          st.rerun()

  with tab2:
    st.subheader("Histórico Completo")
    if not dados["historico_caixa"]:
      st.info("Nenhuma movimentação.")
    else:
      if st.button("🗑️ Limpar Todo o Histórico", type="secondary"):
        dados["historico_caixa"] = []
        salvar_dados(dados)
        st.success("Histórico limpo!")
        st.rerun()
      st.dataframe(dados["historico_caixa"], use_container_width=True)

  with tab3:
    st.subheader("Gráficos de Entradas e Saídas")
    if dados["historico_caixa"]:
      df_hist = pd.DataFrame(dados["historico_caixa"])
      st.bar_chart(df_hist.set_index("data")["valor"])
    else:
      st.info("Sem dados suficientes para gerar gráficos.")

# ==================== 5. INVESTIMENTOS ====================
elif menu == "📈 Investimentos":
  st.title("📈 Controle de Investimentos")

  total_inv = sum(i["valor"] for i in dados["investimentos"])
  st.metric("Total Investido", f"R$ {total_inv:.2f}")

  tab1, tab2 = st.tabs(
      ["📋 Listar / Excluir Investimentos", "➕ Novo Investimento"]
  )

  with tab1:
    if not dados["investimentos"]:
      st.info("Nenhum investimento cadastrado.")
    else:
      ativos_lista = [i["ativo"] for i in dados["investimentos"]]
      inv_para_excluir = st.selectbox(
          "Selecione o investimento para remover",
          ["-- Selecione --"] + ativos_lista,
      )

      if inv_para_excluir != "-- Selecione --":
        if st.button("🗑️ Excluir Investimento Selecionado", type="primary"):
          dados["investimentos"] = [
              i for i in dados["investimentos"] if i["ativo"] != inv_para_excluir
          ]
          salvar_dados(dados)
          st.success("Investimento removido com sucesso!")
          st.rerun()

      st.markdown("---")
      st.dataframe(dados["investimentos"], use_container_width=True)

  with tab2:
    with st.form("form_inv"):
      ativo = st.text_input("Ativo (ex: Tesouro, Ações, Cripto)")
      tipo_inv = st.text_input("Tipo (Renda Fixa, Variável...)")
      val_inv = st.number_input(
          "Valor Investido (R$)", min_value=0.0, format="%.2f"
      )
      if st.form_submit_button("Registrar Investimento") and val_inv > 0:
        dados["caixa"] -= val_inv
        dados["historico_caixa"].append({
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "tipo": "SAÍDA (Investimento)",
            "descricao": f"Aporte em {ativo}",
            "valor": val_inv,
        })
        dados["investimentos"].append({
            "ativo": ativo,
            "tipo": tipo_inv,
            "valor": val_inv,
            "data": datetime.now().strftime("%d/%m/%Y"),
        })
        salvar_dados(dados)
        st.success("Investimento registrado e debitado do caixa!")
        st.rerun()

# ==================== 6. GASTOS DIÁRIOS ====================
elif menu == "🍔 Gastos Diários":
  st.title("🍔 Gastos do Dia a Dia (Lazer, Comida, Gasolina)")

  total_g = sum(g["valor"] for g in dados["gastos_diarios"])
  st.metric("Total de Gastos", f"R$ {total_g:.2f}")

  tab1, tab2 = st.tabs(["📋 Listar / Excluir Gastos", "➕ Adicionar Gasto"])

  with tab1:
    if not dados["gastos_diarios"]:
      st.info("Nenhum gasto registrado.")
    else:
      descricoes_gastos = [
          f"{g['data']} - {g['categoria']}: {g['descricao']} (R$ {g['valor']:.2f})"
          for g in dados["gastos_diarios"]
      ]
      gasto_escolhido = st.selectbox(
          "Selecione o gasto que deseja remover",
          ["-- Selecione --"] + descricoes_gastos,
      )

      if gasto_escolhido != "-- Selecione --":
        if st.button("🗑️ Excluir Gasto Selecionado", type="primary"):
          indice = descricoes_gastos.index(gasto_escolhido)
          removido = dados["gastos_diarios"].pop(indice)
          salvar_dados(dados)
          st.success(f"Gasto '{removido['descricao']}' excluído com sucesso!")
          st.rerun()

      st.markdown("---")
      st.dataframe(dados["gastos_diarios"], use_container_width=True)

  with tab2:
    with st.form("form_gasto"):
      cat = st.selectbox(
          "Categoria", ["Comida", "Gasolina", "Lazer", "Contas/Casa", "Outros"]
      )
      desc_g = st.text_input("Descrição (ex: Almoço, Posto)")
      val_g = st.number_
