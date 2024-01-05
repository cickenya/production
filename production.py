import pandas as pd
import gspread
from google.oauth2 import service_account
import streamlit as st
from st_aggrid import AgGrid
import streamlit_shadcn_ui as ui
from local_components import card_container
from st_aggrid.grid_options_builder import GridOptionsBuilder
import plotly.graph_objects as go
from datetime import timedelta
import base64
import hydralit_components as hc

# Define your Google Sheets credentials JSON file (replace with your own)
credentials_path = 'hackathon-405309-35c43230bdce.json'

# Authenticate with Google Sheets using the credentials
credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=['https://spreadsheets.google.com/feeds'])

# Authenticate with Google Sheets using gspread
gc = gspread.authorize(credentials)

# Your Google Sheets URL
url = "https://docs.google.com/spreadsheets/d/1yQXPZ4zdI8aiIzYXzzuAwDS1V_Zg0fWU6OaqZ_VmwB0/edit#gid=0"

# Open the Google Sheets spreadsheet
worksheet_1 = gc.open_by_url(url).worksheet("accounts")
worksheet_2 = gc.open_by_url(url).worksheet("targets")

#can apply customisation to almost all the properties of the card, including the progress bar
theme_bad = {'bgcolor': '#FFF0F0','title_color': 'red','content_color': 'red','icon_color': 'red', 'icon': 'fa fa-times-circle'}
theme_neutral = {'bgcolor': '#e8d5b7','title_color': 'orange','content_color': '#222831','icon_color': 'orange', 'icon': 'fa fa-question-circle'}
theme_good = {'bgcolor': '#EFF8F7','title_color': 'green','content_color': 'green','icon_color': 'green', 'icon': 'fa fa-check-circle'}

st.set_page_config(page_icon="corplogo.PNG", page_title = 'CIC_PRODUCTION ', layout="wide")

st.sidebar.image('corplogo.PNG', use_column_width=True)

uploaded_file = st.sidebar.file_uploader("Upload Production Listing",  type=['csv', 'xlsx', 'xls'], kwargs=None,)


if uploaded_file is not None:
    try:
        if uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            data_types = {'Policy No': str}
            df = pd.read_excel(uploaded_file, dtype = data_types, header=6)
                      
        elif uploaded_file.type == "text/csv":
            df = pd.read_csv(uploaded_file, header=6)

    except Exception as e:    
        st.write("Error:", e)

