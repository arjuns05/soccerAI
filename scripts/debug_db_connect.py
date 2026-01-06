from app.config import settings
from app.db import engine

print("PG_HOST:", settings.pg_host)
print("PG_PORT:", settings.pg_port)
print("PG_DB:", settings.pg_db)
print("PG_USER:", settings.pg_user)
print("PG_PASSWORD_SET:", bool(settings.pg_password))

with engine.connect() as c:
    print("✅ connected")
    print(c.exec_driver_sql("select current_user, inet_server_addr(), inet_server_port()").fetchone())
