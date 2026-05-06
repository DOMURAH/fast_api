from fastapi import APIRouter,Response,Request,HTTPException,Depends,UploadFile,File
from models.models import User,Login
from security import hash_password,verify_password
from database import db,cursor
from configJWT import create_acces_token,create_refresh_token,verify_token  # type: ignore
import pandas as pd
import json
from routerOS import get_all_users, get_active_connections
from datetime import datetime

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
        refresh = create_refresh_token({"sub":user['email']}) # type:   ignore

        response.set_cookie('access_token',acces,httponly=True,samesite="none",secure=True)
        response.set_cookie('refresh_token',refresh,httponly=True,samesite="none",secure=True)

        return {"name":f"{user['name']}","acces":1} # type: ignore
    else:
        return {"message":"Identifiant incorrect !","acces":0} # type: ignore

@router.post("/upload")
async def upload(file : UploadFile = File(...)): # type: ignore
    from datetime import datetime
    import pandas as pd
    import csv

    df = pd.read_csv(file.file,skiprows=1)

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    data_now = datetime.now().date()

    df_aujourd_hui = df[df['Date'].dt.date == data_now]

    all_user = get_all_users()[2:]  # Skip first 2 entries (static users)

    # Clean API data
    df_api = pd.DataFrame(all_user)

    # username normalisé pour le merge
    df_api['Username'] = df_api['name'].astype(str).str.lower()

    comment_str = df_api['comment'].fillna('').astype(str)

    # Cas 1) comment = "YYYY-MM-DD HH:MM:SS"
    iso_dt = pd.to_datetime(comment_str, format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # Cas 2) comment = "up-352-05.03.26-"  => reconstruit "20YY-MM-DD" (heure inconnue)
    # On extrait MM, DD, YY

    mm_dd_yy = comment_str.str.extract(r'up-\d*-(\d{2})\.(\d{2})\.(\d{2})-')
    mm = mm_dd_yy[0]
    dd = mm_dd_yy[1]
    yy = mm_dd_yy[2]

    y_full = yy.apply(lambda x: f"20{x}" if pd.notna(x) else None)

    reconstructed_date = pd.to_datetime(
        y_full.astype(str) + '-' + mm.astype(str) + '-' + dd.astype(str),
        errors='coerce'
    )

    # Priorité ISO, sinon date reconstruite
    df_api['comment_parsed'] = iso_dt.fillna(reconstructed_date)

    df_api['api_date'] = df_api['comment_parsed'].dt.date
    df_api['api_time'] = df_api['comment_parsed'].dt.time

    # map profile to price
    df_api['Price'] = df_api['profile'].map({'1H': 500, '2h': 1000, '3mois': 40000}).fillna(0)

    # Append only new df_api users not in uploaded CSV
    df['№'] = df['№'].astype(int)
    existing_usernames = set(df['Username'].str.lower())

    new_mask = ~df_api['Username'].isin(existing_usernames)
    new_df = df_api[new_mask].copy()

    appended_count = 0
    if len(new_df) > 0:
        next_no = df['№'].max() + 1
        new_df['№'] = range(next_no, next_no + len(new_df))
        new_df['Date'] = new_df['api_date']
        new_df['Time'] = new_df['api_time'].fillna(pd.NaT).astype(str).fillna('00:00:00')
        new_df['Profile'] = new_df['profile']
        new_df['Comment'] = new_df['comment']
        new_selected = new_df[['№', 'Date', 'Time', 'Username', 'Profile', 'Comment', 'Price']]
        df = pd.concat([df, new_selected], ignore_index=True)
        appended_count = len(new_df)

    # Update totals
    df_today = df[df['Date'] == data_now.strftime('%Y-%m-%d')]
    # Important: total_now should reflect only what is ACTIVE right now, not historical rows.
    # We compute the usernames currently active on Mikrotik and sum only matching CSV rows.
    active_connections = get_active_connections()  # list/dicts from /ip/hotspot/active

    active_usernames = {
        str(conn.get('user', '')).lower()
        for conn in active_connections
        if conn.get('user', None) not in (None, '')
    }

    if active_usernames:
        total = df_today[df_today['Username'].str.lower().isin(active_usernames)]['Price'].sum()
    else:
        total = 0

    total_all = df['Price'].sum()
    number_of_rows = len(df)


    all_name = df['Username'].tolist()

    # Save updated df to report CSV with summary
    csv_path = "report-mikhmon-all.csv"
    total_price = total_all
    summary_line = f"Selling Report all,,,,,Total,Ar {total_price:,.2f}\n"
    header = "№,Date,Time,Username,Profile,Comment,Price\n"
    df.to_csv(csv_path, index=False, header=False, mode='w')


    # Response data
    df_clean = df.replace([float('inf'), -float('inf'), float('nan')], 0).to_dict('records')
    df_api_clean = df_api.replace([float('inf'), -float('inf'), float('nan')], 0).to_dict('records')

    return {
        "appended": appended_count,
        "total_now": float(total) if not pd.isna(total) else 0.0,
        "total_all": float(total_all) if not pd.isna(total_all) else 0.0,
        "number_of_rows": int(number_of_rows),
        "all_name": all_name,
        "updated_data": df_clean,
        "df_api": df_api_clean,
        "user_upload": all_user
    } # type: ignore
    
@router.get("/mikrotik")
def mikrotik():
    from routerOS import get_active_connections, get_all_users

    active_connections = get_active_connections()
    all_user = get_all_users()
    date_user = [user.get('comment', '') for user in all_user]

    total_now = len(active_connections) * 500
    active_connections_count = len(active_connections)

    return {
        "active_connect_now": active_connections,
        "active_connections": active_connections_count,
        "price": total_now,
        "all_user": all_user,
        "date_user": date_user
    }

