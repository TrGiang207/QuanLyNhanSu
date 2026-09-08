import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_connection():
    driver = os.getenv("DB_DRIVER", "SQL Server")
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE", "QuanLyNhanSu")
    trusted = os.getenv("DB_TRUSTED_CONNECTION", "yes")
    trust_cert = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")

    if not server:
        raise RuntimeError(
            "Thiếu DB_SERVER trong .env. Ví dụ: DB_SERVER=DESKTOP-62R1KHE\\SQLEXPRESS"
        )

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"Trusted_Connection={trusted};"
        f"TrustServerCertificate={trust_cert};"
    )
    return pyodbc.connect(connection_string)
