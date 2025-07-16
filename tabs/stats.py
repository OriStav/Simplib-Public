import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

def render_statistics_tab(books_df, loaners_df, loans_df):
    """Render the statistics tab content"""
    st.title("📊 סטטיסטיקות")
    stats_df, top_loaners = render_stats_calculations(books_df, loaners_df, loans_df)
    render_stats_metrics(stats_df, top_loaners)    
    render_leaderboard(stats_df, top_loaners)    
    # Calculate metrics
    
    # Display charts
    col1, col2 = st.columns(2)
    with col1:
        render_loans_over_time_chart(loans_df)
    with col2:
        render_books_by_category_chart(books_df)
    return stats_df
    

def render_loans_over_time_chart(loans_df):
    """Render the loans over time chart"""
    st.subheader("📈 השאלות לאורך זמן")
    
    # Convert loan_date to datetime
    loans_df['loan_date'] = pd.to_datetime(loans_df['loan_date'], format='%d/%m/%Y')
    loans_df.query('loan_date > "1900-01-01"', inplace=True)
    # Group by month and count loans
    monthly_loans = loans_df.groupby(loans_df['loan_date'].dt.to_period('M')).size().reset_index()
    monthly_loans.columns = ['month', 'count']
    monthly_loans = monthly_loans.query('count > 25') #TODO: remove this
    monthly_loans['month'] = monthly_loans['month'].astype(str)
    
    # Create line chart
    fig = px.line(monthly_loans, x='month', y='count', 
                #   title='מספר השאלות לפי חודש',
                  labels={'month': 'חודש', 'count': 'מספר השאלות'})
    fig.update_layout(
        xaxis_title='חודש', 
        yaxis_title='מספר השאלות',
        # title_x=0.5,
        font=dict(size=16, family="Arial, sans-serif"),
        xaxis=dict(title_font=dict(size=20), tickfont=dict(size=16, family="Arial, sans-serif")),
        yaxis=dict(title_font=dict(size=20), tickfont=dict(size=16, family="Arial, sans-serif"))
    )
    fig.update_layout(margin=dict(l=150, r=150))  # Add padding to left and right sides

    st.plotly_chart(fig, use_container_width=True)

def render_books_by_category_chart(books_df):
    """Render the books by category chart"""
    st.subheader("📚 ספרים לפי קטגוריה")
    count_df = books_df.query('active == True and category != "לא ידוע"')
    # Count books by category
    category_counts = count_df.groupby('category').size().reset_index()
    category_counts.columns = ['category', 'count']
    category_counts = category_counts.query('count > 10') #TODO: remove this
    category_counts['percent'] = category_counts['count'] / category_counts['count'].sum() * 100
    
    # Create pie chart
    fig = px.pie(category_counts, values='percent', names='category')
    fig.update_layout( 
        # title_x=0.5,
        font=dict(size=16, family="Arial, sans-serif"),
        legend=dict(font=dict(size=16, family="Arial, sans-serif"))
    )
    fig.update_layout(margin=dict(l=150, r=150))  # Add padding to left and right sides
    fig.update_traces(textinfo='value', texttemplate='%{value:.0f}%')  # Show whole numbers without decimals

    st.plotly_chart(fig, use_container_width=True)

def render_top_loaners_chart(loaner_counts):
    """Render the top loaners chart"""
    
    # Sort and get top 10
    top_loaners = loaner_counts.sort_values('מספר השאלות', ascending=False).head(10)
    
    # Create bar chart
    fig = px.bar(top_loaners, x='מספר השאלות', y='שם מלא',
                #  title='📖 השואלים המובילים 🏆'
                )

    fig.update_layout(
        yaxis_title='שם השואל',
        xaxis_title='מספר השאלות',
        # title_x=0.5, # Center the title
        font=dict(size=16, family="Arial, sans-serif"), # Set all labels to size 18 with Hebrew-friendly font
        xaxis=dict(
            title_font=dict(size=20),
            tickfont=dict(size=16, family="Arial, sans-serif")
        ),
        yaxis=dict(
            title_font=dict(size=20),
            tickfont=dict(size=16, family="Arial, sans-serif")
        )
    )
    fig.update_layout(margin=dict(l=150, r=150))  # Add padding to left and right sides
    fig.update_layout(yaxis=dict(autorange="reversed"))  # Make highest value appear at top

    st.plotly_chart(fig, use_container_width=True)

