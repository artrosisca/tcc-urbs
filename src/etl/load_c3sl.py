import os
import lzma
import json
import pandas as pd

def parse_coord(val):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip().replace(',', '.')
        try:
            return float(val)
        except ValueError:
            return None
    return None

def fix_encoding(text):
    if not isinstance(text, str):
        return text
    # Tenta corrigir encoding de caracteres corrompidos em latin1/utf-8
    try:
        # Se foi lido como utf-8 mas continha bytes latin1 inválidos que viraram replacement character
        # ou se veio com encoding misto. Geralmente, re-encodar para cp1252/latin1 e decodar para utf-8 funciona.
        return text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        try:
            return text.encode('utf-8').decode('latin-1')
        except:
            return text

def load_static_data(date_str, line_code, c3sl_dir="dados_c3sl"):
    """
    Carrega dados estáticos (pontos de parada, tabela planejada e shape da linha) para uma linha específica e data.
    
    Args:
        date_str (str): Data no formato 'YYYY-MM-DD' ou 'YYYY_MM_DD'
        line_code (str): Código da linha (ex: '541')
        c3sl_dir (str): Caminho para o diretório com dados da C3SL
        
    Returns:
        dict: Dicionário contendo DataFrames de 'pontos', 'tabela' e 'shape'
    """
    # Padronizar formato da data para YYYY_MM_DD
    formatted_date = date_str.replace('-', '_')
    
    pontos_file = os.path.join(c3sl_dir, f"{formatted_date}_pontosLinha.json.xz")
    tabela_file = os.path.join(c3sl_dir, f"{formatted_date}_tabelaLinha.json.xz")
    shape_file = os.path.join(c3sl_dir, f"{formatted_date}_shapeLinha.json.xz")
    
    # 1. Carregar Pontos de Parada
    pontos_df = pd.DataFrame()
    if os.path.exists(pontos_file):
        # Primeiro lemos como cp1252 ou latin1 para evitar erros de caractere
        try:
            with lzma.open(pontos_file, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        except UnicodeDecodeError:
            with lzma.open(pontos_file, 'rt', encoding='latin1') as f:
                data = json.load(f)
                
        # Filtrar pela linha
        line_pontos = [p for p in data if p.get('COD') == str(line_code)]
        if line_pontos:
            pontos_df = pd.DataFrame(line_pontos)
            # Corrigir encodings
            for col in ['NOME', 'SENTIDO']:
                if col in pontos_df.columns:
                    pontos_df[col] = pontos_df[col].apply(fix_encoding)
            
            # Formatar coordenadas
            pontos_df['LAT'] = pontos_df['LAT'].apply(parse_coord)
            pontos_df['LON'] = pontos_df['LON'].apply(parse_coord)
            pontos_df['SEQ'] = pontos_df['SEQ'].astype(int)
    else:
        print(f"Aviso: Arquivo de pontos {pontos_file} não encontrado.")
        
    # 2. Carregar Tabela Planejada
    tabela_df = pd.DataFrame()
    if os.path.exists(tabela_file):
        try:
            with lzma.open(tabela_file, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        except UnicodeDecodeError:
            with lzma.open(tabela_file, 'rt', encoding='latin1') as f:
                data = json.load(f)
                
        line_tabela = [t for t in data if t.get('COD') == str(line_code)]
        if line_tabela:
            tabela_df = pd.DataFrame(line_tabela)
            if 'PONTO' in tabela_df.columns:
                tabela_df['PONTO'] = tabela_df['PONTO'].apply(fix_encoding)
    else:
        print(f"Aviso: Arquivo de tabela {tabela_file} não encontrado.")
        
    # 3. Carregar Shape da Linha
    shape_df = pd.DataFrame()
    if os.path.exists(shape_file):
        try:
            with lzma.open(shape_file, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        except UnicodeDecodeError:
            with lzma.open(shape_file, 'rt', encoding='latin1') as f:
                data = json.load(f)
                
        line_shape = [s for s in data if s.get('COD') == str(line_code)]
        if line_shape:
            shape_df = pd.DataFrame(line_shape)
            shape_df['LAT'] = shape_df['LAT'].apply(parse_coord)
            shape_df['LON'] = shape_df['LON'].apply(parse_coord)
    else:
        print(f"Aviso: Arquivo de shape {shape_file} não encontrado.")
        
    return {
        'pontos': pontos_df,
        'tabela': tabela_df,
        'shape': shape_df
    }

if __name__ == "__main__":
    # Teste rápido
    res = load_static_data("2025-10-24", "541")
    print("Pontos carregados:", len(res['pontos']))
    print("Tabela carregada:", len(res['tabela']))
    print("Shape carregado:", len(res['shape']))
    if not res['pontos'].empty:
        print("Pontos (exemplo):\n", res['pontos'][['SEQ', 'NUM', 'NOME', 'LAT', 'LON']].head(3))
