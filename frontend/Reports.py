import datetime
import dateutil
import dateutil.relativedelta
import streamlit as st
import pandas as pd
import altair as alt
import requests

st.set_page_config(layout='wide')

def check_date_in_range(start_date: datetime.date, end_date: datetime.date, check_date: datetime.date) -> bool:
    """Checks if check_date is between start_date and end_date, inclusive."""
    if start_date <= check_date <= end_date:
        return True
    return False


with st.sidebar:
    aggregation_period = st.selectbox(
        label='Report Granularity',
        options=['Monthly', 'Quarterly', 'Yearly'],
        index=0
    )
    number_periods = st.selectbox(
        label='Number of Reporting Periods',
        options=list(range(4, 13)),
        index=2
    )

# Get start date for reporting
if aggregation_period == 'Monthly':
    start_date = datetime.date.today().replace(day=1) - dateutil.relativedelta.relativedelta(months=number_periods-1)
elif aggregation_period == 'Quarterly':
    if check_date_in_range(
        start_date=datetime.date(year=datetime.date.today().year, month=1, day=1),
        end_date=datetime.date(year=datetime.date.today().year, month=3, day=31),
        check_date=datetime.date.today()
    ):
        start_date = datetime.date(year=datetime.date.today().year, month=1, day=1) - dateutil.relativedelta.relativedelta(months=(number_periods-1)*3)
    elif check_date_in_range(
        start_date=datetime.date(year=datetime.date.today().year, month=4, day=1),
        end_date=datetime.date(year=datetime.date.today().year, month=6, day=30),
        check_date=datetime.date.today()
    ):
        start_date = datetime.date(year=datetime.date.today().year, month=4, day=1) - dateutil.relativedelta.relativedelta(months=(number_periods-1)*3)
    elif check_date_in_range(
        start_date=datetime.date(year=datetime.date.today().year, month=7, day=1),
        end_date=datetime.date(year=datetime.date.today().year, month=9, day=30),
        check_date=datetime.date.today()
    ):
        start_date = datetime.date(year=datetime.date.today().year, month=7, day=1) - dateutil.relativedelta.relativedelta(months=(number_periods-1)*3)
    elif check_date_in_range(
        start_date=datetime.date(year=datetime.date.today().year, month=10, day=1),
        end_date=datetime.date(year=datetime.date.today().year, month=12, day=31),
        check_date=datetime.date.today()
    ):
        start_date = datetime.date(year=datetime.date.today().year, month=10, day=1) - dateutil.relativedelta.relativedelta(months=(number_periods-1)*3)
elif aggregation_period == 'Yearly':
    start_date = datetime.date.today().replace(month=1, day=1) - dateutil.relativedelta.relativedelta(years=number_periods-1)

# Get income transactions
income_transactions = requests.get(url=f'http://fastapi:8000/transactions?start_date={start_date}&group=Income').json()
df_income_transactions = pd.DataFrame(data=income_transactions)
df_income_transactions['Date'] = pd.to_datetime(df_income_transactions['Date'])
df_income_transactions['Amount'] = df_income_transactions['Amount'].astype(dtype=float)
if aggregation_period == 'Monthly':
    df_income_transactions['Group Period'] = df_income_transactions['Date'].apply(lambda x: pd.to_datetime(x).strftime('%b %Y'))
elif aggregation_period == 'Quarterly':
    df_income_transactions['Group Period'] = 'Q' + df_income_transactions['Date'].dt.quarter.astype(str) + ' ' + df_income_transactions['Date'].dt.year.astype(str)
elif aggregation_period == 'Yearly':
    df_income_transactions['Group Period'] = df_income_transactions['Date'].apply(lambda x: pd.to_datetime(x).strftime('%Y'))
df_income_grouped = df_income_transactions[['Group Period', 'Amount']].groupby('Group Period').sum().reset_index()
df_income_grouped = df_income_grouped.rename(columns={'Amount': 'Income'})
if aggregation_period == 'Monthly':
    df_income_grouped['Date'] = pd.to_datetime(df_income_grouped['Group Period'], format='%b %Y')
elif aggregation_period == 'Quarterly':
    df_income_grouped['Date'] = pd.to_datetime(df_income_grouped['Group Period'].str.replace(r'Q([1-4]) (\d{4})', r'\2-\1', regex=True)).apply(lambda d: pd.Timestamp(d.year, 3 * (d.month - 1) + 1, 1))
elif aggregation_period == 'Yearly':
    df_income_grouped['Date'] = pd.to_datetime(df_income_grouped['Group Period'], format= '%Y')
df_income_grouped = df_income_grouped.sort_values(by='Date', ascending=True)

# Get income transactions
expense_transactions = requests.get(url=f'http://fastapi:8000/transactions?start_date={start_date}&group=Expenses').json()
df_expense_transactions = pd.DataFrame(data=expense_transactions)
df_expense_transactions['Date'] = pd.to_datetime(df_expense_transactions['Date'])
df_expense_transactions['Amount'] = df_expense_transactions['Amount'].astype(dtype=float)
if aggregation_period == 'Monthly':
    df_expense_transactions['Group Period'] = df_expense_transactions['Date'].apply(lambda x: pd.to_datetime(x).strftime('%b %Y'))
elif aggregation_period == 'Quarterly':
    df_expense_transactions['Group Period'] = 'Q' + df_expense_transactions['Date'].dt.quarter.astype(str) + ' ' + df_expense_transactions['Date'].dt.year.astype(str)
