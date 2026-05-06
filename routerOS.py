import routeros_api
import pandas as pd
from datetime import datetime

df = pd.read_csv("report-mikhmon-all (11).csv")

connection = routeros_api.RouterOsApiPool(
    "192.168.1.55",
    username="admin",
    password="1234",
    port=8728,
    plaintext_login=True
)

print(datetime.now())

api = connection.get_api()

data_now = datetime.now().date()

all_user = api.get_resource('/ip/hotspot/user').get()[2:]

df_api = pd.DataFrame(all_user)
df_api['Username'] = df_api['name'].str.lower()

comment_str = df_api['comment'].fillna('').astype(str)

iso_dt = pd.to_datetime(comment_str,format='%Y-%m-%d %H:%M:%S',errors="coerce")

mm_dd_yy = comment_str.str.extract(r'up-\d*-(\d{2})\.(\d{2})\.(\d{2})-')
mm = mm_dd_yy[0]
dd = mm_dd_yy[1]
yy = mm_dd_yy[2]
# 
y_full = yy.apply(lambda x: f"20{x}" if pd.notna(x) else None)

reconstructed_date = pd.to_datetime(
    y_full.astype(str) + '-' + mm.astype(str) + '-' + dd.astype(str),
    errors='coerce'
)

df_api['comment_parsed'] = iso_dt.fillna(reconstructed_date)

df_api['api_date'] = df_api['comment_parsed'].dt.date
df_api['api_time'] = df_api['comment_parsed'].dt.time
df_api['Price'] = df_api['profile'].map({'1H': 500, '2h': 1000, '3mois': 15000}).fillna(0)

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

df_today = df[df['Date'] == data_now.strftime('%Y-%m-%d')]
total = df_today['Price'].sum()
print(total)


# df['Username_lower'] = df['Username'].str.lower()
# merged_df = df.merge(df_api[['Username','comment_parsed', 'uptime', 'bytes-in', 'bytes-out', 'api_date', 'api_time', 'Price']],left_on='Username_lower',right_on='Username',how='left',suffixes=('', '_api'))

# merged_df['Date'] = merged_df['Date'].fillna(pd.to_datetime(merged_df['comment_parsed']))
# merged_df['Time'] = merged_df['Time'].fillna(merged_df['api_time'].astype(str))

# to_csv = df_api.to_csv("hotspot_users.csv", index=False)
# mikh = df.to_csv("mikhmon_users.csv", index=False)
# merged = merged_df.to_csv("merged_users.csv", index=False)


def get_all_users():
    """Fetch all hotspot users, skipping first 2 (static?). Returns list of dicts."""
    return api.get_resource('/ip/hotspot/user').get()[2:]

def get_active_connections():
    """Fetch active hotspot connections."""
    return api.get_resource('/ip/hotspot/active').get()

def get_logs():
    """Fetch logs."""
    return api.get_resource('/log').get()

