from fastapi import APIRouter, HTTPException,Depends
from pydantic import BaseModel, Field
from auth import get_current_user
import models_functions
from dal_users import du_coins_count,du_reset_coins,du_reduce_coins
import dal_models as dam

DB_NAME_MODELS = "models.db"
DB_NAME_USERS = "users.db"

#py -m uvicorn router_models:router --port 8000 --reload

router = APIRouter(tags=["Models"])

class ModelCreate(BaseModel):
    training_hours: list[float] = Field(..., min_length=1)
    running_time: list[float] = Field(..., min_length=1)
    degree: int = Field(..., ge=0)

dam.dm_create_table(DB_NAME_MODELS)


@router.get("/models")
def get_models_table():
    table = dam.dm_get_table(DB_NAME_MODELS)

    if table is None:
        raise HTTPException(status_code=500, detail="Database error")

    return {"models table: ": table }

@router.get("/models/name")          #ON USE IN WEB
def get_model_by_name(current_user=Depends(get_current_user)):
    user_name = current_user["user_name"]
    model = dam.dm_get_model_by_model_name(user_name,DB_NAME_MODELS)
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"model": model }

@router.get("/models/acc")            #ON USE IN WEB
def get_models_accuracy(current_user=Depends(get_current_user)):
    m = dam.dm_get_model_by_model_name(current_user["user_name"],DB_NAME_MODELS)

    if m is None:
        raise HTTPException(status_code=404, detail="Model not found")

    acc = models_functions.get_model_score(current_user["user_name"])
    return {f"model -{current_user["user_name"]}-": f"accuracy: {acc}"}

@router.get("/models/predict/{hours_value}")          #ON USE IN WEB
def get_prediction(hours_value: float,current_user=Depends(get_current_user)):
    user_name = current_user["user_name"]
    coins_left = du_coins_count(user_name,DB_NAME_USERS)

    if coins_left <= 0:
        du_reset_coins(user_name,DB_NAME_USERS)
        return {"coins left": coins_left,
                "message": "Not enough coins,Please recharge to continue"}

    try:
        prediction = models_functions.predict_model(user_name,hours_value=hours_value)
        du_reduce_coins(user_name,DB_NAME_USERS)
        return {
                    "prediction": prediction,
                    "message" : f"model of {current_user['user_name']} predicted successfully",
                    "coins left": coins_left-1}

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/models/train")         #ON USE IN WEB
def create_model(model_val: ModelCreate ,current_user=Depends(get_current_user)):
    if len(model_val.training_hours) != len(model_val.running_time):
        raise HTTPException(status_code=400, detail="training_hours and running_time must be same length")

    if len(model_val.training_hours) == 0:
        raise HTTPException(status_code=422,detail="You can't send an empty training_hours or running_time")

    if model_val.degree <= 0:
        raise HTTPException(status_code=422, detail="degree must be > 0")

    for h in range(len(model_val.training_hours)):
        if model_val.training_hours[h] < 0 :
            raise HTTPException(status_code=422, detail="You can't send an negative training_hours value")
        if model_val.running_time[h] < 0 :
            raise HTTPException(status_code=422, detail="You can't send an negative running_time value")

    try:
        inserted_model = dam.dm_insert_model(current_user["user_name"],DB_NAME_MODELS)
        models_functions.train_and_save_model(training_hours=model_val.training_hours,
                                              running_time= model_val.running_time,
                                              degree= model_val.degree,
                                              user_name= current_user["user_name"])


        if inserted_model is None:
           raise HTTPException(status_code=500, detail="Failed to save model")

        return { "model": inserted_model,
                "message" : "Created Successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/models/del")          #ON USE IN WEB
def delete_model_by_name(current_user=Depends(get_current_user)):
    user_name = current_user["user_name"]
    m = dam.dm_get_model_by_model_name(user_name,DB_NAME_MODELS)

    if m is None:
        raise HTTPException(status_code=404, detail="Model not found")

    deleted_model = dam.dm_delete_model_by_model_name(user_name,DB_NAME_MODELS)

    if deleted_model is None:
        raise HTTPException(status_code=404, detail="Failed to delete model")

    return {"status":"Successfully deleted",
            "model":deleted_model}


@router.delete("/models/delete/recreate")
def recreate_table():
    restart = dam.dm_recreate_table(DB_NAME_MODELS)

    if restart is None:
        raise HTTPException(status_code=500, detail="Failed to recreate table")

    return { "message" : "recreated successfully"}



