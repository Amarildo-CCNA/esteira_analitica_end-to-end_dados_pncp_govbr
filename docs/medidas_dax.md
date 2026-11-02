# Medidas DAX — esteira_analitica_end-to-end_dados_pncp_govbr

Documentação do Calendário e das medidas criadas no Power BI. O modelo é uma estrela (`fato_item_contratado` e 4 dimensões), e todos os números do dashboard vêm da tabela dedicada `_Medidas`, sem soma implícita. As medidas usam `VAR` e `RETURN`, e os percentuais são sempre `DIVIDE` de soma por soma, nunca média de percentuais.

---

## 1. Visão Geral

São **20 medidas** em `_Medidas`: as **15 obrigatórias** (organizadas em uma pasta de exibição por pergunta) e **5 extras** de apoio.

| Nº | Medida | Pergunta | Página |
|---|---|---|---|
| 1 | Valor Estimado Comparável | P1 · Economia | 1 |
| 2 | Volume Homologado | P1 · Economia | 1, 2, 3, 5, 6 |
| 3 | Economia (R$) | P1 · Economia | 1 |
| 4 | Economia % | P1 · Economia | 1, 3, 5, 6 |
| 5 | % de Itens Comparáveis | P1 · Economia | 1, 3 |
| 6 | Participação do Fornecedor % | P2 · Fornecedores | 2 |
| 7 | Ranking do Fornecedor | P2 · Fornecedores | 2 |
| 8 | Concentração Top 10 % | P2 · Fornecedores | 2 |
| 9 | Participação no Volume % | P3 · Modalidades | 3, 5, 6 |
| 10 | Deságio vs Média Geral (p.p.) | P3 · Modalidades | 3 |
| 11 | Ciclo Médio (dias) | P4 · Ciclo | 4 |
| 12 | Ciclo Máximo (dias) | P4 · Ciclo | 4 |
| 13 | Itens sem Ciclo | P4 · Ciclo | 4 |
| 14 | Qtd Unidades Compradoras | P5 · Regional | 5 |
| 15 | Ticket Médio por Item (R$) | P6 · Perfil | 6 |
| E1 a E5 | Medidas extras | Apoio | — |

---

## 2. Calendário (tabela em DAX)

Tabela de datas dinâmica, com limites que vêm dos dados: do primeiro dia do ano da menor publicação ao último dia do ano da maior homologação. O mês é ordenado por `Mês Nº` e o ano-mês por `Ano-Mês Nº` (AAAAMM). A tabela é marcada como tabela de datas e a hierarquia automática de data do Power BI está desligada.

Relacionamentos com a fato: `Calendario[Data]` → `data_publicacao` (ativa) e `Calendario[Data]` → `data_homologacao` (inativa, usada com `USERELATIONSHIP`).

```dax
Calendario =
VAR _ini = DATE ( YEAR ( MIN ( fato_item_contratado[data_publicacao] ) ), 1, 1 )
VAR _fim = DATE ( YEAR ( MAX ( fato_item_contratado[data_homologacao] ) ), 12, 31 )
RETURN
    SELECTCOLUMNS (
        CALENDAR ( _ini, _fim ),
        "Data", [Date],
        "Ano", YEAR ( [Date] ),
        "Mês Nº", MONTH ( [Date] ),
        "Mês", FORMAT ( [Date], "MMM" ),
        "Ano-Mês Nº", YEAR ( [Date] ) * 100 + MONTH ( [Date] ),
        "Ano-Mês", FORMAT ( [Date], "yyyy-MM" )
    )
```

---

## 3. Tabela de Medidas

Tabela criada apenas para abrigar as medidas.

```dax
_Medidas = ROW ( "x", 1 )
```

---

## 4. Medidas por Pergunta

### 4.1 Pergunta 1 · Economia (Página 1)

#### Medida 1 · Valor Estimado Comparável

Soma do valor total estimado apenas dos itens comparáveis (`comparavel = 1`).

```dax
Valor Estimado Comparável =
VAR _estimadoComparavel =
    CALCULATE (
        SUM ( fato_item_contratado[valor_total_estimado] ),
        fato_item_contratado[comparavel] = 1
    )
RETURN
    _estimadoComparavel
```