elif aggregation_period == 'Yearly':
    df_expense_transactions['Group Period'] = df_expense_transactions['Date'].apply(lambda x: pd.to_datetime(x).strftime('%Y'))
df_expenses_grouped = df_expense_transactions[['Group Period', 'Amount']].groupby('Group Period').sum().reset_index()
df_expenses_grouped = df_expenses_grouped.rename(columns={'Amount': 'Expenses'})
if aggregation_period == 'Monthly':
    df_expenses_grouped['Date'] = pd.to_datetime(df_expenses_grouped['Group Period'], format='%b %Y')
elif aggregation_period == 'Quarterly':
    df_expenses_grouped['Date'] = pd.to_datetime(df_expenses_grouped['Group Period'].str.replace(r'Q([1-4]) (\d{4})', r'\2-\1', regex=True)).apply(lambda d: pd.Timestamp(d.year, 3 * (d.month - 1) + 1, 1))
elif aggregation_period == 'Yearly':
    df_expenses_grouped['Date'] = pd.to_datetime(df_expenses_grouped['Group Period'], format= '%Y')
df_expenses_grouped = df_expenses_grouped.sort_values(by='Date', ascending=True)


cash_flow_tab, spending_tab, income_tab = st.tabs(tabs=['Cash Flow', 'Spending', 'Income'])
with cash_flow_tab:
    with st.container(border=True):
        # Get dataframe with income and expenses in same row for cash flow chart
        df_cash_flow = pd.merge(left=df_income_grouped, right=df_expenses_grouped, on='Group Period', how='inner')
        df_cash_flow['Expenses'] = df_cash_flow['Expenses'] * -1
        df_cash_flow['Cash Flow'] = df_cash_flow['Income'] + df_cash_flow['Expenses']
        df_cash_flow = df_cash_flow.drop(columns=['Date_y'])
        df_cash_flow = df_cash_flow.rename(columns={'Date_x': 'Date'})

        st.altair_chart(
            alt.Chart(df_cash_flow).mark_bar().encode(
                x=alt.X('Group Period:O', title='', sort=alt.EncodingSortField(field='Date'), axis=alt.Axis(labelAngle=0)),
                y=alt.Y('Cash Flow:Q', stack='zero', axis=alt.Axis(format='$,.0f', title='')),
                tooltip=[
                    alt.Tooltip('Income:Q', title='Income', format='$,.2f'),
                    alt.Tooltip('Expenses:Q', title='Expenses', format='$,.2f'),
                    alt.Tooltip('Cash Flow:Q', title='Cash Flow', format='$,.2f')
                ]
            ).properties(
                title='Cash Flow'
            ).configure_axis(
                grid=False
            )
        )

    # Create table style report
    st.divider()
    with st.container(border=True):
        period, income, expenses, cash_flow = st.columns(4)
        with period:
            st.write('**Reporting Period**')
            for _, row in df_cash_flow.iterrows():
                st.write(row['Group Period'])
        with income:
            st.write('**Income**')
            for _, row in df_cash_flow.iterrows():
                st.write('${:,.2f}'.format(row['Income']))
        with expenses:
            st.write('**Expenses**')
            for _, row in df_cash_flow.iterrows():
                st.write('${:,.2f}'.format(row['Expenses']*-1))
        with cash_flow:
            st.write('**Cash Flow**')
            for _, row in df_cash_flow.iterrows():
                st.write('${:,.2f}'.format(row['Cash Flow']))

with spending_tab:
    with st.container(border=True):
        category = st.selectbox(
            label='Category',
            options=sorted(df_expense_transactions['Category'].unique()),
            index=0
        )
        df_category_expenses = df_expense_transactions[df_expense_transactions['Category'] == category]
        st.altair_chart(
            alt.Chart(df_category_expenses).mark_bar().encode(
                x=alt.X('Group Period:O', sort=alt.EncodingSortField(field='Date'), axis=alt.Axis(title='', labelAngle=0)),
                y=alt.Y('sum(Amount):Q', axis=alt.Axis(format='$,.0f', title='Amount')),
                xOffset='Subcategory:N',
                color=alt.Color('Subcategory:N', scale=alt.Scale(scheme='redyellowblue')),
                tooltip=[
                    alt.Tooltip('Subcategory:N', title='Subcategory'),
                    alt.Tooltip('sum(Amount):Q', title='Amount', format='$,.2f')
                ]
            ).configure_axis(
                grid=False
            ),
            use_container_width=True
        )

with income_tab:
    with st.container(border=True):
        category = st.selectbox(
            label='Category',
            options=sorted(df_income_transactions['Category'].unique()),
            index=1
        )
        df_category_income = df_income_transactions[df_income_transactions['Category'] == category]
        st.altair_chart(
            alt.Chart(df_category_income).mark_bar().encode(
                x=alt.X('Group Period:O', sort=alt.EncodingSortField(field='Date'), axis=alt.Axis(title='', labelAngle=0)),
                y=alt.Y('sum(Amount):Q', axis=alt.Axis(format='$,.0f', title='Amount')),
                xOffset='Subcategory:N',
                color=alt.Color('Subcategory:N', scale=alt.Scale(scheme='redyellowblue')),
                tooltip=[
                    alt.Tooltip('Subcategory:N', title='Subcategory'),
                    alt.Tooltip('sum(Amount):Q', title='Amount', format='$,.2f')
                ]
            ).configure_axis(
                grid=False
            ),
            use_container_width=True
        )