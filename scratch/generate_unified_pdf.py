import subprocess
import os

# Save the diagram PNG to a clean asset path in the vault
vault_dir = "/home/arosisca/Documents/vaults/agy-vault/30_Resources/TCC_URBS"
os.makedirs(vault_dir, exist_ok=True)
diagram_png_path = os.path.join(vault_dir, "Diagrama_Metodologico_TCC.png")
subprocess.run(["cp", "/tmp/compact_diagram.png", diagram_png_path], check=True)

html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4;
    margin: 2.0cm 1.8cm 1.8cm 1.8cm;
  }}
  body {{
    font-family: "Liberation Sans", Arial, sans-serif;
    color: #111;
    line-height: 1.35;
  }}
  .header-box {{
    text-align: center;
    border-bottom: 2px solid #222;
    padding-bottom: 6px;
    margin-bottom: 12px;
  }}
  .header-box .institution {{
    font-size: 9.5pt;
    font-weight: bold;
    color: #444;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .header-box h1 {{
    font-size: 13pt;
    font-weight: 800;
    text-transform: uppercase;
    margin: 5px 0 2px 0;
    color: #111;
  }}
  .header-box .subtitle {{
    font-size: 9pt;
    color: #555;
    font-style: italic;
  }}
  .diagram-container {{
    text-align: center;
    margin-top: 8px;
    margin-bottom: 10px;
  }}
  .diagram-img {{
    max-width: 98%;
    max-height: 22.5cm;
    height: auto;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }}
  .diagram-caption {{
    font-size: 8pt;
    color: #666;
    margin-top: 6px;
    font-style: italic;
  }}
  .page-break {{
    page-break-before: always;
  }}
  .context-callout {{
    background-color: #f8f9fa;
    border-left: 3px solid #0056b3;
    padding: 7px 12px;
    margin-bottom: 12px;
    font-size: 8.5pt;
    line-height: 1.35;
    color: #333;
  }}
  .context-callout strong {{
    color: #0056b3;
  }}
  .section-title {{
    font-size: 10.5pt;
    font-weight: bold;
    text-transform: uppercase;
    color: #111;
    border-bottom: 1px solid #ddd;
    padding-bottom: 3px;
    margin-top: 10px;
    margin-bottom: 8px;
  }}
  pre.toc {{
    font-family: "Liberation Mono", "Courier New", Courier, monospace;
    font-size: 8.5pt;
    line-height: 1.38;
    white-space: pre;
    color: #111;
    margin: 0;
    padding: 0;
  }}
  table.comp-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
    margin-bottom: 12px;
    font-size: 8.5pt;
  }}
  table.comp-table th, table.comp-table td {{
    border: 1px solid #999 !important;
    padding: 6px 10px;
    text-align: left;
    vertical-align: top;
  }}
  table.comp-table th {{
    background-color: #f1f3f5;
    font-weight: bold;
    color: #111;
  }}
  .footer-note {{
    font-size: 8pt;
    color: #777;
    text-align: center;
    margin-top: 12px;
    border-top: 1px solid #eee;
    padding-top: 6px;
  }}
</style>
</head>
<body>

  <!-- PÁGINA 1: DIAGRAMA METODOLÓGICO -->
  <div class="header-box">
    <div class="institution">Universidade Tecnológica Federal do Paraná — UTFPR</div>
    <h1>Diagrama Metodológico de Ponta a Ponta</h1>
    <div class="subtitle">Pipeline de Engenharia de Dados, Mineração de Processos e Auditoria Operacional (URBS)</div>
  </div>

  <div class="diagram-container">
    <img src="{diagram_png_path}" class="diagram-img" alt="Diagrama Metodológico Completo">
    <div class="diagram-caption">Figura 1 — Arquitetura de ponta a ponta: Da obtenção dos dados à auditoria em tempo real no CCO.</div>
  </div>

  <div class="footer-note">
    Documento oficial de referência do projeto <em>tcc-urbs</em> — Curitiba, 2026.
  </div>

  <!-- PÁGINA 2 E 3: SUMÁRIO CANÔNICO -->
  <div class="page-break"></div>

  <div class="header-box">
    <div class="institution">Universidade Tecnológica Federal do Paraná — UTFPR</div>
    <h1>Sumário — Trabalho de Conclusão de Curso (TCC)</h1>
    <div class="subtitle">Versão 2: Estrutura Canônica Equilibrada e Alinhada ao Diagrama Metodológico</div>
  </div>

  <div class="context-callout">
    <strong>Sintonia entre Diagrama e Sumário:</strong> Cada uma das 5 etapas do diagrama acima corresponde diretamente às seções canônicas deste sumário, preservando a redação consolidada dos Capítulos 1 e 2 e detalhando o rigor técnico nos Capítulos 3, 4 e 5.
  </div>

  <div class="section-title">Estrutura do Sumário (Normas ABNT / UTFPR)</div>

  <pre class="toc">1 INTRODUÇÃO .................................................................... 15
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

REFERÊNCIAS ..................................................................... 107</pre>

  <div class="section-title">Quadro Comparativo Estratégico</div>

  <table class="comp-table" border="1" cellpadding="6" cellspacing="0">
    <thead>
      <tr>
        <th style="width: 25%;">Critério</th>
        <th style="width: 37%;">Versão 1 (Inflada / Teórica)</th>
        <th style="width: 38%;">Versão 2 (Equilibrada / Alinhada)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Capítulos 1 e 2</strong></td>
        <td>15 subseções extras com fórmulas puras de HMM e Markov.</td>
        <td>Reutiliza 95% do texto pronto, atualizando apenas 2.2.3.</td>
      </tr>
      <tr>
        <td><strong>Esforço de Escrita</strong></td>
        <td>Exigiria redigir ~15 páginas extras de pura teoria.</td>
        <td>Zero retrabalho: foco na defesa dos resultados reais.</td>
      </tr>
      <tr>
        <td><strong>Segurança na Banca</strong></td>
        <td>Arriscado: atrai cobranças sobre matemática abstrata.</td>
        <td>Blindado: a banca avalia a engenharia, testes e dados.</td>
      </tr>
      <tr>
        <td><strong>Capítulos 3, 4 e 5</strong></td>
        <td>Profundo e detalhado.</td>
        <td>Igualmente profundo: HMM/Viterbi, PCHIP, CCO e testes.</td>
      </tr>
    </tbody>
  </table>

  <div class="footer-note">
    Documento oficial de referência do projeto <em>tcc-urbs</em> — Curitiba, 2026.
  </div>

</body>
</html>
"""

tmp_html = "/tmp/diagrama_e_sumario_unificado.html"
with open(tmp_html, "w", encoding="utf-8") as f:
    f.write(html_content)

subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", tmp_html, "--outdir", vault_dir], check=True)

src_pdf = os.path.join(vault_dir, "diagrama_e_sumario_unificado.pdf")
dst_pdf = os.path.join(vault_dir, "Diagrama_e_Sumario_TCC_v2.pdf")
if os.path.exists(src_pdf):
    if os.path.exists(dst_pdf):
        os.remove(dst_pdf)
    os.rename(src_pdf, dst_pdf)

print("PDF unificado gerado e salvo em:", dst_pdf)
