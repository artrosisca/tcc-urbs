"""
Coletor de telemetria da URBS.

Grava os dados brutos em CSV, organizados por dia e hora.

Como configurar a pasta de saida:
- Se PASTA_SAIDA_CONFIGURADA estiver vazia (None), os dados vao para a pasta
  "dados_em_tempo_real_2026" ao lado deste arquivo.
- Se voce colocar um caminho, os dados vao para esse caminho. Use isso para
  salvar dentro de uma pasta sincronizada (ex.: Google Drive).

Uso (Windows): clique duas vezes em "executar_coletor.bat".
Para parar: Ctrl+C.
"""

import os
import time
import datetime

import pandas as pd
import requests

# ============================================================
# CONFIGURACAO: pasta de saida
# ============================================================
# Deixe None para salvar ao lado do script, OU coloque o caminho de uma
# pasta sincronizada para enviar os dados automaticamente.
#
# Exemplos:
#   Windows (Google Drive espelhado):
#     PASTA_SAIDA_CONFIGURADA = r"C:\Users\SEU_USUARIO\My Drive\tcc_dados"
#   Windows (unidade G:):
#     PASTA_SAIDA_CONFIGURADA = r"G:\Meu Drive\tcc_dados"
PASTA_SAIDA_CONFIGURADA = None

if PASTA_SAIDA_CONFIGURADA:
    PASTA_PRINCIPAL_DADOS = PASTA_SAIDA_CONFIGURADA
else:
    PASTA_PRINCIPAL_DADOS = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "dados_em_tempo_real_2026"
    )

# ============================================================
# Configuracoes da API
# ============================================================
BASE_URL = "https://transporteservico.urbs.curitiba.pr.gov.br/"
ENDPOINT = "getVeiculos.php"
API_CODE = "65d35"
FULL_URL = f"{BASE_URL}{ENDPOINT}"
PARAMS = {"c": API_CODE}

INTERVALO_SEGUNDOS = 20


def fetch_vehicle_data():
    try:
        response = requests.get(FULL_URL, params=PARAMS, timeout=30)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data).T
    except requests.exceptions.RequestException as e:
        print(f"  [ERRO DE REDE] Falha na conexao com a API: {e}")
    except requests.exceptions.JSONDecodeError:
        print("  [ERRO DE DADOS] A API nao retornou um JSON valido.")
    except Exception as e:
        print(f"  [ERRO INESPERADO] {e}")
    return None


def save_data_to_csv(df, file_path):
    try:
        file_exists = os.path.isfile(file_path)
        df.to_csv(file_path, mode="a", header=not file_exists, index=False)
        return True
    except IOError as e:
        print(f"  [ERRO DE DISCO] Falha ao escrever no CSV: {e}")
    except Exception as e:
        print(f"  [ERRO INESPERADO] {e}")
    return False


def main():
    print("--- Iniciando Coletor de Dados da URBS ---")
    print(f"Intervalo de coleta: {INTERVALO_SEGUNDOS} segundos")
    print(f"Pasta de saida: {PASTA_PRINCIPAL_DADOS}")
    print("Pressione CTRL+C para parar.")

    while True:
        try:
            agora = datetime.datetime.now()
            print(f"\nColetando dados as: {agora.strftime('%Y-%m-%d %H:%M:%S')}")

            df_dados = fetch_vehicle_data()

            if df_dados is not None and not df_dados.empty:
                df_dados["request_timestamp"] = agora

                pasta_dia = agora.strftime("%Y-%m-%d")
                nome_arquivo = f"{agora.strftime('%Y-%m-%d_%H-00')}.csv"

                caminho_completo_pasta = os.path.join(PASTA_PRINCIPAL_DADOS, pasta_dia)
                caminho_completo_arquivo = os.path.join(caminho_completo_pasta, nome_arquivo)

                os.makedirs(caminho_completo_pasta, exist_ok=True)

                if save_data_to_csv(df_dados, caminho_completo_arquivo):
                    print(f"  Sucesso! {len(df_dados)} registros salvos em: {caminho_completo_arquivo}")
            else:
                print("  Nenhum dado recebido da API nesta coleta.")

            print(f"  Aguardando {INTERVALO_SEGUNDOS} segundos para o proximo ciclo...")
            time.sleep(INTERVALO_SEGUNDOS)

        except KeyboardInterrupt:
            print("\n--- Coletor interrompido pelo usuario. Encerrando. ---")
            break
        except Exception as e:
            print(f"[ERRO GRAVE NO LOOP PRINCIPAL] {e}")
            print("  Aguardando e tentando novamente...")
            time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    main()
