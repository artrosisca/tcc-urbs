import requests
import pandas as pd
import time
import os
import datetime

# --- Configurações da API ---
BASE_URL = "https://transporteservico.urbs.curitiba.pr.gov.br/"
ENDPOINT = "getVeiculos.php"
API_CODE = "65d35"
FULL_URL = f"{BASE_URL}{ENDPOINT}"
PARAMS = {'c': API_CODE}

# --- Configurações do Coletor ---
INTERVALO_SEGUNDOS = 20  # 2 minutos
PASTA_PRINCIPAL_DADOS = "data/dados_em_tempo_real_2026"

def fetch_vehicle_data():
    try:
        # O 'timeout=30' impede que o script fique "preso" se a rede ficar lenta.
        # Se a internet cair, o 'requests.get' vai falhar e pular para o 'except'.
        response = requests.get(FULL_URL, params=PARAMS, timeout=30)
        response.raise_for_status() 
        
        data = response.json()
        df = pd.DataFrame(data).T
        return df
        
    except requests.exceptions.RequestException as e:
        # Se a internet cair, ou o site da URBS estiver fora, o erro é capturado aqui.
        print(f"  [ERRO DE REDE] Falha na conexão com a API: {e}")
        
    except requests.exceptions.JSONDecodeError:
        # Se a API retornar algo que não é JSON (ex: um erro HTML), capturamos aqui.
        print("  [ERRO DE DADOS] A API não retornou um JSON válido.")
        
    except Exception as e:
        # Qualquer outro erro ao buscar dados é capturado aqui.
        print(f"  [ERRO INESPERADO] Ocorreu um erro ao buscar dados: {e}")
        
    # Se qualquer erro acontecer, a função retorna 'None'
    return None

def save_data_to_csv(df, file_path):
    """
    Salva o DataFrame em um arquivo CSV, anexando os dados.
    """
    try:
        file_exists = os.path.isfile(file_path)
        df.to_csv(file_path, mode='a', header=not file_exists, index=False) # mudei para false porque o indice e a coluna tem o mesmo codigo
        return True
        
    except IOError as e:
        # Se o disco estiver cheio, ou o arquivo estiver bloqueado, capturamos aqui.
        print(f"  [ERRO DE DISCO] Falha ao escrever no arquivo CSV: {e}")
        
    except Exception as e:
        print(f"  [ERRO INESPERADO] Ocorreu um erro ao salvar dados: {e}")
        
    return False

def main():
    print("--- Iniciando Coletor de Dados da URBS ---")
    print(f"Intervalo de coleta: {INTERVALO_SEGUNDOS} segundos (2 minutos)")
    print(f"Pressione CTRL+C para parar.")
    
    # Loop infinito que garante a execução contínua
    while True:
        try:
            # loop principal de execucao
            agora = datetime.datetime.now()
            print(f"\nColetando dados às: {agora.strftime('%Y-%m-%d %H:%M:%S')}")

            df_dados = fetch_vehicle_data()
            
            # O script só tenta salvar se 'df_dados' não for 'None' (ou seja, se a coleta foi bem-sucedida)
            if df_dados is not None and not df_dados.empty:
                df_dados['request_timestamp'] = agora

                pasta_dia = agora.strftime("%Y-%m-%d")
                nome_arquivo = f"{agora.strftime('%Y-%m-%d_%H-00')}.csv"
                
                caminho_completo_pasta = os.path.join(PASTA_PRINCIPAL_DADOS, pasta_dia)
                caminho_completo_arquivo = os.path.join(caminho_completo_pasta, nome_arquivo)
                
                os.makedirs(caminho_completo_pasta, exist_ok=True)
                
                if save_data_to_csv(df_dados, caminho_completo_arquivo):
                    print(f"  Sucesso! {len(df_dados)} registros salvos em: {caminho_completo_arquivo}")
            else:
                print("  Nenhum dado recebido da API nesta coleta. (Pode ser falha de rede)")

            print(f"  Aguardando {INTERVALO_SEGUNDOS} segundos para o próximo ciclo...")
            time.sleep(INTERVALO_SEGUNDOS)
            
        except KeyboardInterrupt:
            # Permite que você pare o script manualmente com CTRL+C sem corromper nada.
            print("\n--- Coletor interrompido pelo usuário. Encerrando. ---")
            break
            
        except Exception as e:
            # O script NUNCA morre sozinho.
            print(f"[ERRO GRAVE NO LOOP PRINCIPAL] {e}")
            print("  Ocorreu um erro inesperado. O script vai esperar 2 minutos e tentar novamente.")
            time.sleep(INTERVALO_SEGUNDOS)

if __name__ == "__main__":
    main()