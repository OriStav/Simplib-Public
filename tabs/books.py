import streamlit as st
import pandas as pd
from datetime import datetime
from methods.utils import calculate_metrics, save_books
import io

def render_books_tab(books_df, loaners_df, loans_df):
    """Render the books tab content"""
    metrics = calculate_metrics(books_df, loaners_df, loans_df)
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    with col1:
        st.title("📚 ספרים")
    with col2:
        st.metric("📚 סה״כ ספרים", metrics['total_books'])
    with col3:
        st.metric("✅ ספרים זמינים", metrics['available_books'])
    with col4:
        st.metric("📖 ספרים מושאלים", metrics['borrowed_books'])
    with col5:
        st.metric("⚠️ ספרים באיחור", metrics['late_books'])
    
    render_books_search_and_table(books_df, loaners_df, loans_df)
    
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        render_add_book_form(books_df)
    with col2:
        render_remove_book_form(books_df, loans_df)

def render_books_search_and_table(books_df, loaners_df, loans_df):
    """Render the books search and table section"""
    # Search and filter
    col1, col2, col3 = st.columns([1, 1, 1])
    books_df = books_df.copy()
    books_df  = books_df.query('active == True')#.drop(columns=['active'])
    with col1:
        search_term = st.selectbox("חיפוש ספרים לפי שם או מחבר", 
                                 options=[''] + sorted(books_df['name'].unique().tolist() + books_df['author'].unique().tolist()),
                                 placeholder='בחר/י ספר או מחבר')
    
    # Calculate book status
    active_loans = loans_df[loans_df['return_date'].isna()].copy()
    active_loans.loc[:, 'loan_duration'] = (datetime.today() - pd.to_datetime(active_loans['loan_date'], format='%d/%m/%Y')).dt.days
    active_loans = active_loans.merge(loaners_df[['id', 'name', 'surname']], left_on='loaner_id', right_on='id', how='left')

    # Create status mapping
    book_status = {}
    for _, loan in active_loans.iterrows():
        if loan['loan_duration'] > 30:
            book_status[loan['book_id']] = f"באיחור - {loan['name']} {loan['surname']} - {loan['loan_duration']} ימים⚠️"
        else:
            book_status[loan['book_id']] = f"מושאל - {loan['name']} {loan['surname']} - {loan['loan_duration']} ימים📚"

    # Add status to books_df
    books_df.loc[:, 'status'] = books_df['id'].apply(lambda x: book_status.get(x, '✅ זמין'))
    # Filter books based on search and category
    filtered_books = books_df#.query('active == True').drop(columns=['active'])
    if search_term:
        filtered_books = filtered_books[
            filtered_books['name'].str.contains(search_term, case=False) |
            filtered_books['author'].str.contains(search_term, case=False)
        ]
    
    # Configure columns for books table
    books_columns = {
        'category': st.column_config.TextColumn('🏷️ קטגוריה', width='medium'),
        'status': st.column_config.TextColumn('📊 זמינות', width='medium'),
        'author': st.column_config.TextColumn('✍️ מחבר', width='medium'),
        'name': st.column_config.TextColumn('📖 שם הספר', width='large'),
        # 'id': st.column_config.NumberColumn('🔢 מזהה', width='small'),
        'active': st.column_config.CheckboxColumn('🟢 פעיל', width='small'),
    }
    edit_mode = True
    # Display books with reversed columns
    if edit_mode:
        st.markdown("*💡 נא ללחוץ ENTER לשמירת השינויים*")
        edited_books = st.data_editor(
            filtered_books[list(books_columns.keys())],
            column_config=books_columns,
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            key="books_editor"
        )
        if st.button("שמור שינויים"):
            books_df.loc[filtered_books.index,list(books_columns.keys())] = edited_books
            save_books(books_df)
            st.success("שינויים נשמרו בהצלחה!")
            st.rerun()
    else:
        st.dataframe(
            filtered_books[filtered_books.columns[::-1]],
            column_config=books_columns,
            hide_index=True,
            use_container_width=True,
        )
    # Add header row every 44 rows
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_books[["name","author"]].to_excel(writer, sheet_name='Books', index=False)
    
    # Get the Excel file data
    excel_data = output.getvalue()

    st.download_button(
        label="הורד ספרים",
        data=excel_data,
        file_name="books.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

def render_add_book_form(books_df):
    """Render the add book form"""
    st.subheader("➕ הוספת ספר חדש")
    with st.form("new_book_form"):
        new_book_name = st.text_input("📖 שם הספר")
        new_book_category = st.text_input("🏷️ קטגוריה")
        new_book_author = st.text_input("✍️ מחבר")
    
        submitted = st.form_submit_button("הוסף ספר")
        
        if submitted:
            if new_book_name and new_book_author:
                # Check for duplicates
                bool_book = (books_df['author'].str.lower() == new_book_author.lower()) & (books_df['name'].str.lower() == new_book_name.lower())
                is_duplicate = books_df[bool_book].shape[0] > 0
                
                if is_duplicate:
                    if books_df[bool_book]["active"].iloc[0] == False:
                        books_df.loc[bool_book, "active"] = True
                        st.success("ספר זה הוסף מחדש")
                        save_books(books_df)
                        st.rerun()
                    else:
                        st.error("ספר זה כבר קיים במערכת")
                else:
                    # Generate new ID
                    new_id = books_df['id'].max() + 1 if not books_df.empty else 1
                    
                    # Create new book entry
                    new_book = pd.DataFrame({
                        'id': [new_id],
                        'name': [new_book_name],
                        'author': [new_book_author],
                        'category': [new_book_category],
                        'active': [True]
                    })
                    
                    # Add to database
                    books_df = pd.concat([books_df, new_book], ignore_index=True)
                    save_books(books_df)
                    st.success("הספר נוסף בהצלחה!")
                    st.rerun()
            else:
                st.error("יש למלא שם הספר ומחבר")

def render_remove_book_form(books_df, loans_df):
    """Render the remove book form"""
    st.subheader("🗑️ הסרת ספר")
    with st.container(border=True):
        book_to_remove = st.selectbox("בחר ספר להסרה", 
                                    options=[''] + sorted(books_df[books_df['active']]['name'] + ' - ' + books_df[books_df['active']]['author']),
                                    key='book_remove',
                                    placeholder='בחר/י ספר להסרה')
        if st.button("הסר ספר", key='remove_book_btn'):
            if book_to_remove:
                # Find the book to remove
                book_name, author = book_to_remove.split(' - ')
                book_id = books_df[(books_df['name'] == book_name) & (books_df['author'] == author)]['id'].iloc[0]
                
                # Check if book is currently loaned
                if book_id in loans_df[loans_df['return_date'].isna()]['book_id'].values:
                    st.error("לא ניתן להסיר ספר שנמצא בהשאלה!")
                else:
                    # Set book as inactive instead of deleting
                    books_df.loc[books_df['id'] == book_id, 'active'] = False
                    save_books(books_df)
                    st.success("הספר הוסר בהצלחה!")
                    st.rerun()
            else:
                st.error("יש לבחור ספר להסרה")