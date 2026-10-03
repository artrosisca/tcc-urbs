# Coletor de dados da URBS (Windows)

Este coletor grava a telemetria dos veiculos da URBS a cada 20 segundos.
Os dados ficam na pasta `dados_em_tempo_real_2026` ao lado deste arquivo,
organizados por dia e hora.

## Como usar no Windows 10

1. Instale o Python 3 (https://www.python.org/downloads/). Na instalacao,
   marque a opcao **"Add Python to PATH"**.
2. Baixe a pasta `coletor` deste repositorio.
3. Clique duas vezes em **`executar_coletor.bat`**.
4. Deixe a janela aberta. Para parar, aperte **CTRL+C**.

O arquivo `.bat` instala as dependencias e desativa a suspensao do Windows
enquanto coleta.

## O que observar

- A pasta `dados_em_tempo_real_2026/AAAA-MM-DD/` deve crescer a cada hora.
- Se a internet cair, o coletor continua sozinho e volta a gravar quando a
  conexao retornar.
- Deixe o computador ligado **na tomada**.

## Importante

- Nao feche a janela do coletor.
- Ao terminar a coleta, compacte a pasta `dados_em_tempo_real_2026`
  (Ex.: zip) para transferir os dados.
