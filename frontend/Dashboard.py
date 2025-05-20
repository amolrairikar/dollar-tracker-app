import datetime
import streamlit as st
from streamlit.components.v1 import html
import requests
import pandas as pd
import altair as alt

st.set_page_config(layout='wide')

col1, col2 = st.columns(spec=[0.5, 0.5])
with col1:
    with st.container(border=True):
        # Fetch detailed net worth breakdown
        net_worth_details = requests.get(url='http://fastapi:8000/networth-detailed').json()
        df_net_worth_details = pd.DataFrame(data=net_worth_details)
        df_net_worth_details['Balance'] = df_net_worth_details['Balance'].astype(dtype=float)

        # Get the most recent date net worth was recorded
        most_recent_date = df_net_worth_details['Date'].max()

        # Fetch net worth as of most recent recorded date
        net_worth_aggregate = requests.get(url=f'http://fastapi:8000/networth-aggregated?start_date={most_recent_date}').json()
        df_net_worth_aggregate = pd.DataFrame(data=net_worth_aggregate)
        net_worth = float(df_net_worth_aggregate['Balance'].iloc[0]) - float(df_net_worth_aggregate['Balance'].iloc[1])
        st.write('**Net Worth**')
        st.metric(label='Your Net Worth', value='${:,.2f}'.format(net_worth))
        assets, liabilities = st.tabs(tabs=['Assets', 'Liabilities'])
        with assets:

            # Create horizontal stacked bar chart with asset components
            df_assets = df_net_worth_details[(df_net_worth_details['Date'] == most_recent_date) & (df_net_worth_details['Category'] == 'Asset')]
            df_assets_grouped = df_assets[['Subcategory', 'Balance']].groupby('Subcategory').sum().reset_index()
            df_assets_grouped['Percent'] = df_assets_grouped['Balance'] / df_assets_grouped['Balance'].sum()
            df_assets_grouped['Bar'] = 'Total'

            # In the legend label, include the asset category and percentage for easy viewing
            df_assets_grouped['Subcategory_Label'] = df_assets_grouped.apply(lambda row: f"{row['Subcategory']} ({row['Percent']*100:.1f}%)", axis=1)
            st.altair_chart(
                alt.Chart(df_assets_grouped).mark_bar().encode(
                    x=alt.X('Percent:Q', stack='normalize', axis=None),
                    y=alt.Y('Bar:N', axis=None),
                    color=alt.Color(
                        'Subcategory_Label:N',
                        scale=alt.Scale(scheme='purpleblue'),
                        legend=alt.Legend(title=None, orient='bottom')
                    ),
                    tooltip=['Subcategory', alt.Tooltip('Percent:Q', format='.2%')]
                )
            )

            # Create an expander for each asset category
            asset_categories = df_assets_grouped['Subcategory'].unique()
            for category in asset_categories:
                category_balance = df_assets_grouped[df_assets_grouped['Subcategory'] == category]['Balance'].sum()
                with st.expander(label=f'{category}: {'${:,.2f}'.format(category_balance)}', expanded=False):
                    df_category = df_assets[df_assets['Subcategory'] == category].sort_values(by='Account', ascending=True)
                    with st.container():
                        col_account, col_balance = st.columns(spec=[0.75, 0.25])
                        for _, row in df_category.iterrows():
                            with col_account:
                                st.write(row['Account'])
                            with col_balance:
                                st.write('${:,.2f}'.format(row['Balance']))
        with liabilities:

            # Create horizontal stacked bar chart with liability components
            df_liabilities = df_net_worth_details[(df_net_worth_details['Date'] == most_recent_date) & (df_net_worth_details['Category'] == 'Liability')]
            df_liabilities_grouped = df_liabilities[['Subcategory', 'Balance']].groupby('Subcategory').sum().reset_index()
            df_liabilities_grouped['Percent'] = df_liabilities_grouped['Balance'] / df_liabilities_grouped['Balance'].sum()
            df_liabilities_grouped['Bar'] = 'Total'

            # In the legend label, include the liability category and percentage for easy viewing
            df_liabilities_grouped['Subcategory_Label'] = df_liabilities_grouped.apply(lambda row: f"{row['Subcategory']} ({row['Percent']*100:.1f}%)", axis=1)
            st.altair_chart(
                alt.Chart(df_liabilities_grouped).mark_bar().encode(
                    x=alt.X('Percent:Q', stack='normalize', axis=None),
                    y=alt.Y('Bar:N', axis=None),
                    color=alt.Color(
                        'Subcategory_Label:N',
                        scale=alt.Scale(scheme='redpurple'),
                        legend=alt.Legend(title=None, orient='bottom')
                    ),
                    tooltip=['Subcategory', alt.Tooltip('Percent:Q', format='.2%')]
                )
            )

            # Create an expander for each liability category
            liability_categories = df_liabilities_grouped['Subcategory'].unique()
            for category in liability_categories:
                category_balance = df_liabilities_grouped[df_liabilities_grouped['Subcategory'] == category]['Balance'].sum()
                with st.expander(label=f'{category}: {'${:,.2f}'.format(category_balance)}', expanded=False):
                    df_category = df_liabilities[df_liabilities['Subcategory'] == category].sort_values(by='Account', ascending=True)
                    with st.container():
                        col_account, col_balance = st.columns(spec=[0.85, 0.15])
                        for _, row in df_category.iterrows():
                            with col_account:
                                st.write(row['Account'])
                            with col_balance:
                                st.write('${:,.2f}'.format(row['Balance']))
