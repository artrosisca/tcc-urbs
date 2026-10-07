# Coletor de dados da URBS (Windows)

Este coletor grava a telemetria dos veiculos da URBS a cada 20 segundos.
Os dados ficam organizados por dia e hora, em arquivos CSV.

## Como usar no Windows 10

1. Instale o Python 3 (https://www.python.org/downloads/). Na instalacao,
   marque a opcao **"Add Python to PATH"**.
2. Baixe a pasta `coletor` deste repositorio.
3. Clique duas vezes em **`executar_coletor.bat`**.
4. Deixe a janela aberta. Para parar, aperte **CTRL+C**.

O arquivo `.bat` instala as dependencias e desativa a suspensao do Windows.

## Onde os dados ficam

Por padrao, na pasta `dados_em_tempo_real_2026` ao lado do script:

```
coletor\dados_em_tempo_real_2026\AAAA-MM-DD\AAAA-MM-DD_HH-00.csv
```

## Enviar automaticamente para o Google Drive

O jeito mais simples e usar o **Google Drive para Desktop**:

1. Instale o Google Drive para Desktop e faca login.
2. Escolha a opcao **"Espelhar arquivos"** (assim existe uma pasta local).
3. Abra `coletor_urbs.py` e mude a linha da configuracao, por exemplo:
   ```python
   PASTA_SAIDA_CONFIGURADA = r"C:\Users\SEU_USUARIO\My Drive\tcc_dados"
   ```
4. Salve, feche a janela atual do coletor (CTRL+C) e rode o `.bat` de novo.

A partir dai, os arquivos vao para dentro do Drive e sobem sozinhos.

Alternativa (mais tecnica): instalar o **rclone**, configurar o Google Drive e
agendar uma tarefa no Windows que roda de 15 em 15 minutos:
```
rclone sync C:\caminho\coletor\dados_em_tempo_real_2026 gdrive:tcc_dados
```

## Importante

- Nao feche a janela do coletor e deixe o computador ligado na tomada.
- Ao terminar, compacte a pasta dos dados (zip) para transferir.
