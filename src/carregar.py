"""
carregar.py  -  CARGA NO POSTGRESQL
=========================================================================
Passos:  1) VALIDACAO PREVIA dos arquivos de data/processed (antes de tocar no banco)
         2) recria o banco e as tabelas (banco.recriar_banco + sql/01_criar_banco.sql)
         3) carrega as 4 DIMENSOES   4) carrega a FATO (as dimensoes vem primeiro!)
         5) confere as contagens e a integridade (nenhum item da fato ligado a linha de excecao sk = -1)
         6) COMMIT se tudo estiver certo; qualquer erro => ROLLBACK (tudo ou nada)
Usa so o que o kit ja traz: src/config.py e src/banco.py (recriar_banco, conectar, executar_script, inserir_em_lote, consultar).
O sql/01_criar_banco.sql so cria as tabelas: o banco em si e recriado por banco.recriar_banco().

TRATAMENTO DE FALHAS (o que muda em relacao a uma carga "linha a linha"):
  - validar_arquivos(): acha problemas ANTES de gravar (chave duplicada, FK sem destino, valor que o CHECK recusaria).
  - Uma unica transacao: DDL + dimensoes + fato + conferencia. O PostgreSQL desfaz ate o CREATE TABLE no rollback.
  - try/except/finally: se algo falha, con.rollback() e uma mensagem clara; o banco fica vazio, nunca meio carregado.

COMO RODAR (depois do montar_tabelas):   python -m src.carregar
"""

import pandas as pd

from src import banco, config


class ErroDeCarga(Exception):
    """Erro de validacao ou de conferencia: interrompe a carga e dispara o rollback."""


# Contagens da prova real (anexo 8 do enunciado). A linha de excecao (sk = -1) nao entra na conta.
ESPERADO = {"fato_item_contratado": 6126, "dim_orgao": 363, "dim_fornecedor": 2652,
            "dim_modalidade": 7, "dim_localidade": 27}
SK = {"dim_orgao": "sk_orgao", "dim_fornecedor": "sk_fornecedor", "dim_modalidade": "sk_modalidade",
      "dim_localidade": "sk_localidade"}

# (tabela, colunas): a ordem importa. A 1a coluna e a chave substituta (sk) e a 2a, a chave natural (UNIQUE).
DIMENSOES = [("dim_orgao", ["sk_orgao", "cnpj_orgao", "nome_orgao", "poder"]),
             ("dim_fornecedor", ["sk_fornecedor", "ni_fornecedor", "nome_fornecedor", "tipo_pessoa", "porte"]),
             ("dim_modalidade", ["sk_modalidade", "modalidade_id", "nome_modalidade"]),
             ("dim_localidade", ["sk_localidade", "uf_sigla", "uf_nome", "regiao"])]
COLUNAS_FATO = ["numero_controle_pncp", "numero_item", "sk_orgao", "sk_fornecedor", "sk_modalidade", "sk_localidade",
                "data_publicacao", "data_homologacao", "descricao_item", "perfil_gasto", "quantidade",
                "valor_unitario_estimado", "valor_total_estimado", "valor_unitario_homologado", "valor_total_homologado",
                "comparavel", "economia_valor", "dias_ciclo"]


def ler(nome, **opcoes):
    """PRONTA. Le um CSV de data/processed. Campo vazio vira NaN (que mais abaixo vira None = NULL no banco)."""
    return pd.read_csv(config.PASTA_PROCESSED / f"{nome}.csv", keep_default_na=False, na_values=[""], **opcoes)


def tuplas(tabela, colunas):
    """PRONTA. Transforma o DataFrame em uma lista de tuplas simples, que e o que o banco entende.
    Valor vazio (NaN) vira None, que o banco grava como NULL."""
    dados = tabela[colunas].astype(object)
    dados = dados.where(dados.notna(), None)
    return [tuple(linha) for linha in dados.itertuples(index=False, name=None)]


