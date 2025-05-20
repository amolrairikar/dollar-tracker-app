import streamlit as st
import requests

if st.button('Refresh Data Now'):
    try:
        response = requests.post('http://fastapi:8000/refresh-data')
        if response.ok:
            st.success('Data refreshed successfully!')
        else:
            st.error(f'Failed to refresh data: {response.text}')
    except Exception as e:
        st.error(f'Error: {e}')