#### Medida 2 · Volume Homologado

Soma do valor total homologado de todos os itens da fato (comparáveis ou não).

```dax
Volume Homologado =
VAR _volume = SUM ( fato_item_contratado[valor_total_homologado] )
RETURN
    _volume
```

#### Medida 3 · Economia (R$)

Estimado comparável menos o homologado dos itens comparáveis. O `CALCULATE` filtra `comparavel = 1`, por isso a economia não mistura itens que não podem ser comparados.

```dax
Economia (R$) =
VAR _estimado = [Valor Estimado Comparável]
VAR _homologado =
    CALCULATE ( [Volume Homologado], fato_item_contratado[comparavel] = 1 )
RETURN
    _estimado - _homologado
```

#### Medida 4 · Economia %

Economia (R$) dividida pelo valor estimado comparável: soma sobre soma, nunca média de percentuais.

```dax
Economia % =
VAR _economia = [Economia (R$)]
VAR _base = [Valor Estimado Comparável]
RETURN
    DIVIDE ( _economia, _base )
```

#### Medida 5 · % de Itens Comparáveis

Itens comparáveis divididos pelo total de itens. Mostra quanto da base entra no cálculo da economia.

```dax
% de Itens Comparáveis =
VAR _comparaveis =
    CALCULATE ( COUNTROWS ( fato_item_contratado ), fato_item_contratado[comparavel] = 1 )
VAR _total = COUNTROWS ( fato_item_contratado )
RETURN
    DIVIDE ( _comparaveis, _total )
```

---

### 4.2 Pergunta 2 · Fornecedores (Página 2)

Usa também a Medida 2 (Volume Homologado).

#### Medida 6 · Participação do Fornecedor %

Volume do fornecedor dividido pelo volume total. O total ignora o filtro de fornecedor (`ALL` na dimensão).

```dax
Participação do Fornecedor % =
VAR _volume = [Volume Homologado]
VAR _total =
    CALCULATE ( [Volume Homologado], ALL ( dim_fornecedor ) )
RETURN
    DIVIDE ( _volume, _total )
```

#### Medida 7 · Ranking do Fornecedor

Posição do fornecedor por volume (1º, 2º, 3º...), com `RANKX` sobre `ALL`. Só aparece quando há um único fornecedor no contexto e volume preenchido.

```dax
Ranking do Fornecedor =
VAR _volume = [Volume Homologado]
RETURN
    IF (
        HASONEVALUE ( dim_fornecedor[sk_fornecedor] ) && NOT ISBLANK ( _volume ),
        RANKX ( ALL ( dim_fornecedor ), [Volume Homologado], , DESC, DENSE )
    )
```

#### Medida 8 · Concentração Top 10 %

O `TOPN` seleciona os 10 maiores fornecedores por volume e o `SUMX` soma o volume de cada um. O resultado é dividido pelo volume total.

```dax
Concentração Top 10 % =
VAR _total =
    CALCULATE ( [Volume Homologado], ALL ( dim_fornecedor ) )
VAR _top10 =
    TOPN ( 10, ALL ( dim_fornecedor[sk_fornecedor] ), [Volume Homologado], DESC )
VAR _volumeTop10 = SUMX ( _top10, [Volume Homologado] )
RETURN
    DIVIDE ( _volumeTop10, _total )
```

---

### 4.3 Pergunta 3 · Modalidades (Página 3)

Usa também as Medidas 2, 4 e 5.

#### Medida 9 · Participação no Volume %

Volume da linha atual (modalidade, UF, perfil...) dividido pelo volume total dos itens selecionados.

```dax
Participação no Volume % =
VAR _linha = [Volume Homologado]
VAR _total =
    CALCULATE ( [Volume Homologado], ALLSELECTED () )
RETURN
    DIVIDE ( _linha, _total )
```

#### Medida 10 · Deságio vs Média Geral (p.p.)

Economia % da linha atual menos a Economia % geral (sem nenhum filtro), em pontos percentuais. Esta medida é formatada como **número com 1 casa decimal**, nunca como porcentagem: formatada como %, uma diferença de 5 p.p. apareceria como 500%.

