import streamlit as st
import pandas as pd
from datetime import datetime
from methods.utils import calculate_metrics, save_loaners
import time

def render_loaners_tab(loaners_df, loans_df):
    """Render the loaners tab content"""
    metrics = calculate_metrics(pd.DataFrame(), loaners_df, loans_df)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("👥 שואלים")
    with col2:
        st.metric("👥 סה״כ שואלים", metrics['total_loaners'])
    with col3:
        st.metric("⚠️ שואלים באיחור", metrics['late_loaners'])
    
    render_loaners_search_and_table(loaners_df, loans_df)
    
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        render_add_loaner_form(loaners_df)
    with col2:
        render_remove_loaner_form(loaners_df, loans_df)

def render_loaners_search_and_table(loaners_df, loans_df):
    """Render the loaners search and table section"""
    # Search and filter
    col1, col2, col3 = st.columns([1, 1, 1])
    # loaners_df  = loaners_df.query('active == True')#.drop(columns=['active'])
    loaners_df.fillna("", inplace=True)
    with col1:
        search_term = st.selectbox("חיפוש שואלים לפי שם או שם משפחה", 
                                 options=[''] + sorted(loaners_df['name'].unique().tolist() + loaners_df['surname'].unique().tolist()),
                                 placeholder='בחר/י שואל/ת')
    
    # Calculate loaner status
    active_loans = loans_df[loans_df['return_date'].isna()].copy()
    active_loans.loc[:, 'loan_duration'] = (datetime.today() - pd.to_datetime(active_loans['loan_date'], format='%d/%m/%Y')).dt.days
    
    # Create status mapping
    loaner_status = {}
    for _, loan in active_loans.iterrows():
        if loan['loan_duration'] > 30:
            loaner_status[loan['loaner_id']] = f"באיחור - {loan['loan_duration']} ימים⚠️"
        else:
            loaner_status[loan['loaner_id']] = f"השאלה פעילה - {loan['loan_duration']} ימים📚"
    
    # Add status to loaners_df
    loaners_df.loc[:, 'status'] = loaners_df['id'].apply(lambda x: loaner_status.get(x, '✅ אין השאלות פעילות'))
    
    # Filter loaners based on search
    filtered_loaners = loaners_df#.query('active == True').drop(columns=['active'])
    if search_term:
        filtered_loaners = filtered_loaners[
            filtered_loaners['name'].str.contains(search_term, case=False) |
            filtered_loaners['surname'].str.contains(search_term, case=False)
        ]
    
    # Configure columns for loaners table
    loaners_columns = {
        'phone': st.column_config.TextColumn('📱 טלפון', width='medium'),
        'status': st.column_config.TextColumn('📊 סטטוס', width='large'),
        'surname': st.column_config.TextColumn('👥 שם משפחה', width='medium'),
        'name': st.column_config.TextColumn('👤 שם', width='medium'),
        'active': st.column_config.CheckboxColumn('🟢 פעיל', width='small'),
    }
    edit_mode = True
    # Display books with reversed columns
    if edit_mode:
        st.markdown("*💡 נא ללחוץ ENTER לשמירת השינויים*")
        edited_loaners = st.data_editor(
            filtered_loaners[list(loaners_columns.keys())],
            column_config=loaners_columns,
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            key="loaners_editor"
        )
        if st.button("שמור שינויים",key="save_loaners_btn"):
            loaners_df.loc[filtered_loaners.index,list(loaners_columns.keys())] = edited_loaners
            save_loaners(loaners_df)
            st.success("שינויים נשמרו בהצלחה!")
            time.sleep(0.5)
            st.rerun()
    else:
        st.dataframe(
            filtered_loaners[filtered_loaners.columns[::-1]],
            column_config=loaners_columns,
            hide_index=True,
            use_container_width=True,
        )


def render_add_loaner_form(loaners_df):
    """Render the add loaner form"""
    st.subheader("➕ הוספת שואל חדש")
    with st.form("new_loaner_form"):
        new_loaner_name = st.text_input("👤 שם פרטי")
        new_loaner_surname = st.text_input("👥 שם משפחה")
        new_loaner_phone = st.text_input("📱 טלפון")
    
        submitted = st.form_submit_button("הוסף שואל")
        
        if submitted:
            if new_loaner_name and new_loaner_surname:
                # Check for duplicates
                bool_loaner = (loaners_df['name'].str.lower() == new_loaner_name.lower()) & (loaners_df['surname'].str.lower() == new_loaner_surname.lower())
                is_duplicate = loaners_df[bool_loaner].shape[0] > 0
                
                if is_duplicate:
                    if loaners_df[bool_loaner]["active"].iloc[0] == False:
                        loaners_df.loc[bool_loaner, "active"] = True
                        st.success("שואל זה הוסף מחדש")
                        time.sleep(0.5)
                        save_loaners(loaners_df)
                        st.rerun()
                    else:
                        st.error("שואל זה כבר קיים במערכת")
                else:
                    # Generate new ID
                    new_id = loaners_df['id'].max() + 1 if not loaners_df.empty else 1
                    
                    # Create new loaner entry
                    new_loaner = pd.DataFrame({
                        'id': [new_id],
                        'name': [new_loaner_name],
                        'surname': [new_loaner_surname],
                        'phone': [new_loaner_phone],
                        'active': [True]
                    })
                    
                    # Add to database
                    loaners_df = pd.concat([loaners_df, new_loaner], ignore_index=True)
                    save_loaners(loaners_df)
                    st.success("השואל נוסף בהצלחה!")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.error("יש למלא שם ושם משפחה")

def render_remove_loaner_form(loaners_df, loans_df):
    """Render the remove loaner form"""
    st.subheader("🗑️ הסרת שואל")
    loaners_df.fillna("", inplace=True)
    with st.container(border=True):
        loaner_to_remove = st.selectbox("בחר שואל להסרה", 
                                      options=[''] + sorted(loaners_df[loaners_df['active']]['name'] + ' ' + loaners_df[loaners_df['active']]['surname']),
                                      key='loaner_remove',
                                      placeholder='בחר/י שואל להסרה')
        if st.button("הסר שואל", key='remove_loaner_btn'):
            if loaner_to_remove:
                # Find the loaner to remove
                name, surname = loaner_to_remove.split(' ')
                loaner_id = loaners_df[(loaners_df['name'] == name) & (loaners_df['surname'] == surname)]['id'].iloc[0]
                
                # Check if loaner has active loans
                if loaner_id in loans_df[loans_df['return_date'].isna()]['loaner_id'].values:
                    st.error("לא ניתן להסיר שואל שיש לו השאלות פעילות!")
                else:
                    # Set loaner as inactive instead of deleting
                    loaners_df.loc[loaners_df['id'] == loaner_id, 'active'] = False
                    save_loaners(loaners_df)
                    st.success("השואל הוסר בהצלחה!")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.error("יש לבחור שואל להסרה")