def inserir(con, tabela, colunas, dados):
    """Monta o INSERT INTO ... VALUES (%s, %s, ...) e envia todas as linhas de uma vez.
    confirmar=False: nao faz commit aqui; o commit (ou o rollback) acontece uma vez so, no main()."""
    marcadores = ", ".join(["%s"] * len(colunas))
    sql = f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({marcadores})"
    banco.inserir_em_lote(con, sql, tuplas(dados, colunas), confirmar=False)
    print(f"   {tabela}: {len(dados)} linhas")


# ---------------------------------------------------------------------------------------------
# 1) VALIDACAO PREVIA  (roda ANTES de qualquer comando no banco)
# ---------------------------------------------------------------------------------------------
def validar_arquivos():
    """Confere os CSVs de data/processed. Junta TODOS os problemas e, se houver algum, levanta ErroDeCarga.
    Cada teste abaixo repete, em Python, o que o banco faria depois (PK, UNIQUE, FK e CHECK): assim o erro
    aparece antes de gravar, com uma mensagem que diz o que e onde. O banco continua sendo a 2a barreira."""
    erros, dados = [], {}

    # --- dimensoes: colunas, chave substituta unica, chave natural unica e sem vazio, contagem da prova real
    for nome, colunas in DIMENSOES:
        tabela = ler(nome, dtype=str)                       # dtype=str: o CNPJ nao pode perder o zero da esquerda
        faltam = [c for c in colunas if c not in tabela.columns]
        if faltam:
            erros.append(f"{nome}: faltam as colunas {faltam}")
            continue
        sk, natural = colunas[0], colunas[1]
        if tabela[sk].duplicated().any():
            erros.append(f"{nome}: chave substituta {sk} repetida")
        if tabela[natural].isna().any() or tabela[natural].duplicated().any():
            erros.append(f"{nome}: chave natural {natural} vazia ou repetida")
        if len(tabela) != ESPERADO[nome]:
            erros.append(f"{nome}: {len(tabela)} linhas (esperado {ESPERADO[nome]})")
        dados[nome] = tabela

    # --- fato
    fato = ler("fato_item_contratado")
    faltam = [c for c in COLUNAS_FATO if c not in fato.columns]
    if faltam:
        erros.append(f"fato_item_contratado: faltam as colunas {faltam}")
    else:
        if len(fato) != ESPERADO["fato_item_contratado"]:
            erros.append(f"fato_item_contratado: {len(fato)} linhas (esperado {ESPERADO['fato_item_contratado']})")
        if fato.duplicated(["numero_controle_pncp", "numero_item"]).any():
            erros.append("fato_item_contratado: item repetido (numero_controle_pncp + numero_item)")
        # FK: toda chave da fato precisa existir na dimensao (senao o banco recusaria a linha)
        for dim, sk in SK.items():
            if dim not in dados:
                continue
            if fato[sk].isna().any():
                erros.append(f"fato_item_contratado: {sk} vazio")
                continue
            orfas = ~fato[sk].astype(str).isin(dados[dim][sk])
            if orfas.any():
                erros.append(f"fato_item_contratado: {int(orfas.sum())} linha(s) com {sk} que nao existe em {dim}")
        # CHECK: as mesmas regras do 01_criar_banco.sql
        if not (fato["quantidade"] > 0).all():
            erros.append("fato_item_contratado: quantidade vazia ou <= 0")
        for coluna in ["valor_unitario_estimado", "valor_total_estimado",
                       "valor_unitario_homologado", "valor_total_homologado"]:
            if not (fato[coluna] >= 0).all():
                erros.append(f"fato_item_contratado: {coluna} vazio ou negativo")
        if not fato["comparavel"].isin([0, 1]).all():
            erros.append("fato_item_contratado: comparavel fora de 0/1")
        if not fato["perfil_gasto"].isin(["Bens", "Serviços", "Obras e engenharia"]).all():
            erros.append("fato_item_contratado: perfil_gasto invalido")
        if (fato["dias_ciclo"] < 0).any():
            erros.append("fato_item_contratado: dias_ciclo negativo")
        if (fato["dias_ciclo"].notna() & fato["data_homologacao"].isna()).any():
            erros.append("fato_item_contratado: dias_ciclo sem data_homologacao")
    dados["fato_item_contratado"] = fato

    if erros:
        raise ErroDeCarga("validacao previa encontrou " + str(len(erros)) + " problema(s):\n   - " + "\n   - ".join(erros))
    print("Validacao previa: OK (chaves unicas, FK com destino, regras do CHECK, contagens da prova real)")
    return dados


