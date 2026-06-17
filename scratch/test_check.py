import os
import pandas as pd
from datetime import datetime, time

def check_raw_gps_data(line_code: str, start_date: str, end_date: str, start_hour: str = None, end_hour: str = None, data_dir="dados_em_tempo_real_2026") -> int:
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception as e:
        print("Date parse error:", e)
        return 0

    date_list = pd.date_range(start_dt, end_dt).strftime("%Y-%m-%d").tolist()
    
    start_h_int = 0
    end_h_int = 24
    if start_hour:
        try:
            start_h_int = int(start_hour.split(":")[0])
        except:
            pass
    if end_hour:
        try:
            end_h_int = int(end_hour.split(":")[0])
            if "23:59" in end_hour or "24:00" in end_hour:
                end_h_int = 24
        except:
            pass
            
    total_records = 0
    print(f"Date list: {date_list}, hours: {start_h_int} to {end_h_int}")
    
    for date_str in date_list:
        day_dir = os.path.join(data_dir, date_str)
        if not os.path.exists(day_dir):
            day_dir_alt = os.path.join(data_dir, date_str.replace('-', '_'))
            if os.path.exists(day_dir_alt):
                day_dir = day_dir_alt
            else:
                print(f"Directory {day_dir} does not exist.")
                continue
                
        try:
            files = os.listdir(day_dir)
        except Exception as e:
            print("Listdir error:", e)
            continue
            
        print(f"Checking {len(files)} files in {day_dir}")
        for f in files:
            if not f.endswith('.csv'):
                continue
                
            try:
                hour_part = int(f.split('_')[-1].split('-')[0])
            except Exception as e:
                continue
                
            if hour_part < start_h_int or hour_part > end_h_int:
                continue
                
            filepath = os.path.join(day_dir, f)
            try:
                df_temp = pd.read_csv(filepath, usecols=['CODIGOLINHA', 'request_timestamp'])
                df_line = df_temp[df_temp['CODIGOLINHA'].astype(str) == str(line_code)]
                if not df_line.empty:
                    print(f"File {f} has {len(df_line)} points for line {line_code}")
                total_records += len(df_line)
            except Exception as e:
                print(f"Read error for {f}: {e}")
                
    return total_records

if __name__ == "__main__":
    count = check_raw_gps_data("541", "2025-10-24", "2025-10-24", "00:00", "24:00")
    print(f"TOTAL POINTS: {count}")
