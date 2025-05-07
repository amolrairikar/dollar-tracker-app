import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from utils import get_sheets_data, Operator
from models import Transaction, NetWorthDetail, NetWorthAggregate

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

engine = create_engine('sqlite:///./database.db', connect_args={'check_same_thread': False})


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Define code to run on API startup (before the yield statement) and optionally
        shutdown (after the yield statement).
    
    Args:
        - app (FastAPI): The FastAPI application instance.
    """
    sheets_to_read = ['Transaction_Log', 'Net_Worth_Log']
    for sheet in sheets_to_read:
        data = get_sheets_data(
            sheet_id=os.environ['SHEET_ID'],
            sheet_name=sheet
        )
        with engine.connect() as conn:
            data.to_sql(
                name=sheet,
                con=conn,
                if_exists='replace',
                index=False
            )
    yield

app = FastAPI(lifespan=lifespan)

@app.get('/')
def health_check():
    """Simple health check endpoint to verify if the API is running."""
    return {'status': 'running'}


@app.get('/transactions', response_model=list[Transaction])
def get_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
    merchant: str | None = None,
    amount_op: Operator | None = None,
    amount: float | None = None,
    group: str | None = None,
    category: str | None = None,
    subcategory: str | None = None,
    account: str | None = None
):
    """Fetch transactions with optional filters applied using query parameters
        to get a subset of transactions.
        
    Args:
        - start_date (str): Start date, inclusive (YYYY-MM-DD)
        - end_date (str): End date, inclusive (YYYY-MM-DD)
        - merchant (str): Merchant name
        - amount_op (Operator): Operator for filtering transaction amounts (lt, lte, eq, gt, gte)
        - amount (float): Transaction amount to use in filter
        - group (str): Transaction group name ("Income", "ExpenseS", "Savings")
        - category (str): Category name (e.g, "Food & Drink", "Pets", "Utilities")
        - subcategory (str): Subcategory name corresponding to a category (e.g, "Food & Drink" -> "Groceries")
        - account (str): Account name that made the transaction
    
    Returns:
        - list[Transaction]: List of transactions matching the filters

    Raises:
        - HTTPException: If either amount or amount_op are specified without the other.
    """
    logger.info('Received request with params: %s', {
        'start_date': start_date,
        'end_date': end_date,
        'merchant': merchant,
        'amount_op': amount_op,
        'amount': amount,
        'group': group,
        'category': category,
        'subcategory': subcategory,
        'account': account
    })
    if (amount_op and not amount) or (amount and not amount_op):
        raise HTTPException(
            status_code=400,
            detail='Both amount and amount_op must be provided together.'
        )
    base_query = 'SELECT * FROM Transaction_Log WHERE 1=1'
    operator_map = {
        'lt': '<',
        'lte': '<=',
        'eq': '=',
        'gte': '>=',
        'gt': '>'
    }
    params = {}
    if start_date:
        base_query += ' AND "Date" >= :start_date'
        params['start_date'] = start_date
    if end_date:
        base_query += ' AND "Date" <= :end_date'
        params['end_date'] = end_date
    if merchant:
        base_query += ' AND Merchant = :merchant'
        params['merchant'] = merchant
    if amount_op and amount:
        base_query += f' AND Amount {operator_map[amount_op]} :amount'
        params['amount'] = amount
    if group:
        base_query += ' AND "Group" = :group'
        params['group'] = group
    if category:
        base_query += ' AND Category = :category'
        params['category'] = category
    if subcategory:
        base_query += ' AND Subcategory = :subcategory'
        params['subcategory'] = subcategory
    if account:
        base_query += ' AND Account = :account'
        params['account'] = account
    logger.info('Executing query: %s', base_query)
    logger.info('With params: %s', params)
    with engine.connect() as connection:
        result = connection.execute(text(base_query), params)
        logger.info('Fetched %d rows', result.rowcount)
        return [Transaction(**dict(row._mapping)) for row in result]


@app.get('/networth-detailed', response_model=list[NetWorthDetail])
def get_networth(
    start_date: str | None = None,
    end_date: str | None = None,
    account: str | None = None,
    category: str | None = None
):
    """Fetch detailed net worth entries for each account, with optional query
        parameters to filter the result set.
        
    Args:
        - start_date (str): Start date, inclusive (YYYY-MM-DD)
        - end_date (str): End date, inclusive (YYYY-MM-DD)
        - account (str): Account name
        - category (str): Category name ("Asset" or "Liability")
        
    Returns:
        - list[NetWorthDetail]: List of net worth entries matching the filters
    """
    logger.info('Received request with params: %s', {
        'start_date': start_date,
        'end_date': end_date,
        'account': account,
        'category': category
    })
    base_query = 'SELECT * FROM Net_Worth_Log WHERE 1=1'
    params = {}
    if start_date:
        base_query += ' AND "Date" >= :start_date'
        params['start_date'] = start_date
    if end_date:
        base_query += ' AND "Date" <= :end_date'
        params['end_date'] = end_date
    if account:
        base_query += ' AND Account = :account'
        params['account'] = account
    if category:
        base_query += ' AND Category = :category'
        params['category'] = category
    logger.info('Executing query: %s', base_query)
    logger.info('With params: %s', params)
    with engine.connect() as connection:
        result = connection.execute(text(base_query), params)
        logger.info('Fetched %d rows', result.rowcount)
        return [dict(row._mapping) for row in result]


@app.get('/networth-aggregated', response_model=list[NetWorthAggregate])
def get_networth(
    start_date: str | None = None,
    end_date: str | None = None
):
    """Fetch net worth aggregate entries with optional filters for start and end date.
        A sum of assets and liabilities is returned for each date with an entry.
        
    Args:
        - start_date (str): Start date, inclusive (YYYY-MM-DD)
        - end_date (str): End date, inclusive (YYYY-MM-DD)
    
    Returns:
        - list[NetWorthAggregate]: List of net worth aggregate entries matching the filters
    """
    logger.info('Received request with params: %s', {
        'start_date': start_date,
        'end_date': end_date
    })
    base_query = 'SELECT "Date", Category, SUM(Balance) AS Balance FROM Net_Worth_Log WHERE 1=1'
    params = {}
    if start_date:
        base_query += ' AND "Date" >= :start_date'
        params['start_date'] = start_date
    if end_date:
        base_query += ' AND "Date" <= :end_date'
        params['end_date'] = end_date
    base_query += ' GROUP BY "Date", Category ORDER BY "Date", Category ASC'
    logger.info('Executing query: %s', base_query)
    logger.info('With params: %s', params)
    with engine.connect() as connection:
        result = connection.execute(text(base_query), params)
        logger.info('Fetched %d rows', result.rowcount)
        return [dict(row._mapping) for row in result]
    