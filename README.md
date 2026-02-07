# Quantos dias o mar "fecha" na costa do RJ?

Dashboard interativo que analisa dados meteorológicos reais do INMET (2019-2024) para estimar quantos dias por ano as condições climáticas impedem operações offshore na costa do Rio de Janeiro.

**[Acessar o dashboard](https://offshore-weather-downtime.streamlit.app)**

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red)
![License](https://img.shields.io/badge/License-MIT-green)

## Por que isso importa?

A costa do RJ concentra boa parte da operação offshore brasileira (Bacia de Campos, Bacia de Santos). Operações como içamento com guindaste, transferência de pessoal e mergulho de saturação dependem de janelas de bom tempo. Quando o vento ou a chuva passam dos limites operacionais, a operação para.

Esse projeto usa dados horários de 6 estações meteorológicas costeiras do INMET para responder:
- Quantos dias por ano cada tipo de operação fica parado?
- Quais meses são mais críticos?
- Qual trecho da costa é mais afetado?
- O downtime está aumentando ao longo dos anos?

## Estações analisadas

| Código | Local | Latitude | Longitude |
|--------|-------|----------|-----------|
| A602 | Marambaia | -23.05 | -43.59 |
| A606 | Arraial do Cabo | -22.97 | -42.02 |
| A608 | Macaé | -22.39 | -41.78 |
| A620 | São Tomé (Campos) | -21.75 | -41.05 |
| A627 | Niterói | -22.90 | -43.10 |
| A652 | Forte de Copacabana | -22.99 | -43.19 |

## Limites operacionais

Baseados em NORMAM-01, Noble Denton Guidelines e padrões da indústria:

| Operação | Vento sustentado | Rajada | Chuva |
|----------|-----------------|--------|-------|
| Içamento com guindaste | 25 kt (12.9 m/s) | 30 kt (15.4 m/s) | 10 mm/h |
| Transferência de pessoal | 20 kt (10.3 m/s) | 25 kt (12.9 m/s) | 10 mm/h |
| Mergulho (saturação) | 20 kt (10.3 m/s) | 25 kt (12.9 m/s) | 5 mm/h |
| Operações gerais no convés | 30 kt (15.4 m/s) | 40 kt (20.6 m/s) | 20 mm/h |

Um dia conta como "downtime" quando pelo menos 4 horas excederam os limites.

## Como rodar localmente

```bash
# Clonar o repositório
git clone https://github.com/Furiatii/offshore-weather-downtime.git
cd offshore-weather-downtime

# Instalar dependências
pip install -r requirements.txt

# Baixar dados do INMET (2019-2023)
python scripts/fetch_inmet.py

# Rodar o dashboard
streamlit run app.py
```

## Stack

- **Python** + **pandas** para processamento de dados
- **Streamlit** para o dashboard interativo
- **Plotly** para visualizações
- **INMET** como fonte de dados meteorológicos

## Estrutura

```
├── app.py                  # Dashboard Streamlit
├── analysis/
│   ├── processor.py        # Parser de CSV do INMET
│   └── thresholds.py       # Limites operacionais e classificação
├── scripts/
│   └── fetch_inmet.py      # Script de download dos dados
├── data/                   # CSVs das estações (não versionado)
├── .streamlit/
│   └── config.toml         # Tema do Streamlit
└── requirements.txt
```

## Licença

MIT
