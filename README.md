
# PROJETO — esteira_analitica_end-to-end_dados_pncp_govbr

> PNCP (CSV bruto) → **Python** (auditoria + limpeza) → **PostgreSQL** (Star Schema) → **Power BI** (dashboard executivo)

---

## 1. Contexto do Problema

A Controladoria precisa de clareza sobre sobrepreço, concentração de fornecedores, morosidade dos certames e competitividade por modalidade, mas os dados brutos do PNCP (2.042 contratações, 7.077 itens, 15.896 resultados) vêm com CNPJ corrompido, dinheiro em texto livre, datas em 7 formatos e nulos disfarçados. O projeto **esteira_analitica_end-to-end_dados_pncp_govbr** transforma essa base em um ambiente confiável e auditável, que responde 6 perguntas de negócio.

---

## 2. Estrutura do Repositório

```
esteira_analitica_end-to-end_dados_pncp_govbr/
├── data/raw/          CSVs brutos (compras, itens, resultados)
├── data/processed/    tabelas limpas geradas pelo Python (fato + 4 dimensões)
├── docs/              medidas_dax.md · img/sprints.png
├── src/               config, banco, limpeza, auditoria, montar_tabelas, carregar
├── sql/               01_criar_banco.sql · 02_perguntas.sql
├── powerbi/           arquivo .pbix · tema.json
└── reports/           auditoria.md
```

---

## 3. Planejamento em Sprints e Monitoramento

A execução do projeto foi dividida em Sprints modulares, onde cada ciclo resulta em uma entrega auditável, mapeada diretamente com a prova real.

![Sprints do projeto](docs/imagens/sprints.png)

### Detalhamento das Entregas por Sprint

#### 3.1 Sprint 0: Repositório, Planejamento e Entendimento dos Dados

* **Objetivo:** criação do ambiente de desenvolvimento, segregação de pastas e análise descritiva inicial da estrutura dos arquivos CSV (`compras.csv`, `itens.csv`, `resultados.csv`).
* **Dados iniciais auditados:**
  * Total de linhas em `compras.csv`: **2.042**.
  * Total de linhas em `itens.csv`: **7.077**.
  * Total de linhas em `resultados.csv`: **15.896**.

#### 3.2 Sprint 1: Auditoria Qualitativa (Contagem de Problemas)

* **Objetivo:** identificar e quantificar o volume de anomalias encontradas nas tabelas brutas antes de aplicar os algoritmos de higienização.
* **Dicionário de inconsistências identificadas:**
  * **Despadronização de datas:** foram identificadas **7 máscaras diferentes** para o campo `data_publicacao` (incluindo formatos como `AAAAMMDD` e pontos separadores) e **7 máscaras** para `data_resultado`.
  * **Violação cronológica:** foram encontrados **234 resultados** com a data de homologação anterior à publicação do edital.
  * **Identificadores (CNPJ/CPF) sujos:** no arquivo de compras, **176 CNPJ de órgãos** possuem máscara e **10 perderam o zero à esquerda** (13 dígitos). Nos resultados dos fornecedores, **1.633 registros** possuem máscara e **175 perderam o zero à esquerda**.
  * **Padrões monetários e numéricos corrompidos:** presença de textos contendo "R$" (ex.: **1.148 itens** em quantidade e **1.188** em valor unitário), além de uma mistura de separadores decimais e de milhar nos padrões americano (US) e brasileiro (BR).
  * **Strings com nulos disfarçados:** presença massiva de termos textuais mascarando valores nulos, com destaque para o campo `itens.categoria_item`, com **7.077 registros** preenchidos com "Não se aplica", e para `resultados.porte`, com **4.893 registros** nulos ocultos.
  * **Erros de encoding (Latin-1 lido como UTF-8):** identificados caracteres corrompidos (`Ã§`, `Ã£`), afetando principalmente **223 descrições de itens** e **173 objetos de compras**.
  * **Nomes inconsistentes (grafias distintas):** o mesmo órgão comprador foi registrado de várias formas, totalizando **440 grafias para apenas 352 nomes padronizados**. O mesmo ocorre com fornecedores (**10.707 grafias para 10.165 nomes reais**).

#### 3.3 Sprint 2: Limpeza e Higienização (`src/limpeza.py`)

* **Objetivo:** completar as lacunas estruturais do script de limpeza e validar o sucesso por meio do autoteste.
* **Validação técnica:**
  * Execução bem-sucedida do comando `python -m src.limpeza`, com resultado positivo em todos os cenários de teste (54 de 54).

#### 3.4 Sprint 3: Modelagem Dimensional e Regras de Negócio (`src/montar_tabelas.py`)

* **Objetivo:** estruturar a tabela Fato e as dimensões aplicando os filtros rígidos determinados pela Controladoria.
* **Anotação de valores de conferência (camada Python):**
  * Itens sem resultado homologado descartados (Regra 3): **852**.
  * Itens com orçamento sigiloso (identificados como `True` na auditoria): **54**. *(Estes itens serão avaliados e devidamente rejeitados conforme a Regra 4 do projeto, por não possuírem orçamento estimado utilizável.)*

#### 3.5 Sprint 4: Infraestrutura de Banco de Dados (`sql/01_criar_banco.sql` e `src/carregar.py`)

* **Objetivo:** criação física do banco de dados no PostgreSQL e automação do pipeline de carga em lote com integridade referencial.
* **Métricas finais de ingestão no banco de dados:**
  * Linhas carregadas na `fato_item_contratado`: **6.126** [regra 1]
  * Contratações distintas mapeadas: **1.962**
  * Linhas na `dim_orgao` (CNPJ distintos): **363** [regra 10]
  * Linhas na `dim_fornecedor` (fornecedores distintos): **2.652** [regra 2]

