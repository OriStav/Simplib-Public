import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
import shutil
from pathlib import Path
import threading
from paths import book_names_path, book_loaners_path, loans_log_path

def setup_page():
    """Set up the Streamlit page configuration and styling"""
    st.set_page_config(
        page_title="ספרייה פשוטה",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    st.markdown("<h1 style='text-align: center;'>📚 ספרייה קהילתית 🌳</h1>", unsafe_allow_html=True)
    st.markdown(
        """
        <style>
        .stApp {
            direction: rtl;
        }
        /* Make the tab labels spread equally along the width */
        .stTabs [data-baseweb="tab-list"] {
            display: flex !important;
            justify-content: stretch !important;
            width: 100% !important;
            gap: 0 !important;
        }
        .stTabs [data-baseweb="tab"] {
            flex: 1 1 0 !important;
            text-align: center !important;
            padding-left: 2.5rem !important;
            padding-right: 2.5rem !important;
            min-width: 0 !important;
            font-size: 1.2rem !important;
            max-width: 100% !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_data():
    """Load data from CSV files"""
    books_df = pd.read_csv(book_names_path, dtype={'active': bool,'id': int,'name': str,'author': str,'category': str})
    books_df.fillna("", inplace=True)
    loaners_df = pd.read_csv(book_loaners_path, dtype={'phone': str,'active': bool,'id': int,'name': str,'surname': str})
    loaners_df.fillna("", inplace=True)
    # Add active column if it doesn't exist
    if 'active' not in loaners_df.columns:
        loaners_df['active'] = True
    loans_df = pd.read_csv(loans_log_path)
    return books_df, loaners_df, loans_df

def save_loans(df):
    """Save loans data to CSV"""
    df.to_csv(loans_log_path, index=False)

def save_books(df):
    """Save books data to CSV"""
    df[['id', 'name', 'author', 'category', 'active']].to_csv(book_names_path, index=False)

def save_loaners(df):
    """Save loaners data to CSV"""
    df[['id', 'name', 'surname', 'phone', 'active']].to_csv(book_loaners_path, index=False)

def calculate_metrics(books_df, loaners_df, loans_df):
    """Calculate metrics for the dashboard"""
    total_loaners = len(loaners_df)
    
    # Create a proper copy of active loans and calculate duration
    active_loans = loans_df[loans_df['return_date'].isna()].copy()
    active_loans.loc[:, 'loan_duration'] = (datetime.today() - pd.to_datetime(active_loans['loan_date'], format='%d/%m/%Y')).dt.days
    
    # Create a proper copy of late loans
    late_loans = active_loans[active_loans['loan_duration'] > 30].copy()
    
    active_loaners_count = len(active_loans['loaner_id'].unique())
    late_loaners_count = len(late_loans['loaner_id'].unique())
    late_loans_count = len(late_loans)
    
    total_books = len(books_df)
    borrowed_books = len(active_loans['book_id'].unique())
    late_books = len(late_loans['book_id'].unique())
    available_books = total_books - borrowed_books
    
    return {
        'total_loaners': total_loaners,
        'active_loaners': active_loaners_count,
        'late_loaners': late_loaners_count,
        'active_loans': len(active_loans),
        'late_loans': late_loans_count,
        'total_books': total_books,
        'borrowed_books': borrowed_books,
        'late_books': late_books,
        'available_books': available_books
    }