```dax
Deságio vs Média Geral (p.p.) =
VAR _linha = [Economia %]
VAR _geral =
    CALCULATE ( [Economia %], REMOVEFILTERS () )
RETURN
    IF ( NOT ISBLANK ( _linha ), ( _linha - _geral ) * 100 )
```

---

### 4.4 Pergunta 4 · Ciclo (Página 4)

#### Medida 11 · Ciclo Médio (dias)

Média dos dias entre publicação e homologação. Itens sem ciclo ficam em branco e a média já os ignora.

```dax
Ciclo Médio (dias) =
VAR _media = AVERAGE ( fato_item_contratado[dias_ciclo] )
RETURN
    _media
```

#### Medida 12 · Ciclo Máximo (dias)

Maior ciclo observado.

```dax
Ciclo Máximo (dias) =
VAR _maximo = MAX ( fato_item_contratado[dias_ciclo] )
RETURN
    _maximo
```

#### Medida 13 · Itens sem Ciclo

Itens cuja homologação ficou sem data (anterior à publicação ou data inválida): total de itens menos itens com ciclo.

```dax
Itens sem Ciclo =
VAR _total = COUNTROWS ( fato_item_contratado )
VAR _comCiclo = COUNT ( fato_item_contratado[dias_ciclo] )
RETURN
    _total - _comCiclo
```

---

### 4.5 Pergunta 5 · Regional (Página 5)

Usa também as Medidas 2, 4 e 9.

#### Medida 14 · Qtd Unidades Compradoras

Número de órgãos distintos por chave substituta. Cada CNPJ de órgão é uma unidade compradora, e o mesmo órgão pode ter várias.

```dax
Qtd Unidades Compradoras =
VAR _unidades = DISTINCTCOUNT ( fato_item_contratado[sk_orgao] )
RETURN
    _unidades
```

---

### 4.6 Pergunta 6 · Perfil (Página 6)

Usa também as Medidas 2, 4 e 9.

#### Medida 15 · Ticket Médio por Item (R$)

Volume homologado dividido pela quantidade de itens.

```dax
Ticket Médio por Item (R$) =
VAR _volume = [Volume Homologado]
VAR _itens = COUNTROWS ( fato_item_contratado )
RETURN
    DIVIDE ( _volume, _itens )
```

---

## 5. Medidas Extras

Medidas de apoio que enriquecem as páginas e os tooltips.

#### Extra E1 · Itens com Ciclo

Quantidade de itens com `dias_ciclo` preenchido.

```dax
Itens com Ciclo =
VAR _itens = COUNT ( fato_item_contratado[dias_ciclo] )
RETURN
    _itens
```

#### Extra E2 · Itens com Sobrepreço

Itens comparáveis em que o valor total homologado ficou acima do estimado.

```dax
Itens com Sobrepreço =
VAR _itens =
    CALCULATE (
        COUNTROWS ( fato_item_contratado ),
        FILTER (
            fato_item_contratado,
            fato_item_contratado[comparavel] = 1
                && fato_item_contratado[valor_total_homologado] > fato_item_contratado[valor_total_estimado]
        )
    )
RETURN
    _itens
```

#### Extra E3 · Volume por Data de Homologação

Volume homologado agrupado pela data de homologação, usando a relação inativa com o Calendário (`USERELATIONSHIP`).

```dax
Volume por Data de Homologação =
VAR _volume =
    CALCULATE (
        [Volume Homologado],
        USERELATIONSHIP ( Calendario[Data], fato_item_contratado[data_homologacao] )
    )
RETURN
    _volume
```

#### Extra E4 · Qtd Itens

Quantidade de itens da fato.

```dax
Qtd Itens =
VAR _itens = COUNTROWS ( fato_item_contratado )
RETURN
    _itens
```

#### Extra E5 · Qtd Fornecedores

Número de fornecedores distintos por chave substituta (o mesmo nome com CNPJ diferente conta como fornecedores diferentes).

```dax
Qtd Fornecedores =
VAR _fornecedores = DISTINCTCOUNT ( fato_item_contratado[sk_fornecedor] )
RETURN
    _fornecedores
```
