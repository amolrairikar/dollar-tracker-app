import datetime
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import requests

st.set_page_config(layout='wide')

# Get detailed net worth data
net_worth_data = requests.get(url='http://fastapi:8000/networth-detailed').json()
df_net_worth_data = pd.DataFrame(net_worth_data)
df_net_worth_data['Balance'] = df_net_worth_data['Balance'].astype(float)
df_net_worth_data_grouped = df_net_worth_data[['Date', 'Category', 'Subcategory', 'Balance']].groupby(['Date', 'Category', 'Subcategory']).sum().reset_index()
df_net_worth_data_grouped['Chart Date'] = pd.to_datetime(df_net_worth_data_grouped['Date'])
df_net_worth_data_grouped['Date'] = df_net_worth_data_grouped['Chart Date'].dt.strftime('%b %Y')
df_asset_allocation_grouped = df_net_worth_data_grouped.copy()
df_asset_allocation_grouped = df_asset_allocation_grouped[['Date', 'Category', 'Balance']].groupby(['Date', 'Category']).sum().reset_index()
df_asset_allocation = pd.merge(
    left=df_net_worth_data_grouped,
    right=df_asset_allocation_grouped,
    on=['Date', 'Category'],
    how='left' 
)
df_asset_allocation = df_asset_allocation.rename(
    columns={
        'Balance_x': 'Balance',
        'Balance_y': 'Total Category Balance'
    }
)
df_asset_allocation = df_asset_allocation[df_asset_allocation['Category'] == 'Asset']
df_asset_allocation['Category Percentage'] = df_asset_allocation['Balance'] / df_asset_allocation['Total Category Balance']

# Get aggregated net worth data
net_worth_data_aggregated = requests.get(url='http://fastapi:8000/networth-aggregated').json()
df_net_worth_data_aggregated = pd.DataFrame(net_worth_data_aggregated)
df_net_worth_data_aggregated['Balance'] = df_net_worth_data_aggregated['Balance'].astype(float)
df_net_worth_data_aggregated['Chart Date'] = pd.to_datetime(df_net_worth_data_aggregated['Date'])
df_net_worth_data_aggregated['Date'] = df_net_worth_data_aggregated['Chart Date'].dt.strftime('%b %Y')
df_net_worth_data_aggregated['Balance'] = np.where(
    df_net_worth_data_aggregated['Category'] == 'Asset',
    df_net_worth_data_aggregated['Balance'],
    df_net_worth_data_aggregated['Balance'] * -1
)
df_net_worth_data_aggregated_grouped = df_net_worth_data_aggregated[['Date', 'Chart Date', 'Balance']].groupby(['Date', 'Chart Date']).sum().reset_index()
df_net_worth_data_aggregated_grouped = df_net_worth_data_aggregated_grouped.sort_values(by='Chart Date', ascending=True)
df_net_worth_data_aggregated_grouped['Pct Change'] = (df_net_worth_data_aggregated_grouped['Balance'] - df_net_worth_data_aggregated_grouped.iloc[0]['Balance']) / df_net_worth_data_aggregated_grouped.iloc[0]['Balance']

# Graph net worth over time
with st.container(border=True):
    st.write('**Net Worth**')
    st.altair_chart(
        alt.Chart(df_net_worth_data_aggregated_grouped).mark_area(point=True).encode(
            x=alt.X('Date:O', title='', sort=alt.EncodingSortField(field='Chart Date'), axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Balance:Q', axis=alt.Axis(format='$,.0f', title='')),
            tooltip=[
                alt.Tooltip('Date:O', title='Date'),
                alt.Tooltip('Balance:Q', title='Balance', format='$,.0f'),
                alt.Tooltip('Pct Change:Q', title='% Change', format='.2%')
            ]
        ).configure_axis(
            grid=False
        ),
        use_container_width=True
    )

st.divider()

with st.container(border=True):
    st.write('**Asset Allocation**')
    st.altair_chart(
        alt.Chart(df_asset_allocation).mark_area(point=True).encode(
            x=alt.X('Date:O', title='', sort=alt.EncodingSortField(field='Chart Date'), axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Balance:Q', axis=alt.Axis(format='$,.0f', title='')).stack('normalize'),
            color=alt.Color('Subcategory:N', scale=alt.Scale(scheme='redyellowblue')),
            tooltip=[
                alt.Tooltip('Date:O', title='Date'),
                alt.Tooltip('Subcategory:N', title='Subcategory'),
                alt.Tooltip('Category Percentage:Q', title='Amount', format='.2%')
            ]
        ).configure_axis(
            grid=False
        )
    )