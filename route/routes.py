from fastapi import APIRouter,Response,Request,HTTPException,Depends,UploadFile,File
from fastapi import APIRouter,Response,Request,HTTPException,Depends,UploadFile,File
from models.models import User,Login
from security import hash_password,verify_password
from database import db,cursor
from configJWT import create_acces_token,create_refresh_token,verify_token  # type: ignore
import pandas as pd

router = APIRouter()

def get_current_user(request : Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401)
    
    try:
        payload = verify_token(token)
        return payload["sub"]
    except:
        raise HTTPException(status_code=401)

@router.get("/")
def home():
    return {"message":"Bienvenue dans notre jeux"}

@router.get("/dashboard")
def dashboard(user = Depends(get_current_user)): # type: ignore
    return {"message":f"Bienvenue {user}"}

@router.post("/refresh")
def refresh(request : Request , response : Response):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401)
    
    try:
        payload = verify_token(refresh_token)
        new_acces = create_acces_token({"sub":payload["sub"]})

        response.set_cookie("access_token",new_acces,httponly=True,samesite="none",secure=True)
        return {"message":"refreshed"}
    except:
        raise HTTPException(status_code=401)

@router.post("/logout")
def logout(response : Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message":"logout"}

@router.post("/register")
def register(user : User):
    hashed = hash_password(user.password)
    query = """
        INSERT INTO application (name,email,password) VALUES (%s,%s,%s)
    """
    values = (user.name,user.email,hashed)

    cursor.execute(query,values)
    db.commit()

    return {"message":"Utilisateur securisé !"}

@router.post("/login")
def login(users : Login,response : Response): # type: ignore
    query = "SELECT * FROM application WHERE email = %s"
    value = (users.email,)
    cursor.execute(query,value)

    user = cursor.fetchone()

    if user and verify_password(users.password,user['password']): # type: ignore
        acces = create_acces_token({"sub":user['email']}) # type: ignore
        refresh = create_refresh_token({"sub":user['email']}) # type: ignore

        response.set_cookie('access_token',acces,httponly=True,samesite="none",secure=True)
        response.set_cookie('refresh_token',refresh,httponly=True,samesite="none",secure=True)

        return {"name":f"{user['name']}","acces":1} # type: ignore
    else:
        return {"message":"Identifiant incorrect !","acces":0} # type: ignore

@router.post("/upload")
async def upload(file : UploadFile = File(...)):

    from datetime import datetime

    df = pd.read_csv(file.file,skiprows=1)

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    data_now = datetime.now().date()

    df_aujourd_hui = df[df['Date'].dt.date == data_now]

    total = df_aujourd_hui['Price'].sum()

    return {"total": float(total)}
