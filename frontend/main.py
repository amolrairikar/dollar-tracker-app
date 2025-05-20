import streamlit as st

pages = ['Dashboard.py', 'Spending.py', 'Reports.py', 'Transactions.py', 'Net Worth.py', 'Refresh.py']

pg = st.navigation(pages)
pg.run()