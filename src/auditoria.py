"""
auditoria.py  -  SPRINT 1: AUDITAR OS DADOS BRUTOS (contar as sujeiras antes de limpar)
=======================================================================================
Lê os 3 CSVs como texto e conta, por coluna, cada tipo de problema. O resultado é impresso e
gravado em reports/auditoria.md: Os números obtidos serão usados no "dicionário de inconsistências" 
do README.MD.

COMO RODAR: Abra uma janela de terminal e execute o comando python -m src.auditoria
"""

import re

import pandas as pd

from src import config, limpeza

RE_MASCARA_DOC = re.compile(r"[^\d]")
RE_ACENTO_QUEBRADO = re.compile(r"Ã.|Â.")


def ler(nome):
    return pd.read_csv(config.PASTA_RAW / f"{nome}.csv", dtype=str, keep_default_na=False)


def formato_data(v):
    """Classifica o formato textual de uma data."""
    v = v.strip()
    if v == "":
        return "vazio"
    padroes = [(r"^\d{4}-\d{2}-\d{2}T", "AAAA-MM-DDThh:mm:ss"), (r"^\d{4}-\d{2}-\d{2}$", "AAAA-MM-DD"),
               (r"^\d{2}/\d{2}/\d{4} \d", "DD/MM/AAAA hh:mm"), (r"^\d{2}/\d{2}/\d{4}$", "DD/MM/AAAA"),
               (r"^\d{2}-\d{2}-\d{4}$", "DD-MM-AAAA"), (r"^\d{2}\.\d{2}\.\d{4}$", "DD.MM.AAAA"),
               (r"^\d{4}/\d{2}/\d{2}$", "AAAA/MM/DD"), (r"^\d{8}$", "AAAAMMDD")]
    for padrao, nome in padroes:
        if re.search(padrao, v):
            return nome
    return "outro"


def formato_dinheiro(v):
    v = v.strip()
    if v == "":
        return "vazio"
    if "R$" in v:
        return "com R$"
    if v.startswith("(") or v.endswith("-") or v.startswith("-"):
        return "negativo (parenteses/sinal)"
    if re.search(r"\d\.\d{3},\d", v):
        return "1.234,56 (BR)"
    if re.search(r"\d,\d{3}\.\d", v):
        return "1,234.56 (US)"
    if re.fullmatch(r"\d+,\d+", v):
        return "so virgula decimal"
    if re.fullmatch(r"\d+\.\d+", v):
        return "so ponto decimal"
    if re.fullmatch(r"\d+", v):
        return "inteiro"
    return "outro"


