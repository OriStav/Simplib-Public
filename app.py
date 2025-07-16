"""
streamlit run app.py

TODO:
- backup backslash
"""

import streamlit as st
from methods.utils import setup_page
from methods.backuper import init_backup
from methods.utils import load_data
from tabs.loans import render_loans_tab
from tabs.loaners import render_loaners_tab
from tabs.books import render_books_tab
from tabs.stats import render_statistics_tab
from tabs.history import render_history_table

def main():
    """Main function to run the Streamlit app"""
    # init_backup()

    # Setup page
    setup_page()
    
    # Load data
    books_df, loaners_df, loans_df = load_data()
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📖 השאלות", "📚 ספרים", "👥 שואלים", "📊 סטטיסטיקות", "📜 היסטוריית השאלות"])
    
    # Render each tab
    with tab1:
        render_loans_tab(books_df, loaners_df, loans_df)
    
    with tab2:
        render_books_tab(books_df, loaners_df, loans_df)
    
    with tab3:
        render_loaners_tab(loaners_df, loans_df)
    
    with tab4:
        stats_df = render_statistics_tab(books_df, loaners_df, loans_df)

    with tab5:
        render_history_table(stats_df)

if __name__ == "__main__":
    main()