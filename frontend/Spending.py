import datetime
import urllib
import streamlit as st
import pandas as pd
import altair as alt
import requests

st.set_page_config(layout='wide')

# Fetch initial data to build sidebar filters
all_transactions = requests.get(url='http://fastapi:8000/transactions').json()
df_all_transactions = pd.DataFrame(data=all_transactions)
df_all_transactions['Date'] = pd.to_datetime(df_all_transactions['Date'])

with st.sidebar:
    year = st.selectbox(
        label='Year',
        options=df_all_transactions['Date'].dt.year.unique(),
        index=list(df_all_transactions['Date'].dt.year.unique()).index(datetime.date.today().year)
    )
    month = st.selectbox(
        label='Month',
        options=df_all_transactions['Date'].dt.strftime('%B').unique(),
        index=None
    )

# Get expenses for selected period
if month:
    start_date = datetime.date(
        year=year,
        month=datetime.datetime.strptime(month, '%B').month,
        day=1
    )
    end_date = (start_date.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
else:
    start_date = datetime.date(year=year, month=1, day=1)
    end_date = datetime.date(year=year, month=12, day=31)
expenses_selected_month = requests.get(url=f'http://fastapi:8000/transactions?start_date={start_date}&end_date={end_date}&group=Expenses').json()
df_expenses_selected = pd.DataFrame(data=expenses_selected_month)
df_expenses_selected['Amount'] = df_expenses_selected['Amount'].astype(float)

with st.container(border=True):
    total_expenses, frequent_expenses = st.columns([0.2, 0.8])
    with total_expenses:
        st.write('**Total Spend**')
        st.metric(
            label='Total Spent',
            value='${:,.2f}'.format(df_expenses_selected['Amount'].sum())
        )
    with frequent_expenses:
        st.write('**Most Frequent Expenses**')

        # Get the most common merchants in the current months' transactions
        df_most_common_merchants = df_expenses_selected[['Merchant']].groupby('Merchant').size().reset_index()
        df_most_common_merchants = df_most_common_merchants.rename(columns={0: 'Total Transactions'}).sort_values(by='Total Transactions', ascending=False).head(5)
        merchant1, merchant2, merchant3, merchant4, merchant5 = st.columns(5)
        with merchant1:
            st.metric(
                label=df_most_common_merchants['Merchant'].iloc[0],
                value=f'{df_most_common_merchants['Total Transactions'].iloc[0]}X'
            )
        with merchant2:
            st.metric(
                label=df_most_common_merchants['Merchant'].iloc[1],
                value=f'{df_most_common_merchants['Total Transactions'].iloc[1]}X'
            )
        with merchant3:
            st.metric(
                label=df_most_common_merchants['Merchant'].iloc[2],
                value=f'{df_most_common_merchants['Total Transactions'].iloc[2]}X'
            )
        with merchant4:
            st.metric(
                label=df_most_common_merchants['Merchant'].iloc[3],
                value=f'{df_most_common_merchants['Total Transactions'].iloc[3]}X'
            )
        with merchant5:
            st.metric(
                label=df_most_common_merchants['Merchant'].iloc[4],
                value=f'{df_most_common_merchants['Total Transactions'].iloc[4]}X'
            )

# Group expenses by category
df_expenses_selected_grouped = df_expenses_selected[['Category', 'Amount']].groupby('Category').sum().reset_index()
df_expenses_selected_grouped['Percent'] = df_expenses_selected_grouped['Amount'] / df_expenses_selected_grouped['Amount'].sum()
total_selected_month_expenses = df_expenses_selected_grouped['Amount'].sum()

col_expenses_detailed, col_expenses_widgets = st.columns(spec=[0.6, 0.4])
with col_expenses_detailed:
    with st.container(border=True):
        st.write('**Overall Spend Breakdown**')

        # To get text in center of donut chart, layer text and donut charts
        st.altair_chart(
            alt.Chart(df_expenses_selected_grouped).mark_arc(innerRadius=120).encode(
                theta='Amount',
                color=alt.Color(
                    'Category:N',
                    scale=alt.Scale(scheme='redyellowblue')
                ),
                tooltip=[
                    alt.Tooltip('Category:N', title='Category'),
                    alt.Tooltip('Amount:Q', title='Amount', format='$,.2f'),
                    alt.Tooltip('Percent:Q', title='% of Expenses', format='.1%')
                ]
            ),
            use_container_width=True
        )
with col_expenses_widgets:        
    with st.container(border=True):
        st.write('**Subcategory Spend Breakdown**')
        category = st.selectbox(
            label='Category',
            options=list(df_expenses_selected_grouped['Category'].unique()),
            index=0
        )
        category_param = urllib.parse.quote(category)

        # Get all expenses for the selected category in the current month
        category_expenses = requests.get(url=f'http://fastapi:8000/transactions?start_date={start_date}&end_date={end_date}&group=Expenses&category={category_param}').json()
        df_category_expenses = pd.DataFrame(data=category_expenses)
        df_category_expenses['Amount'] = df_category_expenses['Amount'].astype(dtype=float)
        df_subcategory_expenses = df_category_expenses[['Subcategory', 'Amount']].groupby('Subcategory').sum().reset_index()
        st.altair_chart(
        alt.Chart(df_subcategory_expenses).mark_bar().encode(
            x=alt.X('Amount', axis=alt.Axis(format='$,.0f', title='Amount')),
            y=alt.Y('Subcategory', sort=None, title=None),
            tooltip=[
                alt.Tooltip('Amount', title='Amount', format='$,.2f')
            ]
        ).properties(
            height=265
        ).configure_axis(
            grid=False
        ),
        use_container_width=True
    )

    