import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
import sqlite3

from utils import get_sheets_data

# Load environment variables from .env file
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Define code to run on API startup (before the yield statement) and shutdown (after)."""
    conn = sqlite3.connect('database.db')
    # Store SQLite connection in the app state for later use
    app.state.conn = conn
    sheets_to_read = ['Transaction_Log', 'Net_Worth_Log']  # , 'Investments']
    for sheet in sheets_to_read:
        data = get_sheets_data(
            sheet_id=os.environ['SHEET_ID'],
            sheet_name=sheet
        )
        data.to_sql(
            name=sheet,
            con=conn,
            if_exists='replace',
            index=False
        )
    yield
    conn.close()


app = FastAPI(lifespan=lifespan)


@app.get('/')
def health_check():
    return {'status': 'running'}