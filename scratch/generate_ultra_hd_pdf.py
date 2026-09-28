#!/usr/bin/env python3
"""
Gera o PDF unificado (Diagrama Metodológico de Alta Resolução + Sumário Canônico)
com fontes Liberation do sistema em densidade de 514 DPI.
"""
from pathlib import Path
from fpdf import FPDF

VAULT_DIR = Path("/home/arosisca/Documents/vaults/agy-vault/30_Resources/TCC_URBS")
OUT_PDF = VAULT_DIR / "Diagrama_e_Sumario_TCC_v2.pdf"
DIAGRAM_PNG = VAULT_DIR / "Diagrama_Metodologico_TCC.png"

pdf = FPDF(format='A4')
pdf.set_auto_page_break(False)

# Fontes do sistema
pdf.add_font('LiberationSans', '', '/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf')
pdf.add_font('LiberationSans', 'B', '/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf')
pdf.add_font('LiberationSans', 'I', '/usr/share/fonts/liberation-sans-fonts/LiberationSans-Italic.ttf')
pdf.add_font('LiberationMono', '', '/usr/share/fonts/liberation-mono-fonts/LiberationMono-Regular.ttf')
pdf.add_font('LiberationMono', 'B', '/usr/share/fonts/liberation-mono-fonts/LiberationMono-Bold.ttf')

# ----------------- PÁGINA 1: DIAGRAMA METODOLÓGICO -----------------
pdf.add_page()
pdf.set_margins(15, 14, 15)
pdf.set_xy(15, 14)

pdf.set_font('LiberationSans', 'B', 9.5)
pdf.set_text_color(68, 68, 68)
pdf.cell(180, 5, 'UNIVERSIDADE TECNOLÓGICA FEDERAL DO PARANÁ — UTFPR', align='C', new_x='LMARGIN', new_y='NEXT')

pdf.set_font('LiberationSans', 'B', 13)
pdf.set_text_color(17, 17, 17)
pdf.cell(180, 7, 'Diagrama Metodológico de Ponta a Ponta', align='C', new_x='LMARGIN', new_y='NEXT')

pdf.set_font('LiberationSans', 'I', 8.5)
pdf.set_text_color(85, 85, 85)
pdf.cell(180, 5, 'Pipeline de Engenharia de Dados, Mineração de Processos e Auditoria Operacional (URBS)', align='C', new_x='LMARGIN', new_y='NEXT')

pdf.set_draw_color(34, 34, 34)
pdf.set_line_width(0.5)
pdf.line(15, pdf.get_y() + 2, 195, pdf.get_y() + 2)

pdf.set_y(pdf.get_y() + 5)

# Insere o diagrama em ultra-alta resolução (3646 x 3279 px)
# Largura 180mm x Altura 161.88mm -> ~514 DPI efetivos
img_y = pdf.get_y()
pdf.image(str(DIAGRAM_PNG), x=15, y=img_y, w=180, h=161.88)

pdf.set_y(img_y + 163.5)
pdf.set_font('LiberationSans', 'I', 8)
pdf.set_text_color(102, 102, 102)
pdf.cell(180, 4.5, 'Figura 1 — Arquitetura de ponta a ponta: Da obtenção dos dados à auditoria em tempo real no CCO.', align='C', new_x='LMARGIN', new_y='NEXT')

pdf.set_y(282)
pdf.set_draw_color(220, 220, 220)
pdf.set_line_width(0.2)
pdf.line(40, 281, 170, 281)
pdf.set_font('LiberationSans', '', 7.5)
pdf.set_text_color(119, 119, 119)
pdf.cell(180, 4, 'Documento oficial de referência do projeto tcc-urbs — Curitiba, 2026.', align='C', new_x='LMARGIN', new_y='NEXT')

# ----------------- PÁGINA 2: SUMÁRIO CANÔNICO -----------------
pdf.add_page()
pdf.set_xy(15, 14)

