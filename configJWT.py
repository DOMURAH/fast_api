from jose import jwt
from datetime import datetime,timedelta

SECRET_KEY = "SUPER_SECRET_KEY"
ALGORITHME = "HS256"

def create_acces_token(data : dict): # type: ignore
    to_encode = data.copy() # type: ignore
    expire = datetime.utcnow() +  timedelta(minutes=15) # type: ignore
    to_encode.update({"exp" : expire}) # type: ignore
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHME) # type: ignore

def create_refresh_token(data : dict): # type: ignore
    to_encode = data.copy() # type: ignore
    expire = datetime.utcnow() + timedelta(days=7)# type: ignore
    to_encode.update({"exp":expire}) # type: ignore
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHME)# type: ignore

def verify_token(token : str):
    return jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHME])
