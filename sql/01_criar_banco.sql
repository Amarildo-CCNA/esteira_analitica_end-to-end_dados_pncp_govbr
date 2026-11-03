-- =====================================================================================
-- 01_criar_banco.sql  -  Star Schema do dados_pncp_govbr (PNCP 2025)
-- 1 FATO + 4 DIMENSOES. O banco em si e recriado por banco.recriar_banco() na carga.
-- Obs.: o banco.executar_script separa os comandos por ponto e virgula e remove
--       comentarios iniciados por dois hifens, entao NAO use ponto e virgula nem dois
--       hifens dentro de textos literais.
-- =====================================================================================

-- ---------------------------------- DIMENSOES ----------------------------------------
-- Chave substituta (sk_) = PK. Chave natural = UNIQUE. A linha sk = -1 ("Nao informado")
-- fica fora da sequencia 1, 2, 3... e garante que nenhuma FK da fato fique sem destino.

CREATE TABLE dim_orgao (
    sk_orgao    INTEGER      PRIMARY KEY,
    cnpj_orgao  VARCHAR(14)  NOT NULL UNIQUE,
    nome_orgao  VARCHAR(255) NOT NULL,
    poder       VARCHAR(20)  NOT NULL
);

CREATE TABLE dim_fornecedor (
    sk_fornecedor   INTEGER      PRIMARY KEY,
    ni_fornecedor   VARCHAR(30)  NOT NULL UNIQUE,
    nome_fornecedor VARCHAR(255),
    tipo_pessoa     VARCHAR(2),
    porte           VARCHAR(60)
);

CREATE TABLE dim_modalidade (
    sk_modalidade   INTEGER      PRIMARY KEY,
    modalidade_id   INTEGER      NOT NULL UNIQUE,
    nome_modalidade VARCHAR(60)  NOT NULL
);

CREATE TABLE dim_localidade (
    sk_localidade INTEGER      PRIMARY KEY,
    uf_sigla      VARCHAR(2)   NOT NULL UNIQUE,
    uf_nome       VARCHAR(40)  NOT NULL,
    regiao        VARCHAR(20)  NOT NULL
);

INSERT INTO dim_orgao        VALUES (-1, '00000000000000', 'NAO INFORMADO', 'Não informado');
INSERT INTO dim_fornecedor   VALUES (-1, '-1', 'NAO INFORMADO', NULL, NULL);
INSERT INTO dim_modalidade   VALUES (-1, -1, 'Não informado');
INSERT INTO dim_localidade   VALUES (-1, 'ND', 'Não informado', 'Não informado');

-- ------------------------------------ FATO -------------------------------------------
-- Grao: 1 linha por item de contratacao (numero_controle_pncp + numero_item).
CREATE TABLE fato_item_contratado (
    sk_fato                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    numero_controle_pncp        VARCHAR(60)    NOT NULL,
    numero_item                 INTEGER        NOT NULL,

    sk_orgao                    INTEGER        NOT NULL REFERENCES dim_orgao (sk_orgao),
    sk_fornecedor               INTEGER        NOT NULL REFERENCES dim_fornecedor (sk_fornecedor),
    sk_modalidade               INTEGER        NOT NULL REFERENCES dim_modalidade (sk_modalidade),
    sk_localidade               INTEGER        NOT NULL REFERENCES dim_localidade (sk_localidade),

    data_publicacao             DATE,
    data_homologacao            DATE,

    descricao_item              TEXT,
    perfil_gasto                VARCHAR(20)    NOT NULL,

    quantidade                  DECIMAL(18,4)  NOT NULL,
    valor_unitario_estimado     DECIMAL(18,4)  NOT NULL,
    valor_total_estimado        DECIMAL(18,2)  NOT NULL,
    valor_unitario_homologado   DECIMAL(18,4)  NOT NULL,
    valor_total_homologado      DECIMAL(18,2)  NOT NULL,

    comparavel                  SMALLINT       NOT NULL,
    economia_valor              DECIMAL(18,2),
    dias_ciclo                  INTEGER,

    CONSTRAINT uq_fato_item UNIQUE (numero_controle_pncp, numero_item),
    CONSTRAINT ck_quantidade_positiva CHECK (quantidade > 0),
    CONSTRAINT ck_valores_nao_negativos CHECK (
        valor_unitario_estimado   >= 0 AND valor_total_estimado   >= 0 AND
        valor_unitario_homologado >= 0 AND valor_total_homologado >= 0),
    CONSTRAINT ck_comparavel CHECK (comparavel IN (0, 1)),
    CONSTRAINT ck_perfil CHECK (perfil_gasto IN ('Bens', 'Serviços', 'Obras e engenharia')),
    CONSTRAINT ck_ciclo_nao_negativo CHECK (dias_ciclo IS NULL OR dias_ciclo >= 0),
    CONSTRAINT ck_ciclo_sem_data CHECK (dias_ciclo IS NULL OR data_homologacao IS NOT NULL)
);

-- Indices nas FKs (o PostgreSQL nao cria sozinho) e nas colunas mais filtradas
CREATE INDEX ix_fato_orgao       ON fato_item_contratado (sk_orgao);
CREATE INDEX ix_fato_fornecedor  ON fato_item_contratado (sk_fornecedor);
CREATE INDEX ix_fato_modalidade  ON fato_item_contratado (sk_modalidade);
CREATE INDEX ix_fato_localidade  ON fato_item_contratado (sk_localidade);
CREATE INDEX ix_fato_publicacao  ON fato_item_contratado (data_publicacao);