#### 3.6 Sprint 5: Validação das Perguntas de Negócio em SQL (`sql/02_perguntas.sql`)

* **Objetivo:** escrever consultas analíticas no pgAdmin para responder às 6 perguntas estratégicas da Controladoria e garantir paridade com o pipeline.
* **Resultados consolidados de conferência (métricas de negócio):**
  * **Volume homologado total:** R$ 8.044.498.805,74 [termo volume]
  * **Volume de itens comparáveis:** 5.457 itens [regra 6]
  * **Taxa de economia (deságio geral):** 14,46% [regra 6]
  * **Tempo de ciclo médio / máximo:** 48,1 dias / 611 dias [regra 7]
  * **Itens sem ciclo (NULL):** 230 itens [regra 7]
  * **Perfil do gasto (% do volume):** Obras e engenharia: 60,8% | Serviços: 36,6% | Bens: 2,6% [regra 8]

#### 3.7 Sprint 6: Dashboard no Power BI (`powerbi/`)

* **Objetivo:** construir o dashboard executivo com no mínimo 15 medidas explícitas e uma história por pergunta (pergunta, números e conclusão), com os mesmos valores do SQL.
* **Entregas:**
  * Tabela Calendário em DAX, marcada como tabela de datas e relacionada às duas datas da fato (publicação ativa e homologação inativa, usada com `USERELATIONSHIP`).
  * Tabela dedicada de medidas (`_Medidas`), com as 15 medidas obrigatórias e 5 extras, organizada em uma pasta de exibição por pergunta e documentada em `docs/medidas_dax.md`.
  * Seis páginas, uma por pergunta, cada uma com caixa de conclusão.
  * Menu retrátil com bookmarks e página de tooltip.
  * Tema visual do relatório salvo em `powerbi/tema.json`.

#### 3.8 Sprint 7: Documentação, Figura das Sprints e Vídeo

* **Objetivo:** finalizar o README, a figura das Sprints e o vídeo de defesa técnica.
* **Conferência:** qualquer analista reproduz o projeto apenas lendo o README.

---

## 4. Decisões Técnicas

| Decisão                                                                                       | Motivo                                                         |
| ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Ler os CSVs como texto (`dtype=str`)                                                         | o CNPJ não perde o zero à esquerda                           |
| Ponto ou vírgula sozinho é sempre decimal; só o separador repetido é milhar                | sem essa regra o volume homologado iria para R$ 31 bi          |
| Zero só é nulo em campos de texto; datas válidas de 2000 a 2030                             | em quantidades e valores, o 0 é um número                    |
| Descartar os resultados cancelados antes de escolher o vencedor                                | se o primeiro colocado foi cancelado, o segundo assume o lugar |
| Item comparável: não é Credenciamento e a razão homologado ÷ estimado fica entre 0,1 e 10 | a economia é de 14,46%, e não de 75%                         |
| Homologação anterior à publicação anula a data e o ciclo, mas o item permanece na fato    | o ciclo médio não é distorcido e o volume é preservado     |
| Star Schema com 1 fato e 4 dimensões, chave substituta, `UNIQUE`, `CHECK` e `DECIMAL`   | integridade referencial e o banco como segunda barreira        |
| Carga com validação prévia, transação única e rollback                                   | o banco nunca fica meio carregado                              |
| Calendário em DAX com limites vindos dos dados e hierarquia automática de data desligada     | datas confiáveis e ordenação correta de mês e ano-mês     |

---

## 5. Arquitetura do Banco de Dados (Star Schema)

O banco segue o modelo dimensional estrela abaixo, mitigando redundâncias e acelerando as consultas analíticas:![Relacionamento das Tabelas](docs/imagens/Dimensões.PNG)

`O tempo é a tabela Calendario criada em DAX no Power BI.`

## 6. Técnicas e Tecnologias

* **Python:** pandas, psycopg2, expressões regulares.
* **PostgreSQL:** Star Schema, chaves substitutas, `UNIQUE`, `CHECK`, `DECIMAL`, inserção em lote, transação e rollback.
* **Power BI:** Calendário em DAX, medidas com `VAR`/`RETURN`, `CALCULATE`, `DIVIDE`, `TOPN`, `SUMX`, `USERELATIONSHIP`, bookmarks, tooltip e princípios de design (CRAP).
* **Git e GitHub:** versionamento com commits curtos, no imperativo.
* **Trello:** planejamento e acompanhamento das Sprints.

---

## 7. Instruções de Execução (Reprodutibilidade)

Para rodar a esteira analítica completa a partir dos arquivos brutos, execute os passos abaixo na ordem estabelecida pelas Sprints:

1. **Instalação das dependências do Python:**
   ```bash
   pip install pandas psycopg2-binary
   ```
2. **Executar os autotestes de limpeza (Sprint 2):**
   ```bash
   python -m src.limpeza
   ```
3. **Processar regras de negócio e montar estruturas (Sprint 3):**
   ```bash
   python -m src.montar_tabelas
   ```
4. **Criar o banco e executar a carga automatizada (Sprint 4):**
   ```bash
   python -m src.carregar
   ```

---

## 8. Melhorias Futuras

* Normalizar a unidade de medida.
* Separar serviços continuados de serviços eventuais.
* Criar testes automatizados com `pytest`.
* Agendar a carga para execução periódica.
