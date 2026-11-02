-- =====================================================================================
-- 02_perguntas.sql  -  As 6 perguntas de negocio da Controladoria (Speculum_gov)
-- Regras: percentual = SOMA / SOMA (nunca media de percentuais)
--         economia so conta itens comparaveis (comparavel = 1)
--         denominador que pode ser zero usa NULLIF
-- =====================================================================================


-- -------------------------------------------------------------------------------------
-- P1. Economia global: qual o percentual e o valor nominal economizado pelo governo?
-- Esperado (prova real): economia R$ 992.861.686,95 | 14,46% | 5.457 itens comparaveis
-- -------------------------------------------------------------------------------------
SELECT
    SUM(valor_total_homologado)                                                         AS volume_homologado,
    SUM(valor_total_estimado)                                                           AS estimado_todos_itens,
    SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado  ELSE 0 END)                 AS estimado_comparavel,
    SUM(CASE WHEN comparavel = 1 THEN valor_total_homologado ELSE 0 END)                AS homologado_comparavel,
    SUM(economia_valor)                                                                 AS economia_nominal,
    ROUND(100.0 * SUM(economia_valor)
          / NULLIF(SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado ELSE 0 END), 0), 2) AS economia_pct,
    SUM(comparavel)                                                                     AS itens_comparaveis,
    COUNT(*)                                                                            AS itens_total,
    ROUND(100.0 * SUM(comparavel) / COUNT(*), 1)                                        AS pct_itens_comparaveis,
    SUM(CASE WHEN comparavel = 1 AND valor_total_homologado > valor_total_estimado THEN 1 ELSE 0 END) AS itens_sobrepreco
FROM fato_item_contratado;


-- -------------------------------------------------------------------------------------
-- P2. Concentracao: quem sao os 10 maiores fornecedores em volume e quanto do total concentram?
-- (fornecedor = ni_fornecedor limpo: filiais com CNPJ diferente contam separadas)
-- -------------------------------------------------------------------------------------
SELECT
    RANK() OVER (ORDER BY SUM(f.valor_total_homologado) DESC)                           AS ranking,
    d.ni_fornecedor,
    d.nome_fornecedor,
    COUNT(*)                                                                            AS itens,
    SUM(f.valor_total_homologado)                                                       AS volume_homologado,
    ROUND(100.0 * SUM(f.valor_total_homologado)
          / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado), 2)          AS participacao_pct
FROM fato_item_contratado f
JOIN dim_fornecedor d ON d.sk_fornecedor = f.sk_fornecedor
GROUP BY d.ni_fornecedor, d.nome_fornecedor
ORDER BY volume_homologado DESC
LIMIT 10;

-- P2 (complemento): concentracao acumulada dos 10 maiores sobre o volume total
WITH volume_por_fornecedor AS (
    SELECT sk_fornecedor, SUM(valor_total_homologado) AS volume
    FROM fato_item_contratado
    GROUP BY sk_fornecedor
),
top10 AS (
    SELECT volume FROM volume_por_fornecedor ORDER BY volume DESC LIMIT 10
)
SELECT
    (SELECT SUM(volume) FROM top10)                                                     AS volume_top10,
    (SELECT SUM(volume) FROM volume_por_fornecedor)                                     AS volume_total,
    ROUND(100.0 * (SELECT SUM(volume) FROM top10)
          / (SELECT SUM(volume) FROM volume_por_fornecedor), 2)                         AS concentracao_top10_pct;


-- -------------------------------------------------------------------------------------
-- P3. Eficacia por modalidade: qual economiza mais (desagio) e qual concentra mais recursos?
-- Credenciamento (12) nao tem item comparavel: desagio fica vazio (esperado, nao e erro).
-- -------------------------------------------------------------------------------------
SELECT
    m.modalidade_id,
    m.nome_modalidade,
    COUNT(*)                                                                            AS itens,
    SUM(f.valor_total_homologado)                                                       AS volume_homologado,
    ROUND(100.0 * SUM(f.valor_total_homologado)
          / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado), 2)          AS participacao_volume_pct,
    SUM(f.economia_valor)                                                               AS economia_nominal,
    ROUND(100.0 * SUM(f.economia_valor)
          / NULLIF(SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_estimado ELSE 0 END), 0), 2) AS desagio_pct
FROM fato_item_contratado f
JOIN dim_modalidade m ON m.sk_modalidade = f.sk_modalidade
GROUP BY m.modalidade_id, m.nome_modalidade
ORDER BY desagio_pct DESC NULLS LAST;


