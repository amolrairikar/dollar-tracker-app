import urllib
import streamlit as st
import pandas as pd
import requests

st.set_page_config(layout='wide')

# Fetch initial data to build sidebar filters
all_transactions = requests.get(url='http://fastapi:8000/transactions').json()
df_all_transactions = pd.DataFrame(data=all_transactions)
df_all_transactions['Date'] = pd.to_datetime(df_all_transactions['Date'])
df_all_transactions['Amount'] = df_all_transactions['Amount'].astype(float)

operator_map = {
    '<': 'lt',
    '<=': 'lte',
    '=': 'eq',
    '>=': 'gte',
    '>': 'gt'
}

# Define default session state
DEFAULT_FILTERS = {
    "date_range": [],
    "merchant": "",
    "amount_op": None,
    "amount": 0.0,
    "group": None,
    "category": None,
    "subcategory": None,
    "account": None,
}

# Initialize defaults if not already set
for key, val in DEFAULT_FILTERS.items():
    if key not in st.session_state:
        st.session_state[key] = val

with st.sidebar:
    if st.button('Clear Filters'):
        for key, val in DEFAULT_FILTERS.items():
            st.session_state[key] = val
        st.rerun()

    st.date_input(
        label='Date',
        min_value=df_all_transactions['Date'].min(),
        max_value=df_all_transactions['Date'].max(),
        key='date_range'
    )

    st.text_input(
        label='Merchant',
        key='merchant'
    )

    st.selectbox(
        label='Amount Comparison',
        options=operator_map.keys(),
        index=None,
        key='amount_op'
    )

    st.number_input(
        label='Amount',
        step=10,
        key='amount'
    )

    st.selectbox(
        label='Group',
        options=sorted(df_all_transactions['Group'].unique()),
        index=None,
        key='group'
    )

    if st.session_state.group:
        st.selectbox(
            label='Category',
            options=sorted(df_all_transactions[df_all_transactions['Group'] == st.session_state.group]['Category'].unique()),
            index=None,
            key='category'
        )
    else:
        st.selectbox(
            label='Category',
            options=sorted(df_all_transactions['Category'].unique()),
            index=None,
            key='category'
        )

    if st.session_state.category:
        st.selectbox(
            label='Subcategory',
            options=sorted(df_all_transactions[df_all_transactions['Category'] == st.session_state.category]['Subcategory'].unique()),
            index=None,
            key='subcategory'
        )
    else:
        st.selectbox(
            label='Subcategory',
            options=sorted(df_all_transactions['Subcategory'].unique()),
            index=None,
            key='subcategory'
        )

    st.selectbox(
        label='Account',
        options=sorted(df_all_transactions['Account'].unique()),
        index=None,
        key='account'
    )

# Build filter params
params = {}
dr = st.session_state.date_range
if dr:
    if len(dr) == 1:
        params['start_date'] = dr[0].strftime('%Y-%m-%d')
    elif len(dr) == 2:
        params['start_date'] = dr[0].strftime('%Y-%m-%d')
        params['end_date'] = dr[1].strftime('%Y-%m-%d')

# Add each parameter to Streamlit session state
if st.session_state.merchant:
    params['merchant'] = st.session_state.merchant
if st.session_state.amount_op:
    params['amount_op'] = operator_map[st.session_state.amount_op]
if st.session_state.amount:
    params['amount'] = str(st.session_state.amount)
if st.session_state.group:
    params['group'] = st.session_state.group
if st.session_state.category:
    params['category'] = st.session_state.category
if st.session_state.subcategory:
    params['subcategory'] = st.session_state.subcategory
if st.session_state.account:
    params['account'] = st.session_state.account

if params:
    if len(params.keys()) == 1 and ('amount' in params or 'amount_op' in params):
        param_string = ''
    else:
        param_string = urllib.parse.urlencode(params)
else:
    param_string = ''

filtered_transactions = requests.get(f'http://fastapi:8000/transactions?{param_string}').json()
df_filtered_transactions = pd.DataFrame(filtered_transactions).sort_values(by='Date', ascending=False)
st.subheader('**Transactions**')
st.dataframe(
    data=df_filtered_transactions,
    hide_index=True,
    height=500,
    column_config={
        'Date': st.column_config.DateColumn(label='Date'),
        'Merchant': st.column_config.TextColumn(label='Merchant'),
        'Amount': st.column_config.NumberColumn(label='Amount', format='dollar'),
        'Group': st.column_config.TextColumn(label='Group'),
        'Category': st.column_config.TextColumn(label='Category'),
        'Subcategory': st.column_config.TextColumn(label='Subcategory'),
        'Account': st.column_config.TextColumn(label='Account'),
    }
)
