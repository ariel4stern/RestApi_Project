import numpy as np
from sklearn.metrics  import r2_score
from sklearn.linear_model  import LinearRegression
from  sklearn.preprocessing import PolynomialFeatures
import joblib
import os
from sklearn.pipeline import Pipeline

MODELS_DIR = os.path.join("models", "saved_models")

def train_and_save_model(training_hours:list[float], running_time:list[float], degree:int, user_name:str)->dict:
    os.makedirs(MODELS_DIR, exist_ok=True)

    x = np.array(training_hours).reshape(-1, 1)
    y = np.array(running_time)

    pipeline = Pipeline([
        ("poly", PolynomialFeatures(degree=degree)),
        ("model", LinearRegression())
    ])

    pipeline.fit(x, y)

    y_pred = pipeline.predict(x)

    score = r2_score(y, y_pred)


    model_data = {
        "model": pipeline,
        "score": score
    }

    file_path = os.path.join(MODELS_DIR, f"{user_name}.pkl")
    joblib.dump(model_data, file_path)

    return model_data

def predict_model(model_name: str, hours_value: float)->float:
    file_path = os.path.join(MODELS_DIR, f"{model_name}.pkl")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Model '{model_name}' not found")

    model_data = joblib.load(file_path)

    model = model_data["model"]

    prediction = model.predict(np.array([hours_value]).reshape(-1, 1))

    return prediction.tolist()[0]
def get_model_score(model_name:str)->int|None:
    file_path = os.path.join(MODELS_DIR, f"{model_name}.pkl")

    if not os.path.exists(file_path):
        return None

    model_data = joblib.load(file_path)

    return model_data["score"]

def delete_model_by_name(model_name:str):
    file_path = os.path.join(MODELS_DIR, f"{model_name}.pkl")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Model '{model_name}' not found")
    os.remove(file_path)

def change_model_name_file(old_model_name, new_model_name: str) -> bool:
    old_path = os.path.join(MODELS_DIR, f"{old_model_name}.pkl")
    new_path = os.path.join(MODELS_DIR, f"{new_model_name}.pkl")

    if not os.path.exists(old_path):
        print(f"Model '{old_model_name}' not found")
        return False

    if os.path.exists(new_path):
        print(f"Model '{new_model_name}' already exists")
        return False

    os.rename(old_path, new_path)
    return True


#train_and_save_model(training_hours=[100,120,145,170,195,215,240,265,290,320],running_time=[40 ,50 ,60 ,70  ,80, 90 ,100,110,120,130],user_name='model_1',degree=2)
#print(predict_model(model_name='model_1',hours_value=450))

#{"training_hours":[40 ,50 ,60 ,70  ,80, 90 ,100,110,120,130],
#"running_time":[100,120,145,170,195,215,240,265,290,320],
#"degree":2}



