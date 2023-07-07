from datetime import datetime
from dotenv import dotenv_values
from fastapi import FastAPI, Form, HTTPException
import psycopg2
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

config_env = dotenv_values(".env")


class LocalhostMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        client_host = request.client.host
        if client_host != "127.0.0.1" and client_host != "::1":
            raise HTTPException(status_code=403, detail="Access denied")
        response = await call_next(request)
        return response


app.add_middleware(LocalhostMiddleware)


def get_connection():
    username = config_env["HIS_USER"]
    password = config_env["HIS_PASSWORD"]
    host = config_env["HIS_HOST"]
    port = config_env["HIS_PORT"]
    database = config_env["HIS_DATABASE"]

    # Establish the connection
    connection = psycopg2.connect(
        user=username,
        password=password,
        host=host,
        port=port,
        database=database
    )

    return connection


@app.post("/")
async def execute_query(script: str = Form(...)):
    query = script
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print(current_time, " - ", query)

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

            columns = [col[0] for col in cursor.description]
            data = []
            for row in result:
                row_dict = {}
                for i, column in enumerate(columns):
                    row_dict[column] = row[i]
                data.append(row_dict)

            return data

            # return [row for row in result]

    except (Exception, psycopg2.Error) as error:
        return {"message": error}

    finally:
        connection.close()