-- -------------------------------------------------------------------------------------
-- P4. Ciclo de compras: duracao media (dias) entre publicacao e homologacao, por orgao.
-- Agrupa pelo NOME padronizado (o mesmo orgao tem varias unidades/CNPJ), conta so itens
-- com ciclo (COUNT(dias_ciclo) ignora NULL) e mostra orgaos com 5 ou mais itens com ciclo.
-- -------------------------------------------------------------------------------------
SELECT
    o.nome_orgao,
    COUNT(DISTINCT o.cnpj_orgao)                                                        AS unidades_compradoras,
    COUNT(f.dias_ciclo)                                                                 AS itens_com_ciclo,
    ROUND(AVG(f.dias_ciclo), 1)                                                         AS ciclo_medio_dias,
    MAX(f.dias_ciclo)                                                                   AS ciclo_maximo_dias
FROM fato_item_contratado f
JOIN dim_orgao o ON o.sk_orgao = f.sk_orgao
GROUP BY o.nome_orgao
HAVING COUNT(f.dias_ciclo) >= 5
ORDER BY ciclo_medio_dias DESC;

-- P4 (complemento): visao geral do ciclo. Esperado: 5.896 com ciclo | media 48,1 | max 611 | 230 sem ciclo
SELECT
    COUNT(dias_ciclo)                                                                   AS itens_com_ciclo,
    ROUND(AVG(dias_ciclo), 1)                                                           AS ciclo_medio_dias,
    MAX(dias_ciclo)                                                                     AS ciclo_maximo_dias,
    COUNT(*) - COUNT(dias_ciclo)                                                        AS itens_sem_ciclo
FROM fato_item_contratado;


-- -------------------------------------------------------------------------------------
-- P5. Distribuicao regional: onde se gasta mais e onde o desconto e melhor?
-- -------------------------------------------------------------------------------------
-- Por UF
SELECT
    l.uf_sigla,
    l.uf_nome,
    l.regiao,
    COUNT(DISTINCT o.cnpj_orgao)                                                        AS unidades_compradoras,
    SUM(f.valor_total_homologado)                                                       AS volume_homologado,
    ROUND(100.0 * SUM(f.valor_total_homologado)
          / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado), 2)          AS participacao_volume_pct,
    ROUND(100.0 * SUM(f.economia_valor)
          / NULLIF(SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_estimado ELSE 0 END), 0), 2) AS desagio_pct
FROM fato_item_contratado f
JOIN dim_localidade l ON l.sk_localidade = f.sk_localidade
JOIN dim_orgao      o ON o.sk_orgao      = f.sk_orgao
GROUP BY l.uf_sigla, l.uf_nome, l.regiao
ORDER BY volume_homologado DESC;

-- Por regiao
SELECT
    l.regiao,
    COUNT(DISTINCT o.cnpj_orgao)                                                        AS unidades_compradoras,
    SUM(f.valor_total_homologado)                                                       AS volume_homologado,
    ROUND(100.0 * SUM(f.valor_total_homologado)
          / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado), 2)          AS participacao_volume_pct,
    ROUND(100.0 * SUM(f.economia_valor)
          / NULLIF(SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_estimado ELSE 0 END), 0), 2) AS desagio_pct
FROM fato_item_contratado f
JOIN dim_localidade l ON l.sk_localidade = f.sk_localidade
JOIN dim_orgao      o ON o.sk_orgao      = f.sk_orgao
GROUP BY l.regiao
ORDER BY volume_homologado DESC;


-- -------------------------------------------------------------------------------------
-- P6. Perfil dos gastos: como o dinheiro se distribui entre bens, servicos e obras?
-- (perfil_gasto e coluna da propria fato: sem JOIN)
-- Esperado: Obras e engenharia 60,8% (967 itens) | Servicos 36,6% (1.849) | Bens 2,6% (3.310)
-- -------------------------------------------------------------------------------------
SELECT
    perfil_gasto,
    COUNT(*)                                                                            AS itens,
    SUM(valor_total_homologado)                                                         AS volume_homologado,
    ROUND(100.0 * SUM(valor_total_homologado)
          / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado), 1)          AS participacao_volume_pct,
    ROUND(SUM(valor_total_homologado) / COUNT(*), 2)                                    AS ticket_medio_item,
    ROUND(100.0 * SUM(economia_valor)
          / NULLIF(SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado ELSE 0 END), 0), 2) AS desagio_pct
FROM fato_item_contratado
GROUP BY perfil_gasto
ORDER BY volume_homologado DESC;