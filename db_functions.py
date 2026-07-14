import shutil
import sqlite3
import pandas as pd
import os
def remove_model_from_dir(model_name):
    model_path = os.path.join(os.getcwd(), "models","saved_models",f"{model_name}.pkl")
    try:
        os.remove(model_path)
    except Exception as e:
        print(e)
    print(f"removing {model_path}")

def read_db(table_name:str)->list[dict]|None:
    try:
        conn = sqlite3.connect(f"{table_name}.db")
        table = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        users = table.to_dict(orient="records")
        conn.close()
        return users

    except Exception as e:
        print(e)
        return None
def count_files(folder_path)->int:
    if os.path.exists(folder_path):
        return len(os.listdir(folder_path))
    return 0
def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        try:
            if os.path.isfile(file_path):
                print(f"deleting {filename}")
                os.remove(file_path)

            if os.path.isdir(file_path):
                shutil.rmtree(file_path)


        except Exception as e:
            print(e)
