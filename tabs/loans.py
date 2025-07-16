import streamlit as st
import pandas as pd
from datetime import datetime
import time
from methods.utils import calculate_metrics, save_loans
import time
def render_loans_tab(books_df, loaners_df, loans_df):
    """Render the loans tab content"""
    metrics = calculate_metrics(books_df, loaners_df, loans_df)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("📖 השאלות")
    with col2:
        st.metric("📚 השאלות פעילות", metrics['active_loans'])
    with col3:
        st.metric("⚠️ השאלות באיחור", metrics['late_loans'])
    
    # Create two columns for new loan and return book forms
    col1, col2 = st.columns(2)
    
    # New Loan section
    with col1:
        render_new_loan_form(books_df, loaners_df, loans_df)
    
    # Return Book section
    with col2:
        render_return_book_form(books_df, loaners_df, loans_df)
    
    st.markdown("---")
    render_active_loans(books_df, loaners_df, loans_df)
    
    st.markdown("---")
    render_late_loans(books_df, loaners_df, loans_df)

def render_new_loan_form(books_df, loaners_df, loans_df):
    """Render the new loan form"""
    st.subheader("➕ השאלה חדשה")
    
    # Get available books (not currently loaned)
    loaned_book_ids = loans_df[loans_df['return_date'].isna()]['book_id'].unique()
    available_books = books_df[~books_df['id'].isin(loaned_book_ids)]
    
    # Create form
    with st.form("new_loan_form"):
        selected_book = st.selectbox("בחר ספר", ['']+available_books['name'].tolist())
        selected_loaner = st.selectbox("בחר משאיל", ['']+list(loaners_df['name'] + ' ' + loaners_df['surname']))
        loan_date = st.date_input("תאריך השאלה", datetime.now(), format='DD/MM/YYYY')
        
        submitted = st.form_submit_button("צור השאלה")
        
        if submitted:
            book_id = available_books[available_books['name'] == selected_book]['id'].iloc[0]
            loaner_id = loaners_df[loaners_df['name'] + ' ' + loaners_df['surname'] == selected_loaner]['id'].iloc[0]
            
            new_loan = pd.DataFrame({
                'loaner_id': [loaner_id],
                'book_id': [book_id],
                'loan_date': [loan_date.strftime('%d/%m/%Y')],
                'return_date': [None]
            })
            
            loans_df = pd.concat([loans_df, new_loan], ignore_index=True)
            save_loans(loans_df)
            st.success("ההשאלה נוצרה בהצלחה!")
            time.sleep(0.5)
            st.rerun()

def render_return_book_form(books_df, loaners_df, loans_df):
    """Render the return book form"""
    st.subheader("↩️ החזרת ספר")
    
    # Get active loans
    active_loans = loans_df[loans_df['return_date'].isna()]
    active_loans = active_loans.merge(books_df, left_on='book_id', right_on='id', how='left')
    active_loans = active_loans.merge(loaners_df, left_on='loaner_id', right_on='id', how='left', suffixes=('_book', '_loaner'))
    
    if not active_loans.empty:
        with st.form("return_book_form"):
            selected_loan = st.selectbox(
                "בחר השאלה להחזרה",
                ['']+list(active_loans['name_book'] + ' - ' + active_loans['name_loaner'] + ' ' + active_loans['surname'])
            )
            return_date = st.date_input("תאריך החזרה", datetime.now(), format='DD/MM/YYYY')
            
            submitted = st.form_submit_button("החזר ספר")
            
            if submitted:
                # Find the row in active_loans that matches the selected loan
                matched_row = active_loans[
                    (active_loans['name_book'] + ' - ' + active_loans['name_loaner'] + ' ' + active_loans['surname']) == selected_loan
                ].iloc[0]

                # Find the corresponding index in loans_df (by loaner_id, book_id, and loan_date)
                mask = (
                    (loans_df['loaner_id'] == matched_row['loaner_id']) &
                    (loans_df['book_id'] == matched_row['book_id']) &
                    (loans_df['loan_date'] == matched_row['loan_date'])
                )
                loans_df.loc[mask, 'return_date'] = return_date.strftime('%d/%m/%Y')
                save_loans(loans_df)
                st.success("הספר הוחזר בהצלחה!")
                time.sleep(0.5)
                st.rerun()
    else:
        st.info("אין השאלות פעילות להחזרה.")

