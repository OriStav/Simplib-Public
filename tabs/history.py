import streamlit as st
import pandas as pd
from datetime import datetime

from tabs.stats import render_stats_calculations

def render_history_table(stats_df):

    st.subheader("🗂️ טבלת השאלות")
    stats_df = stats_df.fillna("")
    # Add search functionality
    loaner_options = sorted((stats_df['name_loaner'].fillna('') + ' ' + stats_df['surname'].fillna('')).str.strip())
    book_options = sorted(stats_df['name_book'].unique().tolist() + stats_df['author'].unique().tolist())
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        search_term = st.selectbox("🔍 חיפוש לפי שם משאיל או ספר", 
                                 options=[''] + list(set(loaner_options + book_options)),
                                 placeholder='בחר/י שם משאיל או ספר')
    
    # Filter data based on search term
    filtered_stats = stats_df.copy()
    if search_term:
        filtered_stats = filtered_stats[
            (stats_df['name_loaner'] + ' ' + stats_df['surname']).str.contains(search_term, case=False) |
            filtered_stats['name_book'].str.contains(search_term, case=False) |
            filtered_stats['author'].str.contains(search_term, case=False)
        ]
    
    loans_columns = {
        'name_loaner': st.column_config.TextColumn('👤 שם פרטי', width=150),
        'surname': st.column_config.TextColumn('👥 שם משפחה', width=150),
        'name_book': st.column_config.TextColumn('📖 שם הספר', width=250),
        'author': st.column_config.TextColumn('✍️ מחבר', width=150),
        'loan_date': st.column_config.TextColumn('📅 תאריך השאלה', width=150),
        'return_date': st.column_config.TextColumn('📅 תאריך החזרה', width=150),
        'loan_duration': st.column_config.NumberColumn('⏳ משך השאלה - ימים', width=200)
    }
    current = (datetime.today() - pd.to_datetime(filtered_stats['loan_date'], format='%d/%m/%Y')).dt.days
    filtered_stats['loan_duration'] = filtered_stats['loan_duration'].fillna(current)
    st.dataframe(
        filtered_stats[list(loans_columns.keys())[::-1]],
        column_config=loans_columns,
        hide_index=True,
        use_container_width=True
    )