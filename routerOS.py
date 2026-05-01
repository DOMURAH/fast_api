import routeros_api

connection = routeros_api.RouterOsApiPool(
    "192.168.1.55",
    username="admin",
    password="1234",
    port=8728,
    plaintext_login=True
)

api = connection.get_api()

active_connections = api.get_resource('/ip/hotspot/active').get()

print(len(active_connections))