def render_active_loans(books_df, loaners_df, loans_df):
    """Render the active loans section"""
    st.subheader("📖 השאלות פעילות")
    
    # Merge loans with book and loaner information first
    current_loans = loans_df.merge(books_df, left_on='book_id', right_on='id', how='left', suffixes=('_loan', '_book'))
    current_loans = current_loans.merge(loaners_df, left_on='loaner_id', right_on='id', how='left', suffixes=('_book', '_loaner'))
    
    # Create options list from active loans
    active_loans = current_loans[current_loans['return_date'].isna()]
    loan_duration = (datetime.today() - pd.to_datetime(active_loans['loan_date'],format='%d/%m/%Y')).dt.days
    active_loans = pd.concat([active_loans, loan_duration.rename('loan_duration')], axis=1)
    active_loans = active_loans.fillna("")
    books_df =books_df.fillna("")
    # Create search options
    book_options = sorted(active_loans['name_book'].unique().tolist() + active_loans['author'].unique().tolist())
    loaner_options = sorted(active_loans['name_loaner'] + ' ' + active_loans['surname'])
    search_options = [''] + list(set(book_options + loaner_options))
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        search_term = st.selectbox("🔍 חיפוש לפי שם ספר, מחבר, או משאיל", 
                                 options=search_options,
                                 placeholder='בחר/י לחיפוש...')
    
    # Apply search filter if search term exists
    if search_term:
        filtered_active_loans = active_loans[
            (active_loans['name_book'] + ' - ' + active_loans['author']).str.contains(search_term, case=False) |
            (active_loans['name_loaner'] + ' ' + active_loans['surname']).str.contains(search_term, case=False)
        ]
    else:
        filtered_active_loans = active_loans.copy()

    # Configure columns for loans table
    loans_columns = {
        'loan_date': st.column_config.TextColumn('📅 תאריך השאלה', width=150),
        'name_book': st.column_config.TextColumn('📖 שם הספר', width='medium'),
        'author': st.column_config.TextColumn('✍️ מחבר', width=150),
        'name_loaner': st.column_config.TextColumn('👤 שם פרטי', width=150),
        'surname': st.column_config.TextColumn('👥 שם משפחה', width=150),
        'loan_duration': st.column_config.NumberColumn('⏳ משך השאלה - ימים', width='medium')
    }
    
    if not filtered_active_loans.empty:
        # Display loans with reversed columns
        st.dataframe(
            filtered_active_loans[['loan_duration','name_loaner', 'surname', 'name_book', 'author', 'loan_date']][::-1],
            column_config=loans_columns,
            hide_index=True,
            use_container_width=False,
        )
    else:
        st.info("אין השאלות פעילות.")

def render_late_loans(books_df, loaners_df, loans_df):
    """Render the late loans section"""
    st.subheader("⚠️ השאלות באיחור")
    
    # Get active loans and calculate duration
    active_loans = loans_df[loans_df['return_date'].isna()]
    active_loans = active_loans.merge(books_df, left_on='book_id', right_on='id', how='left')
    active_loans = active_loans.merge(loaners_df, left_on='loaner_id', right_on='id', how='left', suffixes=('_book', '_loaner'))
    loan_duration = (datetime.today() - pd.to_datetime(active_loans['loan_date'],format='%d/%m/%Y')).dt.days
    active_loans = pd.concat([active_loans, loan_duration.rename('loan_duration')], axis=1)
    
    # Filter late loans (more than 30 days)
    late_loans = active_loans[active_loans['loan_duration'] > 30].copy()
    
    # Configure columns for late loans table
    late_loans_columns = {
        'loan_date': st.column_config.TextColumn('📅 תאריך השאלה', width=150),
        'name_book': st.column_config.TextColumn('📖 שם הספר', width='medium'),
        'author': st.column_config.TextColumn('✍️ מחבר', width=150),
        'name_loaner': st.column_config.TextColumn('👤 שם פרטי', width=150),
        'surname': st.column_config.TextColumn('👥 שם משפחה', width=150),
        'phone': st.column_config.TextColumn('📱 טלפון', width='medium'),
        'loan_duration': st.column_config.NumberColumn('⏳ משך השאלה - ימים', width='medium')
    }
    
    if not late_loans.empty:
        # Display late loans with reversed columns
        st.dataframe(
            late_loans[['loan_duration', 'phone', 'name_loaner', 'surname', 'name_book', 'author', 'loan_date']][::-1],
            column_config=late_loans_columns,
            hide_index=True,
            use_container_width=False,
        )
    else:
        st.info("אין השאלות באיחור.")

