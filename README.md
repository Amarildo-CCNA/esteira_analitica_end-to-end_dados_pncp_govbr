# PROJETO — esteira_analitica_end-to-end_dados_pncp_govbr

> PNCP (CSV bruto) → **Python** (auditoria + limpeza) → **PostgreSQL** (Star Schema) → **Power BI** (dashboard executivo)

## 1. Contexto do problema

A Controladoria precisa de clareza sobre sobrepreço, concentração de fornecedores, morosidade dos certames e competitividade por modalidade, mas os dados brutos do PNCP (2.042 contratações, 7.077 itens, 15.896 resultados) vêm com CNPJ corrompido, dinheiro em texto livre, datas em 7 formatos e nulos disfarçados. O Projeto **esteira_analitica_end-to-end_dados_pncp_govbr** transforma essa base em um ambiente confiável e auditável que responde 6 perguntas de negócio.


## 2. Estrutura do repositório

```
esteira_analitica_end-to-end_dados_pncp_govbr/
├── data/raw/          CSVs brutos (compras, itens, resultados)
├── data/processed/    tabelas limpas geradas pelo Python (fato + 4 dimensões)
├── docs/              medidas_dax.md · img/ (sprints.png, prints do modelo e do dashboard)
├── src/               config, banco, limpeza, auditoria, montar_tabelas, carregar
├── sql/               01_criar_banco.sql · 02_perguntas.sql
├── powerbi/           arquivo .pbix
└── reports/           auditoria.md
```


## 🔍3 Dicionário de Inconsistências (Resultados da Auditoria)

Após executar o pipeline de auditoria na base bruta do PNCP (ano 2025), foram identificadas e quantificadas as seguintes anomalias estruturais:

### 3.1. Documentos e Identificadores (CNPJ/CPF)

* **Problema:** Perda de zeros à esquerda devido à conversão incorreta de tipos e presença de máscaras (`.`, `-`, `/`).
* **Volume afetado:**

- compras.cnpj_orgao: com mascara=176 | vazios=0 | lixo (N/A, -)=0 | sem zero a esquerda (13 digitos)=10 | 14 digitos=1965

- resultados.ni_fornecedor: com mascara=1633 | vazios=0 | lixo (N/A, -)=0 | sem zero a esquerda (13 digitos)=175 | 14 digitos=11150

**resultados.tipo_pessoa**

| valor | registros |
| ----- | --------- |
| PJ    | 11344     |
| PF    | 4531      |
| PE    | 21        |

* registros no arquivo `compras.csv` e `resultados.csv`.

### 3.2. Padrões Monetários e Decimais

* **Problema:** Valores preenchidos como texto contendo o símbolo "R$", inversão gráfica de separadores de milhar/decimal e números negativos formatados entre parênteses.
* **Volume afetado:**
* `itens.csv` e `resultados.csv`.

**itens.quantidade**

| valor              | registros |
| ------------------ | --------- |
| so ponto decimal   | 5596      |
| com R$             | 1148      |
| so virgula decimal | 269       |
| 1,234.56 (US)      | 34        |
| 1.234,56 (BR)      | 30        |

**itens.valor_unitario_estimado**

| valor              | registros |
| ------------------ | --------- |
| so ponto decimal   | 5475      |
| com R$             | 1188      |
| so virgula decimal | 190       |
| 1,234.56 (US)      | 113       |
| 1.234,56 (BR)      | 111       |

**itens.valor_total_estimado**

| valor              | registros |
| ------------------ | --------- |
| so ponto decimal   | 5415      |
| com R$             | 1171      |
| 1.234,56 (BR)      | 219       |
| 1,234.56 (US)      | 200       |
| so virgula decimal | 72        |

**resultados.quantidade_homologada**

| valor              | registros |
| ------------------ | --------- |
| so ponto decimal   | 12472     |
| com R$             | 2561      |
| so virgula decimal | 451       |
| 1.234,56 (BR)      | 207       |
| 1,234.56 (US)      | 205       |

**resultados.valor_unitario_homologado**

| valor              | registros |
| ------------------ | --------- |
| so ponto decimal   | 12282     |
| com R$             | 2650      |
| so virgula decimal | 432       |
| 1.234,56 (BR)      | 274       |
| 1,234.56 (US)      | 258       |

**resultados.valor_total_homologado**

| valor              | registros |
| ------------------ | --------- |
| so ponto decimal   | 12064     |
| com R$             | 2647      |
| 1.234,56 (BR)      | 544       |
| 1,234.56 (US)      | 517       |
| so virgula decimal | 124       |

### 3.3. Coerência Temporal e Formatos de Data

* **Problema:** Datas gravadas sob múltiplas máscaras textuais e registros contendo violação cronológica grave (data de homologação/resultado anterior à data de publicação do edital).
* **Volume afetado:**
* casos de inconsistência cronológica.

**compras.data_publicacao**

| valor               | registros |
| ------------------- | --------- |
| AAAA-MM-DDThh:mm:ss | 1319      |
| DD-MM-AAAA          | 138       |
| DD/MM/AAAA hh:mm    | 126       |
| DD.MM.AAAA          | 120       |
| DD/MM/AAAA          | 117       |
| AAAA/MM/DD          | 116       |
| AAAAMMDD            | 106       |

**resultados.data_resultado**

| valor            | registros |
| ---------------- | --------- |
| AAAA-MM-DD       | 10301     |
| AAAA/MM/DD       | 960       |
| DD.MM.AAAA       | 937       |
| DD/MM/AAAA hh:mm | 934       |
| DD/MM/AAAA       | 929       |
| AAAAMMDD         | 923       |
| DD-MM-AAAA       | 912       |

**resultados.data_cancelamento**

| valor               | registros |
| ------------------- | --------- |
| vazio               | 15834     |
| AAAA-MM-DDThh:mm:ss | 62        |

- resultados.data_resultado preenchida mas invalida/fora de 2000-2030: 0
- resultados com data_resultado ANTERIOR a publicacao (cronologia impossivel): 234

### 3.4. Campos "Zumbis" (Nulos Disfarçados)

* **Problema:** Strings textuais mascarando valores ausentes, tais como `"N/A"`, `"NULL"`, `"-"`, `"SEM INFORMAÇÃO"` e `"NÃO SE APLICA"`.
* **Volume afetado:**
* ocorrências mapeadas:

| arquivo.coluna            | nulos disfarcados | vazios |
| ------------------------- | ----------------- | ------ |
| compras.processo          | 77                | 0      |
| compras.modo_disputa      | 967               | 0      |
| itens.categoria_item      | 7077              | 0      |
| itens.situacao_item       | 220               | 0      |
| itens.criterio_julgamento | 1883              | 0      |
| resultados.porte          | 4893              | 0      |

### 3.5. Sanitização Textual e Encodings

* **Problema:** Caracteres corrompidos devido ao conflito entre as codificações Latin-1 e UTF-8 (ex: `Ã§`, `Ã£`), além de grafias totalmente despadronizadas para um mesmo órgão comprador.
* **Volume afetado:**
* As linhas abaixo mostram o volume de registros corrigidos:

- compras.processo: 15 registros
- compras.objeto_compra: 173 registros
- compras.municipio: 30 registros
- compras.nome_unidade: 176 registros
- compras.modo_disputa: 15 registros
- itens.descricao: 223 registros
- itens.unidade_medida: 2 registros
- itens.situacao_item: 55 registros
- resultados.nome_fornecedor: 4 registros
- resultados.porte: 113 registros
