
# PROJETO — esteira_analitica_end-to-end_dados_pncp_govbr

> PNCP (CSV bruto) → **Python** (auditoria + limpeza) → **PostgreSQL** (Star Schema) → **Power BI** (dashboard executivo)

## 1. Contexto do problema

A Controladoria precisa de clareza sobre sobrepreço, concentração de fornecedores, morosidade dos certames e competitividade por modalidade, mas os dados brutos do PNCP (2.042 contratações, 7.077 itens, 15.896 resultados) vêm com CNPJ corrompido, dinheiro em texto livre, datas em 7 formatos e nulos disfarçados. O Projeto **esteira_analitica_end-to-end_dados_pncp_govbr** transforma essa base em um ambiente confiável e auditável que responde 6 perguntas de negócio.