with col2:
    with st.container(border=True):
        st.write('**Spending**')

        # Get spending data for current and previous month
        start_of_current_month = datetime.date.today().replace(day=1)
        start_of_previous_month = (start_of_current_month - datetime.timedelta(days=1)).replace(day=1)
        end_of_previous_month = start_of_current_month - datetime.timedelta(days=1)
        current_month_expenses = requests.get(url=f'http://fastapi:8000/transactions?start_date={start_of_current_month}&group=Expenses').json()
        previous_month_expenses = requests.get(url=f'http://fastapi:8000/transactions?start_date={start_of_previous_month}&end_date={end_of_previous_month}&group=Expenses').json()
        df_current_month_expenses = pd.DataFrame(data=current_month_expenses)
        df_previous_month_expenses = pd.DataFrame(data=previous_month_expenses)
        total_expenses_current_month = df_current_month_expenses['Amount'].astype(dtype=float).sum()
        st.metric(label='Spent this month', value = '${:,.0f}'.format(total_expenses_current_month))

        # Get data in format for chart visualizing current month vs. previous month cumulative spending
        for df, label in zip([df_current_month_expenses, df_previous_month_expenses], ['Current Month', 'Previous Month']):
            df['Date'] = pd.to_datetime(df['Date'])
            df['Amount'] = df['Amount'].astype(float)
            df['Cumulative'] = df['Amount'].cumsum()
            df['Day'] = df['Date'].dt.day
            df['Source'] = label
        df_combined = pd.concat([df_current_month_expenses, df_previous_month_expenses])
        df_combined_aggregated = df_combined.groupby(['Day', 'Source'], as_index=False).agg(
            {'Cumulative': 'last'}
        )
        st.altair_chart(
            alt.Chart(df_combined_aggregated).mark_line().encode(
                x=alt.X('Day:O', title=None),
                y=alt.Y('Cumulative:Q', axis=alt.Axis(format='$~s', title='')),
                color=alt.Color(
                    'Source:N',
                    scale=alt.Scale(
                        domain=['Current Month', 'Previous Month'],
                        range=['#055789', '#d7d7ea']
                    ),
                    legend=alt.Legend(title=None, orient='bottom')
                ),
                tooltip=[
                    alt.Tooltip('Day:O', title='Day'),
                    alt.Tooltip('Cumulative:Q', title='Cumulative Amount', format='$,.2f')
                ]
            ).properties(
                height=250,
            ).configure_axis(
                grid=False,
                domain=False
            ),
            use_container_width=True
        )
        st.write('**Latest Transactions**')

        # Get the 5 most recent transactions
        df_current_month_expenses = df_current_month_expenses.sort_values(by='Date', ascending=False).head(5)
        for _, row in df_current_month_expenses.iterrows():
            with st.container():
                col_date, col_merchant, col_amount = st.columns([0.25, 0.5, 0.25])
                with col_date:
                    st.write(row['Date'].strftime('%Y-%m-%d'))
                with col_merchant:
                    st.write(row['Merchant'])
                with col_amount:
                    st.write('${:,.2f}'.format(row['Amount']))