# ---------------------------------------------------------------------------------------------
# 5) CONFERENCIA  (roda DENTRO da transacao: se divergir, o main() faz rollback)
# ---------------------------------------------------------------------------------------------
def conferir(con):
    """O que esta no banco tem que bater com a prova real (anexo 8). Divergencia => ErroDeCarga => rollback."""
    problemas = []
    print("Conferencia:")
    for tabela, esperado in ESPERADO.items():
        sk = SK.get(tabela)
        filtro = f" WHERE {sk} <> -1" if sk else ""        # a linha sk = -1 nao conta (secao 4.3 do enunciado)
        n = banco.consultar(con, f"SELECT COUNT(*) FROM {tabela}{filtro}")[0][0]
        print(f"   {tabela}: {n} (esperado {esperado}) -> {'OK' if n == esperado else 'DIVERGENTE'}")
        if n != esperado:
            problemas.append(f"{tabela}: {n} linhas no banco (esperado {esperado})")
    # Integridade: itens da fato ligados a linha de excecao (-1). Esperado: 0 (nenhuma FK solta).
    n = banco.consultar(con, """SELECT COUNT(*) FROM fato_item_contratado
                                WHERE sk_orgao = -1 OR sk_fornecedor = -1
                                   OR sk_modalidade = -1 OR sk_localidade = -1""")[0][0]
    print(f"   itens da fato ligados a 'Nao informado': {n} -> {'OK' if n == 0 else 'ATENCAO'}")
    if n != 0:
        problemas.append(f"{n} item(ns) da fato ligados a 'Nao informado' (sk = -1)")
    if problemas:
        raise ErroDeCarga("conferencia divergente: " + "; ".join(problemas))


def main():
    # 1) VALIDACAO PREVIA: se falhar, nem chega a mexer no banco
    try:
        dados = validar_arquivos()
    except ErroDeCarga as erro:
        print(f"\nERRO: {erro}\nNada foi gravado no banco.")
        raise SystemExit(1)

    # 2) Banco novo (o recriar_banco apaga e cria de novo; CREATE DATABASE nao pode ficar dentro de transacao)
    banco.recriar_banco()
    con = banco.conectar()          # psycopg2: a transacao comeca no 1o comando e so termina no commit/rollback
    try:
        # 3) Tabelas, dimensoes PRIMEIRO (a fato tem FK para elas) e fato: tudo na MESMA transacao
        banco.executar_script(con, config.PASTA_SQL / "01_criar_banco.sql", confirmar=False)
        print("Carga:")
        for nome, colunas in DIMENSOES:
            inserir(con, nome, colunas, dados[nome])
        fato = dados["fato_item_contratado"]
        fato["dias_ciclo"] = fato["dias_ciclo"].astype("Int64")   # tem vazios (decimal 48.0); o banco quer inteiro
        inserir(con, "fato_item_contratado", COLUNAS_FATO, fato)
        # 4) Conferencia dentro da transacao
        conferir(con)
        # 5) Tudo certo: confirma de uma vez
        con.commit()
        print("\nCarga confirmada: COMMIT.")
    except Exception as erro:       # erro do banco (FK, CHECK, UNIQUE, conexao) ou ErroDeCarga da conferencia
        con.rollback()              # desfaz TUDO: ate os CREATE TABLE (no PostgreSQL o DDL tambem e transacional)
        print(f"\nERRO NA CARGA: {erro}\nROLLBACK executado: nada foi gravado (o banco fica vazio, nunca meio carregado).")
        raise SystemExit(1)
    finally:
        con.close()


if __name__ == "__main__":
    main()