if uploaded_file is not None:

    view = st.sidebar.radio('Select',['Company', 'Branch', 'Territorial Manager'])
    df2 = df[["TRANSACTION DATE", "BRANCH", "INTERMEDIARY TYPE", "INTERMEDIARY", "PRODUCT", "PORTFOLIO MIX", "SALES TYPE", "STAMP DUTY", "SUM INSURED", "GROSS PREMIUM", "NET BALANCE", "RECEIPTS", "TM"]]    
    df2.loc[df2['INTERMEDIARY'] == 'GWOKA INSURANCE AGENCY', 'BRANCH'] = 'Head Office'
    
    # Convert the 'Date' column to datetime format
    df2['TRANSACTION DATE'] = pd.to_datetime(df2['TRANSACTION DATE'] , format='%m/%d/%Y')

    # Extract the day of the week, month and create new columns
    df2['DayOfWeek'] = df2['TRANSACTION DATE'].dt.day_name()
    df2['MONTH NAME'] = df2['TRANSACTION DATE'].dt.strftime('%B')
    df2['MONTH NAME'] = df2['MONTH NAME'].str.upper()

   
    # Create a pandas Timestamp object
    most_current_date = df2['TRANSACTION DATE'].max()
    current_date = pd.to_datetime(most_current_date)
    timestamp = pd.Timestamp(current_date)

    current_month = timestamp.strftime('%B')
        
    current_month_name = current_month.upper()

    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)


    # to get the portfolio mix (appears in the STAMP DUTY column)
    df2['STAMP DUTY'] = df2['STAMP DUTY'].astype(str)    
    total_motor_produce = df2[df2['STAMP DUTY'].str.contains('MOTOR')]   

    # Read data from the Google Sheets worksheet
    data = worksheet_1.get_all_values()
    
    # Prepare data for Plotly
    headers = data[0]
    data = data[1:]
    lastdf = pd.DataFrame(data, columns=headers)  # Convert data to a DataFrame
    
    
    jointdf = pd.merge(df2, lastdf, on='INTERMEDIARY', how='left')
    jointdf.loc[jointdf['INTERMEDIARY'].str.contains('REIN', case=False, na=False), 'NEW TM'] = 'REINSURANCE'
    jointdf = jointdf[["TRANSACTION DATE", "BRANCH", "INTERMEDIARY TYPE", "INTERMEDIARY", "PRODUCT", "PORTFOLIO MIX", "SALES TYPE", "SUM INSURED", "GROSS PREMIUM", "NET BALANCE", "RECEIPTS", "NEW TM", "MONTH NAME", "DayOfWeek"]]
    
    newdf = jointdf.dropna(subset='TRANSACTION DATE')
    cancellations = newdf[newdf['GROSS PREMIUM'] < 0]
    new_business = newdf[newdf['SALES TYPE'] == 'New Business']
    new_business_percent = ((new_business['GROSS PREMIUM'].sum())/(newdf['GROSS PREMIUM'].sum()) * 100)
    nbp = "{:,.0f}".format(new_business_percent)


    # WEEK 
    # Get transactions done in the current week
    this_week = newdf[((newdf['TRANSACTION DATE']).dt.date >= start_of_week.date()) & ((newdf['TRANSACTION DATE']).dt.date <= end_of_week.date())]

    week_gp = this_week['GROSS PREMIUM'].sum()
    week_total_gp = "Ksh. {:,.0f}".format(week_gp)

    week_receipted = this_week['RECEIPTS'].sum()
    week_total_receipted = "Ksh. {:,.0f}".format(week_receipted)

    week_credit = this_week['NET BALANCE'].sum()
    week_total_credit = "Ksh. {:,.0f}".format(week_credit)

    week_mix = this_week[this_week['PORTFOLIO MIX'] == 'Motor']
    week_mix_percent = ((week_mix['GROSS PREMIUM'].sum())/(this_week['GROSS PREMIUM'].sum()) * 100)
    week_final_mix = "{:,.0f}".format(week_mix_percent)

    week_new_business = this_week[this_week['SALES TYPE'] == 'New Business']
    week_new_business_percent = ((week_new_business['GROSS PREMIUM'].sum())/(this_week['GROSS PREMIUM'].sum()) * 100)
    week_nbp = "{:,.0f}".format(week_new_business_percent)


    # MOST RECENT (YESTERDAY)
    most_recent_date = newdf[newdf['TRANSACTION DATE'] == newdf['TRANSACTION DATE'].max()]
    first_recent_date = most_recent_date.iloc[-1]   


    friday_df = this_week[this_week['DayOfWeek'] == 'Friday']
    friday = friday_df['GROSS PREMIUM'].sum()
    friday_cancelled = friday_df[friday_df['GROSS PREMIUM'] < 0]['GROSS PREMIUM'].sum()
    friday_receipts = friday_df[friday_df['RECEIPTS'] > 0]['RECEIPTS'].sum()
    friday_credits = friday_df['NET BALANCE'].sum()
    
    saturday_df = this_week[this_week['DayOfWeek'] == 'Saturday']
    saturday = saturday_df['GROSS PREMIUM'].sum()
    saturday_receipts = saturday_df[saturday_df['RECEIPTS'] > 0]['RECEIPTS'].sum()
    saturday_credits = saturday_df['NET BALANCE'].sum()
    saturday_cancelled = saturday_df[saturday_df['GROSS PREMIUM'] < 0]['GROSS PREMIUM'].sum()
    
    sunday_df = this_week[this_week['DayOfWeek'] == 'Sunday']
    sunday = sunday_df['GROSS PREMIUM'].sum()
    sunday_receipts = sunday_df[sunday_df['RECEIPTS'] > 0]['RECEIPTS'].sum()
    sunday_credits = sunday_df['NET BALANCE'].sum()
    sunday_cancelled = sunday_df[sunday_df['GROSS PREMIUM'] < 0]['GROSS PREMIUM'].sum()

   
    if first_recent_date.iloc[0].weekday() == 4:
        yesterday = friday
        yesterday_receipts_total = friday_receipts
        yesterday_credit_total = friday_credits
        cancelled_yesterday = friday_cancelled
        
    elif first_recent_date.iloc[0].weekday() == 5:
        yesterday = (friday + saturday)
        yesterday_receipts_total = friday_receipts + saturday_receipts
        yesterday_credit_total = (friday_credits + saturday_credits)
        cancelled_yesterday = friday_cancelled + saturday_cancelled
        
    elif first_recent_date.iloc[0].weekday() == 6:
        yesterday = (friday + saturday+ sunday)
        yesterday_receipts_total = sunday_receipts
        yesterday_credit_total = (friday_credits + saturday_credits + sunday_credits)
        cancelled_yesterday = friday_cancelled + saturday_cancelled + sunday_cancelled
        
    else:
        yesterday = most_recent_date['GROSS PREMIUM'].sum()
        yesterday_receipts = most_recent_date[most_recent_date['RECEIPTS'] > 0].sum()
        yesterday_credit_total = most_recent_date[most_recent_date['NET BALANCE']>0].sum()
        cancelled_yesterday = most_recent_date[most_recent_date['GROSS PREMIUM'] < 0].sum()
       

    fom_yesterday_premium = "Ksh. {:,.0f}".format(yesterday)    
    fom_yesterday_receipts = "Ksh. {:,.0f}".format(yesterday_receipts_total)    
    fom_yesterday_credit = "Ksh. {:,.0f}".format(yesterday_credit_total)  
    amount_yesterday_cancelled = "Ksh. {:,.0f}".format(cancelled_yesterday)

    # THIS MONTH
    this_month = newdf[newdf['MONTH NAME'] == current_month_name]

    month_gp = this_month['GROSS PREMIUM'].sum()
    month_total_gp = "Ksh. {:,.0f}".format(month_gp)

    month_receipted = this_month['RECEIPTS'].sum()
    month_total_receipted = "Ksh. {:,.0f}".format(month_receipted)

    month_credit = this_month['NET BALANCE'].sum()
    month_total_credit = "Ksh. {:,.0f}".format(month_credit)

    month_mix = this_month[this_month['PORTFOLIO MIX'] == 'Motor']
    month_mix_percent = ((month_mix['GROSS PREMIUM'].sum())/(this_month['GROSS PREMIUM'].sum()) * 100)
    month_final_mix = "{:,.0f}".format(month_mix_percent)
    
    month_new_business = this_month[this_month['SALES TYPE'] == 'New Business']
    month_new_business_percent = ((month_new_business['GROSS PREMIUM'].sum())/(this_month['GROSS PREMIUM'].sum()) * 100)
    month_nbp = "{:,.0f}".format(month_new_business_percent)

    

    # Group by and sum with additional text columns
    preview = newdf.groupby('INTERMEDIARY').agg({
        'GROSS PREMIUM': 'sum',
        'BRANCH': 'first',  
        'NEW TM': 'first',  
     
    })
    
    # Sort the results from highest to lowest and take the top 5 rows
    preview_sorted = preview.sort_values(by='GROSS PREMIUM', ascending=False).head(10)

    if view == 'Company':
         # Convert the 'Date' column to datetime format
        df2['TRANSACTION DATE'] = pd.to_datetime(df2['TRANSACTION DATE'], format='%m/%d/%Y')

        
        # Check if there are no January dates
        no_january_dates = (df2['TRANSACTION DATE'].dt.month != 1).all()

        # Display warning if there are no January dates
        if no_january_dates:       
            st.warning("Kindly Upload Year to Date Data.")
        
        else:


            motor = total_motor_produce[total_motor_produce['STAMP DUTY'] == 'MOTOR']
            nonmotor = total_motor_produce[total_motor_produce['STAMP DUTY'] == 'NON-MOTOR']
            motorproduce = motor['GROSS PREMIUM'].sum()
            nonmotorproduce = nonmotor['GROSS PREMIUM'].sum()
            

            totalmix = (motorproduce+nonmotorproduce)
            total_mix_result = "{:,.0f}".format(totalmix)
            mix = (motorproduce/ totalmix)*100
            mix_result = "{:.0f}".format(mix)
            
            
            bar = newdf.groupby('MONTH NAME')['GROSS PREMIUM'].sum().reset_index()

            bar2 = newdf.groupby('BRANCH')['GROSS PREMIUM'].sum().reset_index()
            
            month_bar = this_month.groupby('BRANCH')['GROSS PREMIUM'].sum().reset_index()
            
            week_bar = this_week.groupby('BRANCH')['GROSS PREMIUM'].sum().reset_index()
            week_bar2 = this_week.groupby('DayOfWeek')['GROSS PREMIUM'].sum().reset_index()

            total_amount = f"Ksh.{this_week['GROSS PREMIUM'].sum():,}"

            bar['Percentage'] = (bar['GROSS PREMIUM']/(bar['GROSS PREMIUM'].sum()) * 100)
                
                
            gp = newdf['GROSS PREMIUM'].sum()
            total_gp = "Ksh. {:,.0f}".format(gp)

            receipted = newdf['RECEIPTS'].sum()
            total_receipted = "Ksh. {:,.0f}".format(receipted)

            credit = newdf['NET BALANCE'].sum()
            total_credit = "Ksh. {:,.0f}".format(credit)

            tab_one, tab_two, tab_three, tab_four = st.tabs(["Year to Date", "Month to Date", "Week To Date", "Yesterday"])
            
            with tab_one:
                st.subheader('YEAR TO DATE PRODUCTION SUMMARY')

                with card_container(key="year"):
                    cc = st.columns(5)

                    with cc[0]:
                    # can just use 'good', 'bad', 'neutral' sentiment to auto color the card
                        hc.info_card(title='Production', content= f'Ksh. {total_mix_result}', sentiment='good',bar_value=77, content_text_size = 'medium', title_text_size='medium')
            
                    with cc[1]:
                        hc.info_card(title='Receipted', content=f'{total_receipted}',bar_value=12, sentiment='good', content_text_size = 'medium', title_text_size='medium')
            
                    with cc[2]:
                        hc.info_card(title='Credit', content=f'{total_credit}', sentiment='neutral',bar_value=55, content_text_size = 'medium', title_text_size='medium')
            
                    with cc[3]:
                        hc.info_card(title='New Business', content=f'{nbp}%',bar_value=44, title_text_size='medium', sentiment='good',  content_text_size = 'medium')
            
                    with cc[4]:
                        hc.info_card(title='Portfolio Mix',content= f'{mix_result}% Motor',key='sec',bar_value=75, content_text_size = 'medium', sentiment='good', title_text_size='medium')
                
                tab1, tab2, tab3= st.tabs(["📈 Company Production Summary", "Branch Performance", "🗃 Top Producing Intermediaries"])
                with tab1:
                    with card_container(key="year_tabs"):
                
                
                        fig2 = go.Figure()
                
                        fig2.add_trace(go.Bar(
                                width= 0.5,
                                x= bar['MONTH NAME'],
                                y= bar['GROSS PREMIUM'],       
                                ))
                        
                
                        fig2.update_layout(title={'text': 'MONTHLY AGGREGATE PRODUCTION', 'x': 0.5, 'xanchor': 'center'}, width=975, xaxis=dict(categoryorder='array', categoryarray=["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"], tickfont=dict(size=10))) 
                
                        
                        st.plotly_chart(fig2)

                with tab2:                     
                    
                    with card_container(key="year_chart_tab2"):
                
                        fig3 = go.Figure()
                
                        fig3.add_trace(go.Bar(
                                width= 0.75,
                                x= bar2['BRANCH'],
                                y= bar2['GROSS PREMIUM'],       
                                ))
                        
                
                        fig3.update_layout(title={'text': 'BRANCH PERFORMANCE', 'x': 0.5, 'xanchor': 'center'}, width=975) 
                
                        
                        st.plotly_chart(fig3)



                with tab3:          
                    sorted_prev = pd.DataFrame(preview_sorted)
            
                    st.subheader("**Intermediaries with the Highest Production**")
                    st.dataframe(sorted_prev)


            with tab_two:
                # Check if it's the first day of the month or if the third day of the month is a Monday
                if current_date.day == 1 or (current_date.day == 3 and current_date.monthday() == 0):  # 0 represents Monday
                    # Subtract one month to get the previous month
                    previous_month = current_date - timedelta(days=current_date.day)
                    previous_month_name = previous_month.strftime('%B').upper()
    
                    # Use the previous month's name in the header
                    st.subheader(f"{previous_month_name} PRODUCTION SUMMARY - TARGET KES 45M")
                else:
                    # Use the current month's name in the header
                    current_month_name = current_date.strftime('%B').upper()
                    st.subheader(f"{current_month_name} PRODUCTION SUMMARY - TARGET KES 45M")
                        
                with card_container(key="month_chart"):
                    cc = st.columns(5)

                    with cc[0]:
                    # can just use 'good', 'bad', 'neutral' sentiment to auto color the card
                        hc.info_card(title='Production', content= f'{month_total_gp}', sentiment='good',bar_value=77, key='mth_prod', content_text_size = 'medium', title_text_size='medium')
            
                    with cc[1]:
                        hc.info_card(title='Receipted', content=f'{month_total_receipted}',bar_value=12, sentiment='good', key='mth_rec', content_text_size = 'medium', title_text_size='medium')
            
                    with cc[2]:
                        hc.info_card(title='Credit', content=f'{month_total_credit}', sentiment='neutral',bar_value=55, key='mth_cr', content_text_size = 'medium', title_text_size='medium')
            
                    with cc[3]:
                        hc.info_card(title='New Business', content=f'{month_nbp}%',bar_value=44, title_text_size='medium', key='mth_biz', sentiment='good',  content_text_size = 'medium')
            
                    with cc[4]:
                        hc.info_card(title='Portfolio Mix', content=f'{month_final_mix}% Motor',bar_value=44, title_text_size='medium', key='mth_mix', sentiment='good',  content_text_size = 'medium')


                tab1, tab2 = st.tabs(["📈 This Month Production Summary", "🗃 Preview This Month Data"])
                with tab1:
                    with card_container(key="month_tabs"):
                        cols2 = st.columns(2)
                
                        fig = go.Figure()
                
                        fig.add_trace(go.Bar(
                
                                width=0.5,
                                x= month_bar["BRANCH"],
                                y= month_bar["GROSS PREMIUM"]        
                                ))
                
                        fig.update_layout(title={'text': 'MONTH TO DATE BRANCH PERFORMANCE', 'x': 0.5, 'xanchor': 'center'}, width=450) 
                
                        with cols2[0]: 
                            st.plotly_chart(fig)
                
                        with cols2[1]: 
                            # Group by quarters
                            
                            this_month['QUARTERS'] = pd.cut(this_month['TRANSACTION DATE'].dt.day, bins=[0, 7, 14, 21, 31], labels=["1st Quarter", "2nd Quarter", "3rd Quarter", "4th Quarter"], include_lowest=True)

                            # Calculate sum of production for each quarter
                            qs = this_month.groupby('QUARTERS')['GROSS PREMIUM'].sum().reset_index()

                    
                            fig2 = go.Figure()
                    
                            fig2.add_trace(go.Bar(
                                    width=0.45,
                                    x= qs['QUARTERS'],
                                    y= qs['GROSS PREMIUM']        
                                    ))
                            
                    
                            fig2.update_layout(title={'text': 'MONTH PRODUCTION ANALYSIS', 'x': 0.5, 'xanchor': 'center'}, width=475, xaxis=dict(categoryorder='array', categoryarray=["1st Quarter", "2nd Quarter", "3rd Quarter", "4th Quarter"], tickfont=dict(size=12)))
                            
                            st.plotly_chart(fig2)

                with tab2:
                    st.subheader("**Preview of this Month's Data**")
                    month_df = this_month[["NEW TM", "INTERMEDIARY", "TRANSACTION DATE", "PRODUCT", "GROSS PREMIUM", "NET BALANCE", "RECEIPTS", ]]
                    
                    st.dataframe(month_df)
                    

                
            with tab_three:
                st.subheader('WEEK TO DATE PRODUCTION SUMMARY')

                with card_container(key="week_chart_one"):
                    cc = st.columns(5)

                    with cc[0]:
                    # can just use 'good', 'bad', 'neutral' sentiment to auto color the card
                        hc.info_card(title='Production', content= f'{week_total_gp}', sentiment='good',bar_value=77, key='week_prod', content_text_size = 'medium', title_text_size='medium')
            
                    with cc[1]:
                        hc.info_card(title='Receipted', content=f'{week_total_receipted}',bar_value=12, sentiment='good', key='week_rec', content_text_size = 'medium', title_text_size='medium')
            
                    with cc[2]:
                        hc.info_card(title='Credit', content=f'{week_total_credit}', sentiment='neutral',bar_value=55, key='week_cr', content_text_size = 'medium', title_text_size='medium')
            
                    with cc[3]:
                        hc.info_card(title='New Business', content=f'{week_nbp}%',bar_value=44, title_text_size='medium', key='week_biz', sentiment='good',  content_text_size = 'medium')
            
                    with cc[4]:
                        hc.info_card(title='Portfolio Mix', content=f'{week_final_mix}% Motor',bar_value=44, title_text_size='medium', key='week_mix', sentiment='good',  content_text_size = 'medium')
            
                    
                tab1, tab2 = st.tabs(["📈 This Week Production Summary", "🗃 Preview This Week Data"])
                with tab1:
                    with card_container(key="chart_two"):
                        week_cols = st.columns(2)

                        fig = go.Figure()
                
                        fig.add_trace(go.Bar(
                
                                width=0.5,
                                x= week_bar["BRANCH"],
                                y= week_bar["GROSS PREMIUM"]        
                                ))
                
                        fig.update_layout(title={'text': 'MONTH TO DATE BRANCH PERFORMANCE', 'x': 0.5, 'xanchor': 'center'}, width=450) 
                

                        fig2 = go.Figure()
                
                        fig2.add_trace(go.Bar(
                                width=0.5,
                                x= week_bar2['DayOfWeek'],
                                y= week_bar2['GROSS PREMIUM'],       
                                ))
                        
                        fig2.update_layout(title={'text': 'THIS WEEK AGGREGATE DAILY PRODUCTION', 'x': 0.5, 'xanchor': 'center'}, width=550, xaxis=dict(categoryorder='array', categoryarray=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], tickfont=dict(size=12))) 

                        with week_cols[0]: 
                            st.plotly_chart(fig)
                
                        with week_cols[1]: 
                            st.plotly_chart(fig2)
                        

                with tab2:
                    st.subheader('**Preview of the Uploaded Data Frame**')
                    this_week = this_week[["NEW TM", "INTERMEDIARY", "TRANSACTION DATE", "PRODUCT", "GROSS PREMIUM", "NET BALANCE", "RECEIPTS", ]]
                    st.dataframe(this_week)


            with tab_four:
                most_recent_longdate = df2['TRANSACTION DATE'].max()

                # Ensure most_recent_date is a single datetime object
                if isinstance(most_recent_longdate, pd.Series):
                    most_recent_longdate = most_recent_longdate.iloc[0]
                    
                formatted_date = most_recent_longdate.strftime('%A %d %B') 
                st.subheader(f'{formatted_date} Production Summary')
                
                with card_container(key="chart4"):
                    yesterday_cc= st.columns(4)

                    with yesterday_cc[0]:
                    # can just use 'good', 'bad', 'neutral' sentiment to auto color the card
                        hc.info_card(title= 'Yesterday Production', content= f'{fom_yesterday_premium}', sentiment='good',  key = 'yst_prod', title_text_size='small', bar_value=77, content_text_size='medium')
            
                    with yesterday_cc[1]:
                        hc.info_card(title='Yesterday Receipted', content=f'{fom_yesterday_receipts}',bar_value=12,  key = 'yst_rcpt', title_text_size='small', sentiment='good', content_text_size='medium')
            
                    with yesterday_cc[2]:
                        hc.info_card(title='Yesterday On Credit', content=f'{fom_yesterday_credit}', sentiment='neutral', key = 'yst_crd', title_text_size='small', bar_value=55, content_text_size='medium')
            
                    with yesterday_cc[3]:
                        hc.info_card(title='Yesterday Cancellations', content=f'{amount_yesterday_cancelled}',bar_value=2, key = 'yst_canc', sentiment='bad',title_text_size='small', content_text_size = 'medium')
            
                    tab1, tab2 = st.tabs(["📈 Yesterday Production Summary", "🗃 Preview Yesterday's Data"])
                    with tab1:
                        with card_container(key="yesterday_tabs"):
                        
                            yesterday = most_recent_date.groupby('NEW TM')['GROSS PREMIUM'].sum().reset_index()

                            fig = go.Figure()
                
                            fig.add_trace(go.Bar(
                    
                                    width=0.5,
                                    x= yesterday["NEW TM"],
                                    y= yesterday["GROSS PREMIUM"]        
                                    ))
                    
                            fig.update_layout(title={'text': 'YESTERDAY ACCOUNT MANAGERS PRODUCTION SUMMARY', 'x': 0.5, 'xanchor': 'center'}, width=850) 
                
                            st.plotly_chart(fig)
                
                        
                    with tab2 : 
                        st.dataframe(most_recent_date)
                            

    if view == 'Branch':
        unique = newdf['BRANCH'].unique()

        selected_branch =st.sidebar.selectbox("Choose Branch", unique)

        # Filter the DataFrame based on the selected branch
        filtered_df = newdf[newdf['BRANCH'] == selected_branch]
        filtered_df2 = this_week[this_week['BRANCH'] == selected_branch]
        
        for_cancellation =  cancellations[cancellations['BRANCH'] == selected_branch]

        nonmotordf = filtered_df[~filtered_df['PRODUCT'].str.contains('Motor')]
        motordf = filtered_df[filtered_df['PRODUCT'].str.contains('Motor')]
        nonmotor = nonmotordf['GROSS PREMIUM'].sum()
        motor = motordf['GROSS PREMIUM'].sum()
        cancelled = for_cancellation['GROSS PREMIUM'].sum()
        amount_cancelled = "Ksh. {:,.0f}".format(cancelled)
        total_mix = (motor+nonmotor)
        total_mix_result = "{:,.0f}".format(total_mix)
        mix = (motor/total_mix)*100
        mix_result = "{:.0f}".format(mix)

        bar_df = filtered_df.groupby('NEW TM')['GROSS PREMIUM'].sum()

        gp = filtered_df['GROSS PREMIUM'].sum()
        
        total_gp = "Ksh. {:,.0f}".format(gp)

        receipted = filtered_df['RECEIPTS'].sum()
        total_receipted = "Ksh. {:,.0f}".format(receipted)

        credit = filtered_df['NET BALANCE'].sum()
        total_credit = "Ksh. {:,.0f}".format(credit)

        st.subheader(f"{selected_branch} Branch Month To Date Production")

        with card_container(key="chart1"):
            cc = st.columns(5)
    
            with cc[0]:
            # can just use 'good', 'bad', 'neutral' sentiment to auto color the card
                hc.info_card(title='Production', content= f'Ksh. {total_mix_result}', content_text_size = 'medium',sentiment='good',bar_value=77, title_text_size='small')
    
            with cc[1]:
                hc.info_card(title='Receipted', content=f'{total_receipted}',bar_value=12, content_text_size = 'medium', sentiment='good', title_text_size='small')
    
            with cc[2]:
                hc.info_card(title='Credit', content=f'{total_credit}', sentiment='neutral', content_text_size = 'medium', bar_value=55, title_text_size='small')
    
            with cc[3]:
                hc.info_card(title='Cancelled', content=f'{amount_cancelled}',bar_value=2, sentiment='bad',title_text_size='small', content_text_size = 'medium')
    
            with cc[4]:
                hc.info_card(title='Portfolio Mix',content=f'{mix_result}% Motor ',key='sec', bar_value=5, content_text_size = 'medium', sentiment='good', title_text_size='small')

        
        bar_df = filtered_df.groupby('NEW TM')['GROSS PREMIUM'].sum().reset_index()
        bar_df2 = filtered_df2.groupby('DayOfWeek')['GROSS PREMIUM'].sum().reset_index()

        with card_container(key="chart2"):
            cols3 = st.columns(2)
    
            fig = go.Figure()
    
            fig.add_trace(go.Bar( 
                 width=0.5,
                 x= bar_df['NEW TM'],
                 y= bar_df['GROSS PREMIUM']      
                 ))

            fig.update_layout(title={'text': 'TERRITORIAL MANAGER PERFORMANCE IN BRANCH', 'x': 0.5, 'xanchor': 'center'}, width=525, xaxis=dict(tickfont=dict(size=9))) 
    
            with cols3[0]: 
                st.plotly_chart(fig)
    
    
            fig2 = go.Figure()
    
            fig2.add_trace(go.Bar(
                    width=0.45,
                     x= bar_df2['DayOfWeek'],
                     y= bar_df2['GROSS PREMIUM']        
                     ))
            
    
            fig2.update_layout(title={'text': 'THIS WEEK DAILY PRODUCTION', 'x': 0.5, 'xanchor': 'center'}, width=425, xaxis=dict(categoryorder='array', categoryarray=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], tickfont=dict(size=9)))
    
            with cols3[1]: 
                st.plotly_chart(fig2)

    if view == 'Territorial Manager':
        unique = newdf['NEW TM'].unique()

        data = worksheet_2.get_all_values()
        headers = data[0]
        data = data[1:]
        target = pd.DataFrame(data, columns=headers)  # Convert data to a DataFrame

        target['NEW TM'] = target['NEW TM'].str.strip()
        target['MONTH'] = target['MONTH'].str.strip() 
        target['NEW TM'] = target['NEW TM'].str.strip() 
        selected_manager =st.sidebar.selectbox("Choose TM", unique)

        for_cancellation =  cancellations[(cancellations['NEW TM'] == selected_manager) & (cancellations['MONTH NAME'] == current_month_name)]
      

        # Filter the DataFrame based on the selected branch
        filtered_df = newdf[(newdf['NEW TM'] == selected_manager)]
        filtered_target = target[(target['NEW TM'] == selected_manager) & (target['MONTH'] == current_month_name)]
        total = int(filtered_target['TOTAL'].sum())
        target_total = "{:,.0f}".format(total)
        daily = (total/20)
        weekly = (total/4)
        target_daily = "{:,.0f}".format(daily)
        target_weekly = "{:,.0f}".format(weekly)
        
        month_premium = filtered_df['GROSS PREMIUM'].sum()
        fom_month_premium = "Ksh. {:,.0f}".format(month_premium)
        month_receipts = filtered_df['RECEIPTS'].sum()
        fom_month_receipts = "Ksh. {:,.0f}".format(month_receipts)
        month_credit = filtered_df['NET BALANCE'].sum()
        fom_month_credit = "Ksh. {:,.0f}".format(month_credit)
        month_receipts = filtered_df[filtered_df['RECEIPTS'] > 0]
        month_receipts_total = month_receipts['RECEIPTS'].sum()
        fom_month_receipts = "Ksh. {:,.0f}".format(month_receipts_total)
        month_credit = filtered_df[filtered_df['NET BALANCE'] > 0]
        month_credit_total = month_credit['NET BALANCE'].sum()
        fom_week_credit = "Ksh. {:,.0f}".format(month_credit_total) 
        

        most_current_date = newdf['TRANSACTION DATE'].max()
        current_date = pd.to_datetime(most_current_date)
        most_recent = filtered_df[filtered_df['TRANSACTION DATE'] == current_date]
        
        # daily_cancellation =  cancellations[(cancellations['NEW TM'] == selected_manager) & (cancellations['TRANSACTION DATE'] == most_current_date)]

        friday_df = this_week[(this_week['DayOfWeek'] == 'Friday') & (this_week['NEW TM'] == selected_manager) ]
        friday = friday_df['GROSS PREMIUM'].sum()
        friday_cancelled = friday_df[friday_df['GROSS PREMIUM'] < 0]['GROSS PREMIUM'].sum()
        friday_receipts = friday_df[friday_df['RECEIPTS'] > 0]['RECEIPTS'].sum()
        friday_credits = friday_df['NET BALANCE'].sum()
        
        saturday_df = this_week[(this_week['DayOfWeek'] == 'Saturday') & (this_week['NEW TM'] == selected_manager)]
        saturday = saturday_df['GROSS PREMIUM'].sum()
        saturday_receipts = saturday_df[saturday_df['RECEIPTS'] > 0]['RECEIPTS'].sum()
        saturday_credits = saturday_df['NET BALANCE'].sum()
        saturday_cancelled = saturday_df[saturday_df['GROSS PREMIUM'] < 0]['GROSS PREMIUM'].sum()
        
        sunday_df = this_week[(this_week['DayOfWeek'] == 'Sunday') & (this_week['NEW TM'] == selected_manager)]
        sunday = sunday_df['GROSS PREMIUM'].sum()
        sunday_receipts = sunday_df[sunday_df['RECEIPTS'] > 0]['RECEIPTS'].sum()
        sunday_credits = sunday_df['NET BALANCE'].sum()
        sunday_cancelled = sunday_df[sunday_df['GROSS PREMIUM'] < 0]['GROSS PREMIUM'].sum()
    
       
        if first_recent_date.iloc[0].weekday() == 4:
            yesterday = friday
            yesterday_receipts_total = friday_receipts
            yesterday_credit_total = friday_credits
            cancelled_yesterday = friday_cancelled
            
        elif first_recent_date.iloc[0].weekday() == 5:
            yesterday = (friday + saturday)
            yesterday_receipts_total = friday_receipts + saturday_receipts
            yesterday_credit_total = (friday_credits + saturday_credits)
            cancelled_yesterday = friday_cancelled + saturday_cancelled
            
        elif first_recent_date.iloc[0].weekday() == 6:
            yesterday = (friday + saturday+ sunday)
            yesterday_receipts_total = sunday_receipts
            yesterday_credit_total = (friday_credits + saturday_credits + sunday_credits)
            cancelled_yesterday = friday_cancelled + saturday_cancelled + sunday_cancelled
            
        else:
            yesterday = most_recent['GROSS PREMIUM'].sum()
            yesterday_receipts = most_recent[most_recent['RECEIPTS'] > 0].sum()
            yesterday_credit_total = most_recent[most_recent['NET BALANCE']>0].sum()
            cancelled_yesterday = most_recent[most_recent['GROSS PREMIUM'] < 0].sum()
           

        
      
        fom_day_premium = "Ksh. {:,.0f}".format(yesterday)       
        fom_day_receipts = "Ksh. {:,.0f}".format(yesterday_receipts_total)        
        fom_day_credit = "Ksh. {:,.0f}".format(yesterday_credit_total)
        amount_daily_cancelled = "Ksh. {:,.0f}".format(cancelled_yesterday)
               

        monthly_cancelled = for_cancellation['GROSS PREMIUM'].sum()
        amount_cancelled = "Ksh. {:,.0f}".format(monthly_cancelled)      
        

        filtered_df['TRANSACTION DATE'] = pd.to_datetime(filtered_df['TRANSACTION DATE'])

      
        # Ensure 'TRANSACTION DATE' is a datetime object
        if pd.api.types.is_datetime64_any_dtype(filtered_df['TRANSACTION DATE']):
            # Calculate the start date of the current week (Monday)
            start_of_week = most_current_date - timedelta(days=most_current_date.dayofweek)

            # Filter data for payments from Monday of the current week to the most recent date
            filtered_data = filtered_df[(filtered_df['TRANSACTION DATE'] >= start_of_week) & (filtered_df['TRANSACTION DATE'] <= most_current_date)]


        else:
            print("The 'TRANSACTION DATE' column is not in datetime format.")
            
        week_premium = filtered_data['GROSS PREMIUM'].sum()
        fom_week_premium = "Ksh. {:,.0f}".format(week_premium)
        week_receipts = filtered_data[filtered_data['RECEIPTS'] > 0]
        week_receipts_total = week_receipts['RECEIPTS'].sum()
        fom_week_receipts = "Ksh. {:,.0f}".format(week_receipts_total)
        week_credit = filtered_data[filtered_data['NET BALANCE'] > 0]
        week_credit_total = filtered_data['NET BALANCE'].sum()
        fom_week_credit = "Ksh. {:,.0f}".format(week_credit_total)   
        week_cancelled = filtered_data[filtered_data['SUM INSURED'] < 0]
        total_cancelled = week_cancelled['GROSS PREMIUM'].sum()
        week_total_cancelled = "Ksh. {:,.0f}".format(total_cancelled)   


        # Create a DataFrame without an index
        table_data = pd.DataFrame({
            ' ': [f'{selected_manager} TARGETS'],
            'MONTHLY': [f'Ksh. {target_total}'],
            'WEEKLY': [f'Ksh. {target_weekly}'],
            'DAILY': [f'Ksh. {target_daily}']
        })
        
        # Display the table
    
        with card_container(key="chart"):
            ui.table(data=table_data)
            #st.write(table_data.style.set_properties(**{'text-align': 'center'}).to_html(index=False, escape=False), unsafe_allow_html=True)
                        
        with card_container(key="chart1"):
            cc= st.columns(4)

            with cc[0]:
            # can just use 'good', 'bad', 'neutral' sentiment to auto color the card
                hc.info_card(title= 'Month To Date Production', content= f'{fom_month_premium}', sentiment='good',  title_text_size='small', bar_value=77, content_text_size='medium')
    
            with cc[1]:
                hc.info_card(title='Month To Date Receipted', content=f'{fom_month_receipts}',bar_value=12,  title_text_size='small', sentiment='good', content_text_size='medium')
    
            with cc[2]:
                hc.info_card(title='Month To Date On Credit', content=f'{fom_month_credit}', sentiment='neutral',  title_text_size='small', bar_value=55, content_text_size='medium')
    
            with cc[3]:
                hc.info_card(title='Month To Date Cancellations', content=f'{amount_cancelled}',bar_value=2, key ='month_cancellation', sentiment='bad',title_text_size='small', content_text_size = 'medium')
    
            cc_row1 = st.columns(4)
    
            with cc_row1[0]:
            # can just use 'good', 'bad', 'neutral' sentiment to auto color the card
                hc.info_card(title= 'Week To Date Production', content= f'{fom_week_premium}', key = 'week_premium', sentiment='good',bar_value=77, content_text_size='medium', title_text_size='small')
    
            with cc_row1[1]:
                hc.info_card(title='Week To Date Receipted', content=f'{fom_week_receipts}', key='week_receipt', bar_value=12, sentiment='good', content_text_size='medium',title_text_size='small')
    
            with cc_row1[2]:
                hc.info_card(title='Week To Date On Credit', content=f'{fom_week_credit}', key='week_credit', sentiment='neutral',bar_value=55, content_text_size='medium', title_text_size='small')
    
            with cc_row1[3]:
                hc.info_card(title='Week To Date Cancellations', content=f'{week_total_cancelled}', key='week_cancelled', sentiment='bad',bar_value=55, content_text_size='medium',title_text_size='small')
            
            
            
            cc_row2 = st.columns(4)
    
            with cc_row2[0]:
            # can just use 'good', 'bad', 'neutral' sentiment to auto color the card
                hc.info_card(title='Yesterday Production', content= f'{fom_day_premium}', sentiment='good',bar_value=77, key='day_premium', content_text_size='medium', title_text_size='small')
    
            with cc_row2[1]:
                hc.info_card(title='Yesterday Receipted', content= f'{fom_day_receipts}',bar_value=12, key='day_receipts', sentiment='good',  content_text_size='medium', title_text_size='small')
    
            with cc_row2[2]:
                hc.info_card(title='Yesterday On Credit', content=f'{fom_day_credit}', key='day_credit', sentiment='neutral', bar_value=55, content_text_size='medium', title_text_size='small')
    
            with cc_row2[3]:
                hc.info_card(title='Yesterday Cancellations', content=f'{amount_daily_cancelled}',bar_value=2, key='cancelled', sentiment='bad',title_text_size='small', content_text_size = 'medium')



        griddf2 = filtered_df[["NEW TM", "INTERMEDIARY", "TRANSACTION DATE", "PRODUCT", "GROSS PREMIUM", "NET BALANCE", "RECEIPTS", ]]
        gd = GridOptionsBuilder.from_dataframe(griddf2) 
        select = st.radio('', options = ['multiple'])
        gd.configure_selection(selection_mode = select, use_checkbox=True)
        gridoptions = gd.build()
        st.subheader(f"**PREVIEW OF {selected_manager}'S DATA**")

        AgGrid(griddf2, gridOptions=gridoptions)

        if st.button("Download CSV"):
            csv_data = griddf2.to_csv(index=False, encoding='utf-8')
            b64 = base64.b64encode(csv_data.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="{selected_manager}.csv">Download CSV</a>'
            st.markdown(href, unsafe_allow_html=True) 