pdf.set_font('LiberationSans', 'B', 12)
pdf.set_text_color(17, 17, 17)
pdf.cell(180, 8, 'SUMÁRIO', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.ln(3)

toc_text = '''1 INTRODUÇÃO .................................................................... 15
  1.1 OBJETIVOS ................................................................. 17
      1.1.1 Objetivo Geral ...................................................... 17
      1.1.2 Objetivos Específicos ............................................... 17
  1.2 JUSTIFICATIVA ............................................................. 18
  1.3 ESTRUTURA DO TRABALHO ..................................................... 20

2 FUNDAMENTAÇÃO TEÓRICA E REVISÃO DA LITERATURA ................................. 21
  2.1 CONCEITOS FUNDAMENTAIS DA MINERAÇÃO DE PROCESSOS ........................... 21
      2.1.1 Os Três Pilares: Descoberta, Conformidade e Desempenho .............. 22
      2.1.2 Algoritmos de Descoberta: Alpha Miner e Inductive Miner ............. 23
      2.1.3 Ferramentas para Mineração de Processos: ProM e PM4Py ............... 25
  2.2 ANÁLISE DE DADOS EM TRANSPORTE PÚBLICO: CONCEITOS E TÉCNICAS ............... 26
      2.2.1 Mobilidade Urbana e Dados de GPS .................................... 26
      2.2.2 APIs de Transporte Público como Fonte de Dados ...................... 28
      2.2.3 Reconstrução de Trajetórias: Map Matching e Interpolação ............ 29
  2.3 TRABALHOS RELACIONADOS .................................................... 31
      2.3.1 Aplicações de Mineração de Processos ................................ 31
      2.3.2 Análise de Dados de Transporte Urbano ............................... 32
      2.3.3 Interseção: Mineração de Processos Aplicada ao Transporte ........... 33
  2.4 SÍNTESE DO CAPÍTULO ....................................................... 35

3 METODOLOGIA E ENGENHARIA DE DADOS ............................................. 37
  3.1 VISÃO GERAL DA ARQUITETURA DA SOLUÇÃO ..................................... 37
  3.2 OBTENÇÃO E ACESSO AOS DADOS DA API DA URBS ................................ 39
  3.3 PROTOCOLO DE COLETA CONTÍNUA E REGIMES OPERACIONAIS (REGIMES A E B) ........ 41
  3.4 PRÉ-PROCESSAMENTO E FILTRAGEM COM RESTRIÇÃO NA MALHA VIÁRIA (SHAPE) ....... 44
  3.5 RECONSTRUÇÃO DE TRAJETÓRIAS E GERAÇÃO DO LOG DE EVENTOS ................... 47
      3.5.1 Segmentação Semântica de Viagens (Cases) ............................ 47
      3.5.2 Projeção Espacial HMM/Viterbi sobre o Traçado Físico ................ 49
      3.5.3 Estimação Temporal Monotônica via PCHIP e Limiar de Geocerca (150m) . 52
      3.5.4 Padronização com Chaves Canônicas e Incerteza de Sensoriamento ...... 55
      3.5.5 Mecanismo de Qualidade e Taxa de Censura Operacional ................ 57
  3.6 ESTRUTURAÇÃO E EXPORTAÇÃO DO LOG DE EVENTOS (PADRÃO IEEE 1849 / OPENXES) .. 59
  3.7 ARQUITETURA DA PLATAFORMA INTEGRADA DE AUDITORIA OPERACIONAL (FASTAPI E CCO) 62
  3.8 PROTOCOLO DE VALIDAÇÃO E SUÍTE DE TESTES AUTOMATIZADOS (89 TESTES) ........ 66

4 RESULTADOS E DISCUSSÃO ........................................................ 69
  4.1 CARACTERIZAÇÃO DOS DATASETS OPERACIONAIS DA URBS .......................... 69
  4.2 AVALIAÇÃO DO IMPACTO DA CADÊNCIA DE AMOSTRAGEM (REGIME A VS. REGIME B) .... 72
  4.3 DESCOBERTA DE PROCESSOS: IDENTIFICAÇÃO DOS MODELOS REAIS DE OPERAÇÃO ...... 75
  4.4 VERIFICAÇÃO DE CONFORMIDADE: QUANTIFICAÇÃO DE DESVIOS E PARADAS OMITIDAS .. 79
  4.5 ANÁLISE DE DESEMPENHO: MAPEAMENTO DE GARGALOS OPERACIONAIS NO DFG ......... 84
  4.6 PLATAFORMA DE AUDITORIA OPERACIONAL NO CCO E REPLAY ESPAÇOTEMPORAL ....... 89
  4.7 DISCUSSÃO DOS RESULTADOS E IMPACTOS NA FISCALIZAÇÃO DO TRANSPORTE ......... 94

5 CONSIDERAÇÕES FINAIS E CONCLUSÕES ............................................. 98
  5.1 SÍNTESE DAS CONTRIBUIÇÕES CIENTÍFICAS E METODOLÓGICAS ..................... 98
  5.2 CONTRIBUIÇÕES PRÁTICAS PARA A GESTÃO DO TRANSPORTE PÚBLICO DE CURITIBA .... 100
  5.3 LIMITAÇÕES METODOLÓGICAS DO TRABALHO ...................................... 102
  5.4 RECOMENDAÇÕES E TRABALHOS FUTUROS ......................................... 104

REFERÊNCIAS ..................................................................... 107'''

pdf.set_font('LiberationMono', '', 8.3)
pdf.set_text_color(17, 17, 17)

for line in toc_text.split('\n'):
    if line.strip():
        if line and line[0] in '12345' and ' ' in line and line.split()[0].isdigit():
            pdf.set_font('LiberationMono', 'B', 8.3)
        elif line.startswith('REFERÊNCIAS'):
            pdf.set_font('LiberationMono', 'B', 8.3)
        else:
            pdf.set_font('LiberationMono', '', 8.3)
        pdf.cell(180, 4.4, line, new_x='LMARGIN', new_y='NEXT')
    else:
        pdf.ln(2.2)

pdf.set_y(282)
pdf.set_draw_color(220, 220, 220)
pdf.set_line_width(0.2)
pdf.line(40, 281, 170, 281)
pdf.set_font('LiberationSans', '', 7.5)
pdf.set_text_color(119, 119, 119)
pdf.cell(180, 4, 'Documento oficial de referência do projeto tcc-urbs — Curitiba, 2026.', align='C', new_x='LMARGIN', new_y='NEXT')

pdf.output(str(OUT_PDF))
print(f"PDF gerado com sucesso em: {OUT_PDF}")