def main():
    compras, itens, resultados = ler("compras"), ler("itens"), ler("resultados")
    saida = []

    def titulo(t):
        saida.append(f"\n## {t}\n")

    def linha(t):
        saida.append(t)

    def tabela(serie, rotulo):
        linha(f"\n**{rotulo}**\n\n| valor | registros |\n|---|---|")
        for k, v in serie.value_counts().items():
            linha(f"| {k} | {v} |")

    titulo("1. Volume dos arquivos")
    linha(f"- compras.csv: {len(compras)} linhas | itens.csv: {len(itens)} linhas | resultados.csv: {len(resultados)} linhas")
    linha(f"- numero_controle_pncp repetido em compras: {compras['numero_controle_pncp'].duplicated().sum()}")
    linha(f"- itens repetidos (controle + item): {itens.duplicated(['numero_controle_pncp', 'numero_item']).sum()}")
    sem_pai = (~itens['numero_controle_pncp'].isin(compras['numero_controle_pncp'])).sum()
    linha(f"- itens sem compra correspondente: {sem_pai}")
    res_chave = resultados['numero_controle_pncp'] + '|' + resultados['numero_item']
    itens_chave = itens['numero_controle_pncp'] + '|' + itens['numero_item']
    linha(f"- resultados sem item correspondente: {(~res_chave.isin(itens_chave)).sum()}")
    linha(f"- itens com tem_resultado=True: {(itens['tem_resultado'].str.lower() == 'true').sum()}")
    linha(f"- resultados com data_cancelamento preenchida: {(resultados['data_cancelamento'].str.strip() != '').sum()}")
    n_res = resultados.groupby(['numero_controle_pncp', 'numero_item']).size()
    linha(f"- itens com mais de 1 resultado (SRP/credenciamento): {(n_res > 1).sum()}")

    titulo("2. Formatos de data")
    for arq, df, col in [("compras", compras, "data_publicacao"), ("resultados", resultados, "data_resultado"),
                         ("resultados", resultados, "data_cancelamento")]:
        tabela(df[col].map(formato_data), f"{arq}.{col}")
    datas_invalidas = resultados["data_resultado"].map(lambda v: v.strip() != "" and limpeza.converter_data(v) is None)
    linha(f"\n- resultados.data_resultado preenchida mas invalida/fora de 2000-2030: {datas_invalidas.sum()}")
    pub = compras.set_index("numero_controle_pncp")["data_publicacao"].map(limpeza.converter_data)
    hom = resultados["data_resultado"].map(limpeza.converter_data)
    pub_res = resultados["numero_controle_pncp"].map(pub)
    antes = [h is not None and p is not None and not pd.isna(h) and not pd.isna(p) and h < p for h, p in zip(hom, pub_res)]
    linha(f"- resultados com data_resultado ANTERIOR a publicacao (cronologia impossivel): {sum(antes)}")

    titulo("3. Formatos de dinheiro e numeros")
    for arq, df, cols in [("itens", itens, ["quantidade", "valor_unitario_estimado", "valor_total_estimado"]),
                          ("resultados", resultados, ["quantidade_homologada", "valor_unitario_homologado", "valor_total_homologado"])]:
        for col in cols:
            tabela(df[col].map(formato_dinheiro), f"{arq}.{col}")

    titulo("4. Documentos (CNPJ/CPF)")
    for arq, serie in [("compras.cnpj_orgao", compras["cnpj_orgao"]), ("resultados.ni_fornecedor", resultados["ni_fornecedor"])]:
        s = serie.str.strip()
        com_mascara = s.str.contains(r"[./-]", regex=True).sum()
        digitos = s.map(lambda v: RE_MASCARA_DOC.sub("", v))
        linha(f"- {arq}: com mascara={com_mascara} | vazios={(s == '').sum()} | lixo (N/A, -)={s.str.upper().isin(limpeza.NULOS).sum()}"
              f" | sem zero a esquerda (13 digitos)={(digitos.str.len() == 13).sum()} | 14 digitos={(digitos.str.len() == 14).sum()}")
    tabela(resultados["tipo_pessoa"], "resultados.tipo_pessoa")

    titulo("5. Nulos disfarcados por coluna de texto (N/A, NULL, -, 0, SEM INFORMACAO, NAO SE APLICA, vazio)")
    linha("| arquivo.coluna | nulos disfarcados | vazios |\n|---|---|---|")
    for arq, df in [("compras", compras), ("itens", itens), ("resultados", resultados)]:
        for col in df.columns:
            s = df[col].str.strip().str.upper()
            disfarcado = s.isin(limpeza.NULOS).sum()
            if disfarcado:
                linha(f"| {arq}.{col} | {disfarcado} | {(s == '').sum()} |")

    titulo("6. Encoding quebrado (Latin-1 lido como UTF-8: Ã§, Ã£...)")
    for arq, df in [("compras", compras), ("itens", itens), ("resultados", resultados)]:
        for col in df.columns:
            n = df[col].str.contains(RE_ACENTO_QUEBRADO).sum()
            if n:
                linha(f"- {arq}.{col}: {n} registros")

    titulo("7. Nomes inconsistentes")
    nomes = compras["razao_social_orgao"]
    padron = nomes.map(limpeza.padronizar_nome)
    linha(f"- razao_social_orgao: {nomes.nunique()} grafias distintas -> {padron.nunique()} nomes padronizados")
    linha(f"- cnpj_orgao distintos apos limpeza: {compras['cnpj_orgao'].map(lambda v: limpeza.limpar_documento(v, 'PJ')).nunique()}")
    nomes_f = resultados["nome_fornecedor"]
    linha(f"- nome_fornecedor: {nomes_f.nunique()} grafias distintas -> {nomes_f.map(limpeza.padronizar_nome).nunique()} padronizadas")
    linha(f"- modalidade_nome: {compras['modalidade_nome'].nunique()} grafias para {compras['modalidade_id'].nunique()} modalidade_id")
    tabela(itens["categoria_item"], "itens.categoria_item (nao ajuda, conforme enunciado)")
    tabela(itens["sigiloso"], "itens.sigiloso")

    texto = "# Auditoria dos dados brutos\n" + "\n".join(saida) + "\n"
    config.PASTA_REPORTS.mkdir(parents=True, exist_ok=True)
    (config.PASTA_REPORTS / "auditoria.md").write_text(texto, encoding="utf-8")
    print(texto)
    print("Gravado em reports/auditoria.md")


if __name__ == "__main__":
    main()