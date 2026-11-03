# Auditoria dos dados brutos

## 1. Volume dos arquivos

- compras.csv: 2042 linhas | itens.csv: 7077 linhas | resultados.csv: 15896 linhas
- numero_controle_pncp repetido em compras: 0
- itens repetidos (controle + item): 0
- itens sem compra correspondente: 0
- resultados sem item correspondente: 0
- itens com tem_resultado=True: 6225
- resultados com data_cancelamento preenchida: 62
- itens com mais de 1 resultado (SRP/credenciamento): 466

## 2. Formatos de data


**compras.data_publicacao**

| valor | registros |
|---|---|
| AAAA-MM-DDThh:mm:ss | 1319 |
| DD-MM-AAAA | 138 |
| DD/MM/AAAA hh:mm | 126 |
| DD.MM.AAAA | 120 |
| DD/MM/AAAA | 117 |
| AAAA/MM/DD | 116 |
| AAAAMMDD | 106 |

**resultados.data_resultado**

| valor | registros |
|---|---|
| AAAA-MM-DD | 10301 |
| AAAA/MM/DD | 960 |
| DD.MM.AAAA | 937 |
| DD/MM/AAAA hh:mm | 934 |
| DD/MM/AAAA | 929 |
| AAAAMMDD | 923 |
| DD-MM-AAAA | 912 |

**resultados.data_cancelamento**

| valor | registros |
|---|---|
| vazio | 15834 |
| AAAA-MM-DDThh:mm:ss | 62 |

- resultados.data_resultado preenchida mas invalida/fora de 2000-2030: 0
- resultados com data_resultado ANTERIOR a publicacao (cronologia impossivel): 234

## 3. Formatos de dinheiro e numeros


**itens.quantidade**

| valor | registros |
|---|---|
| so ponto decimal | 5596 |
| com R$ | 1148 |
| so virgula decimal | 269 |
| 1,234.56 (US) | 34 |
| 1.234,56 (BR) | 30 |

**itens.valor_unitario_estimado**

| valor | registros |
|---|---|
| so ponto decimal | 5475 |
| com R$ | 1188 |
| so virgula decimal | 190 |
| 1,234.56 (US) | 113 |
| 1.234,56 (BR) | 111 |

**itens.valor_total_estimado**

| valor | registros |
|---|---|
| so ponto decimal | 5415 |
| com R$ | 1171 |
| 1.234,56 (BR) | 219 |
| 1,234.56 (US) | 200 |
| so virgula decimal | 72 |

**resultados.quantidade_homologada**

| valor | registros |
|---|---|
| so ponto decimal | 12472 |
| com R$ | 2561 |
| so virgula decimal | 451 |
| 1.234,56 (BR) | 207 |
| 1,234.56 (US) | 205 |

**resultados.valor_unitario_homologado**

| valor | registros |
|---|---|
| so ponto decimal | 12282 |
| com R$ | 2650 |
| so virgula decimal | 432 |
| 1.234,56 (BR) | 274 |
| 1,234.56 (US) | 258 |

**resultados.valor_total_homologado**

| valor | registros |
|---|---|
| so ponto decimal | 12064 |
| com R$ | 2647 |
| 1.234,56 (BR) | 544 |
| 1,234.56 (US) | 517 |
| so virgula decimal | 124 |

## 4. Documentos (CNPJ/CPF)

- compras.cnpj_orgao: com mascara=176 | vazios=0 | lixo (N/A, -)=0 | sem zero a esquerda (13 digitos)=10 | 14 digitos=1965
- resultados.ni_fornecedor: com mascara=1633 | vazios=0 | lixo (N/A, -)=0 | sem zero a esquerda (13 digitos)=175 | 14 digitos=11150

**resultados.tipo_pessoa**

| valor | registros |
|---|---|
| PJ | 11344 |
| PF | 4531 |
| PE | 21 |

## 5. Nulos disfarcados por coluna de texto (N/A, NULL, -, 0, SEM INFORMACAO, NAO SE APLICA, vazio)

| arquivo.coluna | nulos disfarcados | vazios |
|---|---|---|
| compras.processo | 77 | 0 |
| compras.modo_disputa | 967 | 0 |
| itens.categoria_item | 7077 | 0 |
| itens.situacao_item | 220 | 0 |
| itens.criterio_julgamento | 1883 | 0 |
| resultados.porte | 4893 | 0 |

## 6. Encoding quebrado (Latin-1 lido como UTF-8: Ã§, Ã£...)

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

## 7. Nomes inconsistentes

- razao_social_orgao: 440 grafias distintas -> 352 nomes padronizados
- cnpj_orgao distintos apos limpeza: 370
- nome_fornecedor: 10707 grafias distintas -> 10165 padronizadas
- modalidade_nome: 7 grafias para 7 modalidade_id

**itens.categoria_item (nao ajuda, conforme enunciado)**

| valor | registros |
|---|---|
| Não se aplica | 7077 |

**itens.sigiloso**

| valor | registros |
|---|---|
| False | 7023 |
| True | 54 |
