# -*- coding: utf-8 -*-
"""
Competição de Carteiras UFPR 2026 — App Streamlit para alunos
Mercado Financeiro e de Capitais — UFPR Ciências Contábeis

Preços via Yahoo Finance · CDI via API Banco Central do Brasil
Cache de 30 minutos (dados atualizam automaticamente)
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
from collections import defaultdict
import time
import math

def _safe(v):
    """Retorna None se v for None, NaN ou infinito."""
    try:
        return v if (v is not None and math.isfinite(v)) else None
    except Exception:
        return None

st.set_page_config(
    page_title="Competição de Carteiras UFPR 2026",
    page_icon="📊",
    layout="wide",
)

# ── Senha de acesso ────────────────────────────────────────────────────
def _check_password() -> bool:
    try:
        senha_correta = st.secrets["senha_turma"]
    except (FileNotFoundError, KeyError):
        return True  # desenvolvimento local → acesso livre
    if st.session_state.get("_auth_ok", False):
        return True
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 📊 Competição de Carteiras UFPR 2026")
        st.caption("Mercado Financeiro e de Capitais — UFPR Ciências Contábeis")
        st.text_input("Senha de acesso", type="password", key="_senha_input")
        if st.button("Entrar", type="primary", use_container_width=True):
            if st.session_state.get("_senha_input", "") == senha_correta:
                st.session_state["_auth_ok"] = True
                st.rerun()
            else:
                st.error("Senha incorreta. Consulte o professor.")
    return False

if not _check_password():
    st.stop()

# ── Configuração da competição ─────────────────────────────────────────
INVESTIMENTO_INICIAL = 100_000.00

EQUIPES = [
    {"nome": "ACLS",                    "turma": "A", "data": "2026-03-08", "int1": "Ane Caroline De Lima Da Silva",         "int2": "",                              "ativos": ["SLCE3","BBAS3","PRIO3","QBTC11"],    "pesos": [0.35,0.25,0.25,0.15]},
    {"nome": "Alpha Capital",            "turma": "A", "data": "2026-03-12", "int1": "Eduardo Nunes E Silva",                 "int2": "Garcia Kiala Marques",          "ativos": ["PETR4","ABEV3","PRIO3","VALE3"],      "pesos": [0.30,0.30,0.20,0.20]},
    {"nome": "Bagulhete",               "turma": "A", "data": "2026-03-12", "int1": "Chrystoffer Cauan Lopes Stenzel",       "int2": "",                              "ativos": ["VALE3","HGLG11","NVDC34","IVVB11"],   "pesos": [0.30,0.20,0.40,0.10]},
    {"nome": "Barra & Barril",          "turma": "A", "data": "2026-03-02", "int1": "Gustavo Artur Bueno Valerio",           "int2": "Rodrigo Ribeiro De Padua",      "ativos": ["GOLD11","PETR4","CPLE3","VALE3"],     "pesos": [0.45,0.30,0.125,0.125]},
    {"nome": "Borba e Gerber",          "turma": "A", "data": "2026-03-12", "int1": "Graziele Borba Dos Santos",             "int2": "Luiz Gustavo Dudek Gerber",     "ativos": ["ITUB4","ASML34","TSMC34","MELI34"],   "pesos": [0.40,0.35,0.15,0.10]},
    {"nome": "BÊTRÊS",                  "turma": "A", "data": "2026-03-11", "int1": "",                                      "int2": "",                              "ativos": ["WEGE3","EGIE3","HGLG11","BBAS3"],     "pesos": [0.22,0.23,0.20,0.35]},
    {"nome": "Carteira Núcleo Brasil",  "turma": "A", "data": "2026-03-12", "int1": "Giovanna Geffer De Faria",              "int2": "Milene Herbst De Lima",         "ativos": ["ITUB4","PETR4","ABEV3","WEGE3"],      "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "Cash and Caos",           "turma": "A", "data": "2026-03-03", "int1": "Gabriel Ramos Caetano",                 "int2": "Maria Paula Silva Amaral",      "ativos": ["PETR4","VALE3","AAPL34","IVVB11"],    "pesos": [0.30,0.30,0.20,0.20]},
    {"nome": "D&F",                     "turma": "A", "data": "2026-03-11", "int1": "Danilo Santos Mendonca Teixeira",       "int2": "Francisco Leonardo De Alencar", "ativos": ["PETR4","BBAS3","NVDC34","MSFT34"],    "pesos": [0.15,0.20,0.40,0.25]},
    {"nome": "Eloyse",                  "turma": "A", "data": "2026-03-11", "int1": "Eloyse Age",                            "int2": "",                              "ativos": ["BBAS3","WEGE3","PETR4","BOVA11"],     "pesos": [0.25,0.30,0.30,0.15]},
    {"nome": "Equipe Lucro Certo",      "turma": "A", "data": "2026-03-11", "int1": "Daniel Arruda Da Silva Riffert",        "int2": "",                              "ativos": ["TOTS3","NVDC34","MSFT34","NASD11"],   "pesos": [0.25,0.30,0.25,0.20]},
    {"nome": "Joaeh",                   "turma": "A", "data": "2026-03-11", "int1": "Juarildo Juliano Dias De Oliveira",     "int2": "Caue Alexandre Pereira",        "ativos": ["PETR4","CPLE3","BOVA11","A1MD34"],    "pesos": [0.30,0.30,0.20,0.20]},
    {"nome": "FerInvest",               "turma": "A", "data": "2026-03-01", "int1": "Fernanda Cristina Dos Santos Do Couto","int2": "",                              "ativos": ["PETR4","NVDC34","BOVA11","IVVB11"],   "pesos": [0.20,0.25,0.30,0.25]},
    {"nome": "GC",                      "turma": "A", "data": "2026-03-12", "int1": "Giovanna Castellon",                   "int2": "",                              "ativos": ["PETR4","ITUB4","WEGE3","NVDC34"],     "pesos": [0.25,0.20,0.20,0.35]},
    {"nome": "Herika Stocks",           "turma": "A", "data": "2026-03-12", "int1": "HERIKA LORENE DE ALMEIDA GODOY",       "int2": "",                              "ativos": ["PETR4","VALE3","ITUB4","WEGE3"],      "pesos": [0.25,0.25,0.25,0.25]},
    {"nome": "InvestUltramax",          "turma": "A", "data": "2026-03-04", "int1": "Samuel Dias De Almeida",               "int2": "",                              "ativos": ["PRIO3","SBFG3","KLBN11","SMAL11"],    "pesos": [0.35,0.25,0.25,0.15]},
    {"nome": "JG Investment Partners",  "turma": "A", "data": "2026-03-12", "int1": "Joao Vitor Mendes Umbelino Alves",     "int2": "Gabriel Arthur Harmatiuk",      "ativos": ["GOGL34","NVDC34","VALE3","ROXO34"],   "pesos": [0.25,0.25,0.25,0.25]},
    {"nome": "Joaninha",                "turma": "A", "data": "2026-03-10", "int1": "Maria Eduarda Leichtweis Gomes",       "int2": "",                              "ativos": ["SBSP3","ITUB4","PETR4","SUZB3"],      "pesos": [0.30,0.20,0.15,0.35]},
    {"nome": "João e Lucas",            "turma": "A", "data": "2026-03-02", "int1": "Joao Vitor Gomes Demetino",            "int2": "",                              "ativos": ["ITUB4","BBAS3","PETR4","WEGE3"],      "pesos": [0.35,0.25,0.10,0.30]},
    {"nome": "Juka",                    "turma": "A", "data": "2026-03-12", "int1": "Julia Vanzo Chaves",                   "int2": "Erika Sudou Aguiar",            "ativos": ["BBSE3","BBDC3","SPXI11","WEGE3"],     "pesos": [0.40,0.20,0.25,0.15]},
    {"nome": "LM",                      "turma": "A", "data": "2026-03-10", "int1": "Laura Mello",                          "int2": "",                              "ativos": ["BITH11","ASAI3","XPCI11","ITUB4"],   "pesos": [0.20,0.30,0.30,0.20]},
    {"nome": "Lapa",                    "turma": "A", "data": "2026-03-01", "int1": "Rodrigo Augusto Marques Weiss",        "int2": "",                              "ativos": ["BOVA11","SAPR11","VBBR3","CMIG4"],   "pesos": [0.40,0.20,0.20,0.20]},
    {"nome": "M Contábil",              "turma": "A", "data": "2026-03-12", "int1": "Manitheli Gabriela Da Cruz Da Rocha",  "int2": "",                              "ativos": ["BBAS3","AURE3","HGLG11","IVVB11"],   "pesos": [0.25,0.25,0.25,0.25]},
    {"nome": "Maket",                   "turma": "A", "data": "2026-03-11", "int1": "Ayrton Felipe Prantl Dos Santos",      "int2": "",                              "ativos": ["PETR4","VALE3","IVVB11","XPML11"],   "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "Marsupilâmicos",          "turma": "A", "data": "2026-03-12", "int1": "Joao Vitor Paloschi",                  "int2": "Vinicius Da Silva Nogueira",    "ativos": ["H1AS34","PETR4","LMTB34","EXXO34"],  "pesos": [0.15,0.35,0.20,0.30]},
    {"nome": "Não grita",               "turma": "A", "data": "2026-03-07", "int1": "Erick Miguel Dos Santos",              "int2": "Daniele Caroline Hartmann",     "ativos": ["AURA33","PRIO3","EXXO34","NVDC34"],  "pesos": [0.256,0.316,0.050,0.378]},
    {"nome": "OS FUNDAMENTALISTAS",     "turma": "A", "data": "2026-03-08", "int1": "Daniel Da Rocha Capera",               "int2": "Raquel Auzani Da Silva",        "ativos": ["ITUB4","EGIE3","BPAC11","PETR4"],    "pesos": [0.35,0.15,0.30,0.20]},
    {"nome": "Pam & Kassy",             "turma": "A", "data": "2026-03-11", "int1": "Kassyelle Pawlik",                     "int2": "Pamela Salvi",                  "ativos": ["WEGE3","ITUB4","PETR4","NEOE3"],      "pesos": [0.15,0.30,0.40,0.15]},
    {"nome": "Park the Bus",            "turma": "A", "data": "2026-03-04", "int1": "Josué Rosa Dos Santos",                "int2": "",                              "ativos": ["DIVO11","ITUB4","ABEV3","MXRF11"],   "pesos": [0.40,0.25,0.20,0.15]},
    {"nome": "QM Invest",               "turma": "A", "data": "2026-03-11", "int1": "Bianca Cardoso",                       "int2": "",                              "ativos": ["WEGE3","ITUB4","VALE3","ITSA4"],      "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "Rumovias",                "turma": "A", "data": "2026-03-11", "int1": "Marcelo Mildemberger Mathias",          "int2": "",                              "ativos": ["RAIL3","KLBN11","SUZB3","HBSA3"],    "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "Sabor investimentos",     "turma": "A", "data": "2026-03-03", "int1": "Kayc Mello Cordeiro",                  "int2": "",                              "ativos": ["PETR4","VALE3","EMBJ3","BPAC11"],    "pesos": [0.25,0.30,0.20,0.25]},
    {"nome": "Tabajara Investimentos",  "turma": "A", "data": "2026-03-03", "int1": "Paulo Jose Dos Santos Freitas",        "int2": "Ricardo Alexandre De Souza",    "ativos": ["PETR3","VALE3","WEGE3","ITUB4"],     "pesos": [0.35,0.20,0.25,0.20]},
    {"nome": "Vetor de Soberania",      "turma": "A", "data": "2026-03-11", "int1": "Hebrom Guilherme Duarte De Oliveira",  "int2": "",                              "ativos": ["ITUB4","EMBJ3","SMTO3","TASA3"],     "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "Área 51",                 "turma": "A", "data": "2026-03-12", "int1": "Anna Beatriz G Moreira Garcez",        "int2": "",                              "ativos": ["PRIO3","WEGE3","ITUB4","BBAS3"],     "pesos": [0.40,0.30,0.15,0.15]},
    {"nome": "A & N investimentos",     "turma": "B", "data": "2026-03-12", "int1": "Daniella Alves Dagostin",              "int2": "Daniel Henrique De Souza Nielsen","ativos": ["PETR4","ABEV3","CPLE3","NVDC34"],  "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "AI Engine",               "turma": "B", "data": "2026-03-09", "int1": "Matheus Henrique Martins Do Nascimento","int2": "",                             "ativos": ["WEGE3","TOTS3","B3SA3","ITUB4"],     "pesos": [0.40,0.30,0.20,0.10]},
    {"nome": "Agora vai",               "turma": "B", "data": "2026-03-12", "int1": "Mariana Gomes Dos Santos",             "int2": "Jorge Camilotti Filho",         "ativos": ["BOVA11","IVVB11","HASH11","SOJA3"],  "pesos": [0.35,0.35,0.25,0.05]},
    {"nome": "Arqueiras da B3",         "turma": "B", "data": "2026-03-11", "int1": "Ariely Oliveira Soares",               "int2": "Giovana Cristina Lell Da Silva","ativos": ["ABEV3","ITUB4","VALE3","WEGE3"],      "pesos": [0.25,0.30,0.15,0.30]},
    {"nome": "Astronômico",             "turma": "B", "data": "2026-03-12", "int1": "Bruna Siqueira",                       "int2": "Karine Cardoso Cosmo",          "ativos": ["ITUB4","PETR4","RIAA3","CPFE3"],     "pesos": [0.25,0.25,0.25,0.25]},
    {"nome": "Aurora Quant",            "turma": "B", "data": "2026-03-12", "int1": "Amanda Lucia Ianhaki Da Silva",        "int2": "Noeli Edvirgem Carriel Cordeiro","ativos": ["PRIO3","WEGE3","ITUB4","XPLG11"],   "pesos": [0.35,0.25,0.25,0.15]},
    {"nome": "Azul Navy",               "turma": "B", "data": "2026-03-12", "int1": "Giovanna Mesquita Da Silva",           "int2": "Isabelly Cristine Wenceslau Pereira","ativos": ["PETR4","HGRU11","BOVA11","ITUB4"],"pesos": [0.20,0.10,0.40,0.30]},
    {"nome": "Carreira Solo",           "turma": "B", "data": "2026-03-12", "int1": "Cristiane Aparecida Piezzoti",         "int2": "",                              "ativos": ["ITUB3","WEGE3","BOVA11","NASD11"],   "pesos": [0.45,0.30,0.15,0.10]},
    {"nome": "Carteira Estratégica",    "turma": "B", "data": "2026-03-12", "int1": "Luana Da Silva",                       "int2": "",                              "ativos": ["PETR4","ITUB4","HGLG11","BOVA11"],   "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "Carteira da sorte",       "turma": "B", "data": "2026-03-09", "int1": "Ariane Batista De Almeida Barbosa",   "int2": "",                              "ativos": ["PETR4","ISAE4","BBDC3","SMTO3"],     "pesos": [0.25,0.25,0.25,0.25]},
    {"nome": "Clube do Capital",        "turma": "B", "data": "2026-03-11", "int1": "Eduarda Markiv Gimenes",               "int2": "Ingred Thais Costa Wosch",      "ativos": ["EMBJ3","PETR4","PRIO3","BOVA11"],    "pesos": [0.40,0.25,0.20,0.15]},
    {"nome": "Colorado1909",            "turma": "B", "data": "2026-03-12", "int1": "Diego Machado Postai",                 "int2": "",                              "ativos": ["PETR4","PRIO3","VALE3","LMTB34"],    "pesos": [0.40,0.35,0.15,0.10]},
    {"nome": "Dividend Strategy",       "turma": "B", "data": "2026-03-12", "int1": "Lucas Dos Santos",                     "int2": "",                              "ativos": ["PRIO3","AXIA3","BTLG11","TAEE11"],   "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "Ebenézer Investments",    "turma": "B", "data": "2026-03-02", "int1": "Guilherme Marques Dos Santos",         "int2": "Luana Jacon Halama",            "ativos": ["ITSA4","TAEE4","PRIO3","BOVA11"],    "pesos": [0.30,0.20,0.20,0.30]},
    {"nome": "Em ação",                 "turma": "B", "data": "2026-03-12", "int1": "Emanuele Aparecida Dagort Nascimento", "int2": "Kauanny Stephany Cardoso De Carvalho","ativos": ["NVDC34","PETR4","VALE3","ITUB4"],"pesos": [0.30,0.30,0.20,0.20]},
    {"nome": "Gadonski Capital",        "turma": "B", "data": "2026-03-04", "int1": "Renata Gadonski Ferreira",             "int2": "",                              "ativos": ["NATU3","VALE3","BBDC4","MGLU3"],     "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "Gestão de Ativos",        "turma": "B", "data": "2026-03-12", "int1": "Evelin Aparecida Do Nascimento Macedo","int2": "",                             "ativos": ["NVDC34","WEGE3","MELI34","ITUB4"],   "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "Hedge III Guerra",        "turma": "B", "data": "2026-03-06", "int1": "Maria Fernanda Nascimento Da Silva",   "int2": "",                              "ativos": ["EXXO34","BCHI39","ITUB4","LMTB34"],  "pesos": [0.35,0.25,0.20,0.20]},
    {"nome": "Hello Kitty",             "turma": "B", "data": "2026-03-08", "int1": "Leticia Maria Rudniki",                "int2": "Maria Aparecida Quintiliano",   "ativos": ["PETR4","VALE3","XPML11","IVVB11"],   "pesos": [0.30,0.30,0.20,0.20]},
    {"nome": "INVEST SMILE",            "turma": "B", "data": "2026-03-12", "int1": "Jhonatan Nicolas Costa Dos Santos",   "int2": "",                              "ativos": ["WEGE3","RENT3","SUZB3","IVVB11"],    "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "JM INVEST",               "turma": "B", "data": "2026-03-11", "int1": "Julia Menezes Assolari",              "int2": "Murilo Broto",                  "ativos": ["PETR4","ITUB4","VALE3","WEGE3"],     "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "Ju e Anaju",              "turma": "B", "data": "2026-03-11", "int1": "Ana Júlia Cordeiro Fernandes Rios",   "int2": "Juliana Teofilo Dos Santos",    "ativos": ["WEGE3","ITUB4","VALE3","HGLG11"],    "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "LECRIS",                  "turma": "B", "data": "2026-03-12", "int1": "Cristiane Pereira Sarmento",          "int2": "Leonardo Gabriel Burlikowski De Oliveira","ativos": ["PETR4","BBAS3","SUZB3","CPLE3"],"pesos": [0.30,0.30,0.25,0.15]},
    {"nome": "Lagartixa Day-trader",    "turma": "B", "data": "2026-03-12", "int1": "Anthony Pontes De Melo",              "int2": "Keyla Kauani Martins Da Silva", "ativos": ["ITUB4","AMZO34","PETR4","NVDC34"],   "pesos": [0.20,0.25,0.30,0.25]},
    {"nome": "Malves",                  "turma": "B", "data": "2026-03-11", "int1": "Maria Eduarda Goncalves Da Silva",    "int2": "Leticia Taina Marques Pereira", "ativos": ["VALE3","RADL3","EQTL3","ABEV3"],     "pesos": [0.25,0.25,0.25,0.25]},
    {"nome": "Mielniczki SA.",          "turma": "B", "data": "2026-03-12", "int1": "Roger Dos Santos Mielniczki",         "int2": "",                              "ativos": ["ITUB4","IVVB11","HGLG11","VALE3"],   "pesos": [0.40,0.20,0.20,0.20]},
    {"nome": "Multisetorial",           "turma": "B", "data": "2026-03-08", "int1": "Daniella Aparecida Quandt",           "int2": "",                              "ativos": ["ITUB4","CPFE3","SAPR11","INTB3"],    "pesos": [0.30,0.20,0.40,0.10]},
    {"nome": "Outsider Trader",         "turma": "B", "data": "2026-03-12", "int1": "Arthur Fernandes Moysa",              "int2": "",                              "ativos": ["CXSE3","BBDC3","SAPR4","TIMS3"],     "pesos": [0.20,0.25,0.30,0.25]},
    {"nome": "Pierri",                  "turma": "B", "data": "2026-03-12", "int1": "Nicoly Ferreira Pierri",              "int2": "",                              "ativos": ["PETR4","ITUB4","WEGE3","BOVA11"],    "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "Power Rangers",           "turma": "B", "data": "2026-03-12", "int1": "Jessica De Sousa Ramos",              "int2": "Marina Padilha Rodrigues",      "ativos": ["PETR4","ITSA4","RADL3","SAPR11"],    "pesos": [0.30,0.25,0.25,0.20]},
    {"nome": "RevOp",                   "turma": "B", "data": "2026-03-06", "int1": "Vinicius Dutra Santana",              "int2": "",                              "ativos": ["CPLE3","PETR4","BPAC11","WEGE3"],    "pesos": [0.20,0.30,0.25,0.25]},
    {"nome": "WARHEAD BULLS",           "turma": "B", "data": "2026-03-11", "int1": "Lucas Manduca Kreuka",                "int2": "Ana Clara Miranda",             "ativos": ["EXXO34","NVDC34","LMTB34","GOLD11"], "pesos": [0.35,0.30,0.20,0.15]},
    {"nome": "xx",                      "turma": "B", "data": "2026-03-11", "int1": "Matheus Moro Pietrzak",               "int2": "",                              "ativos": ["EXXO34","LMTB34","JNJB34","N1EM34"], "pesos": [0.35,0.25,0.15,0.25]},
]

# ── Funções de dados ────────────────────────────────────────────────────

@st.cache_data(ttl=timedelta(minutes=30), show_spinner=False)
def _buscar_preco_historico(ticker: str, data_ref: str):
    """Preço de fechamento na data de início da equipe."""
    yt = ticker.upper() + ".SA"
    dt = datetime.strptime(data_ref, "%Y-%m-%d")
    for delta in range(0, 12):
        d0 = (dt - timedelta(days=delta)).strftime("%Y-%m-%d")
        d1 = (dt - timedelta(days=delta) + timedelta(days=2)).strftime("%Y-%m-%d")
        try:
            tick = yf.Ticker(yt)
            hist = tick.history(start=d0, end=d1, auto_adjust=True)
            if not hist.empty:
                return _safe(float(hist["Close"].iloc[-1]))
        except Exception:
            pass
        time.sleep(0.1)
    return None


@st.cache_data(ttl=timedelta(minutes=30), show_spinner=False)
def _buscar_preco_atual(ticker: str):
    """Último preço de fechamento disponível."""
    yt = ticker.upper() + ".SA"
    try:
        tick = yf.Ticker(yt)
        hist = tick.history(period="5d", auto_adjust=True)
        if not hist.empty:
            return _safe(float(hist["Close"].iloc[-1]))
    except Exception:
        pass
    return None


@st.cache_data(ttl=timedelta(minutes=60), show_spinner=False)
def _buscar_cdi(data_inicio: str) -> float | None:
    """CDI acumulado desde data_inicio via API BCB."""
    url = (
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
        f"?formato=json"
        f"&dataInicial={datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')}"
        f"&dataFinal={datetime.today().strftime('%d/%m/%Y')}"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        dados = resp.json()
        if not dados:
            return None
        fator = 1.0
        for d in dados:
            fator *= (1 + float(d["valor"].replace(",", ".")) / 100)
        return (fator - 1) * 100
    except Exception:
        return None


@st.cache_data(ttl=timedelta(minutes=30), show_spinner=False)
def calcular_ranking() -> list[dict]:
    """Calcula retorno de todas as equipes. Cache de 30 min."""
    resultado = []
    for eq in EQUIPES:
        total_investido = 0.0
        total_atual = 0.0
        ativos_detalhe = []

        for ticker, peso in zip(eq["ativos"], eq["pesos"]):
            valor_aloc = INVESTIMENTO_INICIAL * peso
            p_ini = _buscar_preco_historico(ticker, eq["data"])
            p_atu = _buscar_preco_atual(ticker)

            qtd = valor_aloc / p_ini if (p_ini and p_ini > 0) else 0.0
            v_atu = qtd * p_atu if (p_atu and qtd) else None
            ret_pct = (v_atu / valor_aloc - 1) * 100 if v_atu else None

            ativos_detalhe.append({
                "ticker": ticker,
                "peso": peso,
                "valor_aloc": valor_aloc,
                "preco_ini": p_ini,
                "qtd": qtd,
                "preco_atual": p_atu,
                "valor_atual": v_atu,
                "retorno_pct": ret_pct,
            })
            total_investido += valor_aloc
            if v_atu:
                total_atual += v_atu

        ret_total_pct = (total_atual / total_investido - 1) * 100 if total_atual else None
        cdi = _buscar_cdi(eq["data"])
        alpha = (ret_total_pct - cdi) if (ret_total_pct is not None and cdi is not None) else None

        resultado.append({
            "nome": eq["nome"],
            "turma": eq["turma"],
            "data_base": eq["data"],
            "integrantes": ", ".join(i for i in [eq["int1"], eq["int2"]] if i),
            "total_investido": total_investido,
            "total_atual": total_atual,
            "retorno_rs": total_atual - total_investido if total_atual else None,
            "retorno_pct": ret_total_pct,
            "cdi_pct": cdi,
            "alpha_pct": alpha,
            "ativos": ativos_detalhe,
        })

    resultado.sort(key=lambda x: x["alpha_pct"] if x["alpha_pct"] is not None else -999, reverse=True)
    return resultado


# ── Interface ──────────────────────────────────────────────────────────

st.markdown("""
<style>
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 16px 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .metric-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 1.6rem; font-weight: 800; color: #1e3a5f; margin-top: 4px; }
    .pos-1 { color: #d4a017 !important; }
    .pos-2 { color: #8c8c8c !important; }
    .pos-3 { color: #b87333 !important; }
    div[data-testid="stExpander"] { border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

# Cabeçalho
col_title, col_update = st.columns([4, 1])
with col_title:
    st.markdown("## 📊 Competição de Carteiras UFPR 2026")
    st.caption("Mercado Financeiro e de Capitais — Prof. Claudio Marcelo Edwards Barros")
with col_update:
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Cache: 30 min · Agora: {datetime.now().strftime('%H:%M')}")

st.divider()

# Carrega dados
with st.spinner("Buscando cotações via Yahoo Finance..."):
    dados = calcular_ranking()

hora_atualizacao = datetime.now().strftime("%d/%m/%Y %H:%M")

# Resumo geral
total_equipes = len(dados)
total_investido_geral = sum(d["total_investido"] for d in dados)
total_atual_geral = sum(
    d["total_atual"] for d in dados
    if d["total_atual"] and math.isfinite(d["total_atual"]) and d["total_atual"] > 0
)
ret_geral_pct = (
    (total_atual_geral / total_investido_geral - 1) * 100
    if total_atual_geral and total_investido_geral else None
)

lider = dados[0] if dados else None

cols = st.columns(5)
with cols[0]:
    st.metric("Equipes", f"{total_equipes}")
with cols[1]:
    st.metric("Capital total", f"R$ {total_investido_geral/1e6:.2f}M")
with cols[2]:
    st.metric("Valor atual", f"R$ {total_atual_geral/1e6:.3f}M" if (total_atual_geral and total_atual_geral > 0) else "—")
with cols[3]:
    st.metric("Retorno geral", f"{ret_geral_pct:+.2f}%" if (ret_geral_pct is not None) else "—")
with cols[4]:
    if lider:
        st.metric("Líder atual", lider["nome"], f"{lider['alpha_pct']:+.2f}% alpha" if lider["alpha_pct"] else "")

st.divider()

# Filtros
col_f1, col_f2, col_f3 = st.columns([1, 1, 3])
with col_f1:
    filtro_turma = st.selectbox("Turma", ["Todas", "A", "B"])
with col_f2:
    ordenar_por = st.selectbox("Ordenar por", ["Alpha s/ CDI", "Retorno (%)", "Retorno (R$)"])
with col_f3:
    busca = st.text_input("Buscar equipe", placeholder="Nome da equipe ou integrante...")

# Filtra e ordena
df_dados = dados.copy()
if filtro_turma != "Todas":
    df_dados = [d for d in df_dados if d["turma"] == filtro_turma]
if busca:
    busca_lower = busca.lower()
    df_dados = [d for d in df_dados if busca_lower in d["nome"].lower() or busca_lower in d["integrantes"].lower()]

key_ord = {
    "Alpha s/ CDI": lambda x: x["alpha_pct"] if x["alpha_pct"] is not None else -999,
    "Retorno (%)":  lambda x: x["retorno_pct"] if x["retorno_pct"] is not None else -999,
    "Retorno (R$)": lambda x: x["retorno_rs"] if x["retorno_rs"] is not None else -999,
}
df_dados.sort(key=key_ord[ordenar_por], reverse=True)

# ── Tabela de ranking ──────────────────────────────────────────────────
st.markdown("### 🏆 Ranking")

medalhas = {0: "🥇", 1: "🥈", 2: "🥉"}

for i, d in enumerate(df_dados):
    pos_global = dados.index(d) + 1
    icon = medalhas.get(i, f"**{i+1}º**")

    ret_cor = "green" if (d["retorno_pct"] or 0) >= 0 else "red"
    alpha_cor = "green" if (d["alpha_pct"] or 0) >= 0 else "red"

    ret_str   = f"{d['retorno_pct']:+.2f}%" if d["retorno_pct"] is not None else "—"
    alpha_str = f"{d['alpha_pct']:+.2f}%" if d["alpha_pct"] is not None else "—"
    cdi_str   = f"{d['cdi_pct']:.2f}%" if d["cdi_pct"] is not None else "—"
    val_str   = f"R$ {d['total_atual']:,.2f}" if d["total_atual"] else "—"
    ret_rs_str = f"R$ {d['retorno_rs']:+,.2f}" if d["retorno_rs"] is not None else "—"

    label = f"{icon}  {d['nome']}  [Turma {d['turma']}]   Retorno: {ret_str}  |  Alpha: {alpha_str}  |  CDI: {cdi_str}  |  {val_str}"

    with st.expander(label, expanded=False):
        st.caption(f"Integrantes: {d['integrantes']} | Data base: {datetime.strptime(d['data_base'], '%Y-%m-%d').strftime('%d/%m/%Y')}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Investimento", f"R$ {d['total_investido']:,.2f}")
        c2.metric("Valor atual", f"R$ {d['total_atual']:,.2f}" if d['total_atual'] else "—")
        c3.metric("Retorno", ret_str, delta=None)
        c4.metric("Alpha s/ CDI", alpha_str)

        ativos_df = pd.DataFrame(d["ativos"])
        if not ativos_df.empty:
            ativos_df["peso"] = ativos_df["peso"].map(lambda x: f"{x:.0%}")
            ativos_df["valor_aloc"] = ativos_df["valor_aloc"].map(lambda x: f"R$ {x:,.2f}")
            ativos_df["preco_ini"] = ativos_df["preco_ini"].map(lambda x: f"R$ {x:.4f}" if x else "—")
            ativos_df["preco_atual"] = ativos_df["preco_atual"].map(lambda x: f"R$ {x:.4f}" if x else "—")
            ativos_df["valor_atual"] = ativos_df["valor_atual"].map(lambda x: f"R$ {x:,.2f}" if x else "—")
            ativos_df["retorno_pct"] = ativos_df["retorno_pct"].map(lambda x: f"{x:+.2f}%" if x is not None else "—")
            ativos_df.columns = ["Ticker","Peso","Valor Alocado","Preço Base","Qtd","Preço Atual","Valor Atual","Retorno"]
            st.dataframe(ativos_df[["Ticker","Peso","Valor Alocado","Preço Base","Qtd","Preço Atual","Valor Atual","Retorno"]],
                        hide_index=True, use_container_width=True)

# ── Gráfico de barras ──────────────────────────────────────────────────
st.divider()
st.markdown("### 📈 Retorno por equipe (Alpha s/ CDI)")

nomes  = [d["nome"] for d in df_dados if d["alpha_pct"] is not None]
alphas = [d["alpha_pct"] for d in df_dados if d["alpha_pct"] is not None]
turmas = [d["turma"] for d in df_dados if d["alpha_pct"] is not None]
cores  = ["#22c55e" if a >= 0 else "#ef4444" for a in alphas]

if nomes:
    fig = go.Figure(go.Bar(
        x=nomes, y=alphas,
        marker_color=cores,
        text=[f"{a:+.2f}%" for a in alphas],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Alpha: %{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        height=420,
        xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
        yaxis=dict(title="Alpha (%)", zeroline=True, zerolinecolor="#94a3b8"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=20, b=120),
        font=dict(family="Arial"),
    )
    fig.add_hline(y=0, line_color="#94a3b8", line_width=1)
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption(
    f"Atualizado em {hora_atualizacao} · Preços via Yahoo Finance · "
    f"CDI via API Banco Central · Cache de 30 minutos"
)
