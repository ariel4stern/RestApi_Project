from typing import Optional
from fastapi import APIRouter,HTTPException, status,Depends
from pydantic import BaseModel, Field, EmailStr
from auth import create_access_token,get_current_user
import credit_functions as cd
import dal_users as dau
from dal_models import dm_change_model_name,dm_get_model_by_model_name
from models_functions import change_model_name_file

DB_NAME_MODELS = "models.db"
DB_NAME_USERS = "users.db"

#py -m uvicorn router_users:router --port 8000 --reload

router = APIRouter(tags=["Users"])


class UserCreate(BaseModel):
    user_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=4, max_length=100)
class UserUpdate(BaseModel):
    user_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=4, max_length=100)
class UserUpdatePatch(BaseModel):
    user_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class LoginRequest(BaseModel):
    user_name: str
    password: str
class Credit(BaseModel):
    front_digits: str
    expire_digits: str
    back_digits: str

dau.du_create_table_users(DB_NAME_USERS)

@router.get("/users")
def get_users():
    users = dau.du_get_all_users(DB_NAME_USERS)
    if users is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"Status" : "Success",
            "All users: ": users}
@router.get("/users/id/{user_id}")
def get_user_by_id(user_id: int):
    user = dau.du_get_user_by_id(user_id,DB_NAME_USERS)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"User: ": user}
@router.get("/users/name/{user_name}")
def get_user_by_username(user_name:str):
    user = dau.du_get_user_by_user_name_public(user_name,DB_NAME_USERS)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"User: ": user}

@router.post("/users")                  #ON USE IN WEB
def create_user(user: UserCreate):
    new_user = dau.du_insert_user(user_name=user.user_name,
                                     email=user.email,
                                     password= user.password,
                                     db_name = DB_NAME_USERS)
    if new_user is None:
        raise HTTPException(status_code=404,
                            detail="Username or email already exists")

    return {"message": "Signed in Successfully",
            "User": new_user}
@router.put("/users/update/{user_id}")
def update_user(user_id:int, user: UserUpdate,current_user = Depends(get_current_user)):
    updated_user = dau.du_update_user(user_id = user_id,
                                         user_name=user.user_name,
                                         email=user.email,
                                         password=user.password,
                                         db_name = DB_NAME_USERS)
    if updated_user is None:
        raise HTTPException(status_code=404,detail="User not found")

    return {"Status": "Success",
            "Updated user: ": updated_user}

@router.patch("/users/patch/{user_id}")       #ON USE IN WEB
def patch_user(user_id:int, patched_user:UserUpdatePatch,current_user = Depends(get_current_user)):
    old_name = current_user["user_name"]
    new_name = patched_user.user_name

    updated_user = dau.du_patch_user(user_id = user_id,
                                        user_name=new_name,
                                        email=patched_user.email,
                                        password=patched_user.password,
                                        db_name = DB_NAME_USERS)
    if updated_user is None:
        raise HTTPException(status_code=404,detail="User not found")

    m = dm_get_model_by_model_name(user_name=old_name, db_name = DB_NAME_MODELS)

    if new_name is not None and m is not None and old_name != new_name:
        db_up_model = dm_change_model_name(old_model_name=old_name,new_model_name=new_name,db_name=DB_NAME_MODELS)

        if db_up_model is None:
            raise HTTPException(status_code=404,detail="Model not found")

        file_up_model = change_model_name_file(old_model_name=old_name,new_model_name=new_name)

        if not file_up_model:
            raise HTTPException(status_code=404,detail="Model not found")

        return {"Status": "Success",
                "Patched user: ": updated_user,
                "new model: ": db_up_model}

    return {"Status": "Success",
            "Patched user: ": updated_user}

@router.delete("/users/del/{user_id}")
def delete_user(user_id: int,current_user = Depends(get_current_user)):

    deleted_user = dau.du_delete_user(user_id = user_id,db_name = DB_NAME_USERS)

    if deleted_user is None:
        raise HTTPException(status_code=404,detail="User not found")

    return {"message": "User deleted Successfully",
            "user": deleted_user}

@router.post("/users/login")              #ON USE IN WEB
def login(login_data: LoginRequest):
    is_valid = dau.du_login_user(login_data.user_name,
                                    login_data.password,DB_NAME_USERS)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    access_token = create_access_token(login_data.user_name)

    return {
        "Status" : "Success",
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/users/buy_coins")         #ON USE IN WEB
def buy_coins(credit:Credit,current_user=Depends(get_current_user)):
    if not cd.c_fronted_digits(credit.front_digits):
        raise HTTPException(status_code=400,detail="Front Digits not allowed (16 numbers only)")

    if not cd.c_expired_digits(credit.expire_digits):
        raise HTTPException(status_code=400,detail="Expired Digits not allowed(format: 11.11 | 11/11 )")

    if not cd.c_back_digits(credit.back_digits):
        raise HTTPException(status_code=400,detail="Back Digits not allowed (3 numbers only)")

    n_coins = dau.du_decrease_coins(current_user["user_name"],DB_NAME_USERS)

    if n_coins is None:
        raise HTTPException(status_code=500,detail="DataBase Error")

    return {"message": f"10 coins decreased successfully, coins left: {n_coins}"}

@router.delete("/users/tables/recreate")
def recreate_table(current_user = Depends(get_current_user)):
    re = dau.du_recreate_table_users(DB_NAME_USERS)
    if not re:
        raise HTTPException(status_code=500,detail="Database Error")
    return {"message": "Table recreated and set successfully"}