def render_top_books_chart(book_counts):
    """Render the top books chart"""
    # Sort and get top 10
    top_books = book_counts.sort_values('מספר השאלות', ascending=False).head(10)
    top_books.rename(columns={'name_book': 'שם הספר'}, inplace=True)
    # Create bar chart
    fig = px.bar(top_books, x='מספר השאלות', y='שם הספר',
                #  title='📚 הספרים הפופולריים 🏆',
                )

    fig.update_layout(
        yaxis_title='שם הספר',
        xaxis_title='מספר השאלות',
        # title_x=0.5, # Center the title
        font=dict(size=16, family="Arial, sans-serif"), # Set all labels to size 18 with Hebrew-friendly font
        xaxis=dict(
            title_font=dict(size=20),
            tickfont=dict(size=16, family="Arial, sans-serif"),
            tickmode='linear',
            dtick=1  # Force ticks to be whole numbers
        ),
        yaxis=dict(
            title_font=dict(size=20),
            tickfont=dict(size=16, family="Arial, sans-serif")
        )
    )
    fig.update_layout(margin=dict(l=150, r=150))  # Add padding to left and right sides
    fig.update_layout(yaxis=dict(autorange="reversed"))  # Make highest value appear at top

    st.plotly_chart(fig, use_container_width=True)

def render_stats_calculations(books_df, loaners_df, loans_df):
    """Render the stats metrics"""
    # Merge all data for statistics
    stats_df = loans_df.merge(books_df, left_on='book_id', right_on='id', how='left', suffixes=('_loan', '_book'))
    stats_df = stats_df.merge(loaners_df, left_on='loaner_id', right_on='id', how='left', suffixes=('_book', '_loaner'))
    
    # Handle deleted loaners
    stats_df['name_loaner'] = stats_df['name_loaner'].fillna('משאיל לא פעיל')
    stats_df['surname'] = stats_df['surname'].fillna('')
    
    # stats_df.dropna(subset=['return_date'],inplace=True)
    stats_df['loan_duration'] = (pd.to_datetime(stats_df['return_date'],format='%d/%m/%Y') - pd.to_datetime(stats_df['loan_date'],format='%d/%m/%Y')).dt.days
    # Count loans per loaner
    top_loaners = stats_df.groupby(['name_loaner', 'surname']).size().reset_index(name='מספר השאלות')

    return stats_df, top_loaners


def render_stats_metrics(stats_df, top_loaners):
    """Render the stats table"""
    # Calculate metrics from stats_df
    total_loans = len(stats_df)
    avg_loan_duration = stats_df['loan_duration'].mean(skipna=True)
    avg_loan_duration = avg_loan_duration if not pd.isna(avg_loan_duration) else 0
    avg_loans_per_loaner = top_loaners['מספר השאלות'].mean()#stats_df['loaner_id'].nunique() / stats_df['loaner_id'].count()
    # max_loan_duration = stats_df['loan_duration'].max()
    # total_unique_loaners = len(stats_df['loaner_id'].unique())
    # total_unique_books = len(stats_df['book_id'].unique())
    
    # Display metrics in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📚 סה״כ השאלות", f"{total_loans:,}")
    with col2:
        st.metric("⏳ ממוצע ימי השאלה", f"{avg_loan_duration:.1f}")
    with col3:
        st.metric("👥 ממוצע השאלות למשאיל", f"{avg_loans_per_loaner:.1f}")
    
    st.markdown("---")

def render_leaderboard(stats_df, top_loaners):
    # Reorder columns to show return date before loan date
    stats_df = stats_df[['name_loaner', 'surname', 'name_book', 'author', 'loan_date', 'return_date', 'loan_duration']]
    
    # Create two columns for side-by-side display
    
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 משאילים מובילים")
        top_loaners = top_loaners.sort_values('מספר השאלות', ascending=False)
        top_loaners['שם מלא'] = top_loaners['name_loaner'] + ' ' + top_loaners['surname']
        render_top_loaners_chart(top_loaners)
        
        # Configure columns for top loaners
        loaners_stats_columns = {
            'שם מלא': st.column_config.TextColumn('👤 שם', width='medium'),
            'מספר השאלות': st.column_config.NumberColumn('📚 מספר השאלות', width='medium')
        }
        
        st.dataframe(
            top_loaners[['מספר השאלות','שם מלא']],
            column_config=loaners_stats_columns,
            hide_index=True,
            use_container_width=False,
            height=210
        )
    
    with col2:
        st.subheader("📚 ספרים פופולריים")
        # Count loans per book
        top_books = stats_df.groupby(['name_book', 'author']).size().reset_index(name='מספר השאלות')
        top_books = top_books.sort_values('מספר השאלות', ascending=False)
        render_top_books_chart(top_books)
        
        # Configure columns for top books
        books_stats_columns = {
            'name_book': st.column_config.TextColumn('📖 שם הספר', width='medium'),
            'author': st.column_config.TextColumn('✍️ מחבר', width='medium'),
            'מספר השאלות': st.column_config.NumberColumn('📚 מספר השאלות', width='medium')
        }
        
        st.dataframe(
            top_books[top_books.columns[::-1]],
            column_config=books_stats_columns,
            hide_index=True,
            use_container_width=False,
            height=210
        )
