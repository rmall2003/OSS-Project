import streamlit as st
from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from streamlit_option_menu import option_menu

# Database setup
def init_db():
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                    (id INTEGER PRIMARY KEY, username TEXT, password TEXT, budget REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses 
                    (user_id INTEGER, category TEXT, description TEXT, amount REAL, date TEXT)''')
    conn.commit()
    conn.close()

# User authentication
def register_user(username, password, budget):
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, budget) VALUES (?, ?, ?)", (username, password, budget,))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, budget FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# Adding expenses to the database
def add_expense(user_id, category, description, amount, date):
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (user_id, category, description, amount, date) VALUES (?, ?, ?, ?, ?)",
                   (user_id, category, description, amount, date))
    conn.commit()
    conn.close()

# Fetching expenses for a user
def get_expenses(user_id, month, year):
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT category, description, amount, date FROM expenses WHERE user_id=? AND strftime('%m', date)=? AND strftime('%Y', date)=?", 
                   (user_id, f"{month:02d}", str(year)))
    data = cursor.fetchall()
    conn.close()
    return data

# Initialize the database
init_db()

# Streamlit UI
st.set_page_config(page_title="Expense Tracker", page_icon="💰")
st.title("Personal Expense Tracker")

# Authentication (Login/Register)
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    option = st.radio("Login or Register", ["Login", "Register"])

    if option == "Register":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        budget = st.number_input("Monthly Budget", min_value=100)
        if st.button("Register"):
            register_user(username, password,budget)
            st.success("User registered successfully!")
    else:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.user = user
                st.success("Login successful!")
            else:
                st.error("Invalid credentials.")
else:
    user_id, username, budget = st.session_state.user
    # Main Menu with Profile and Logout
    selected = option_menu(
        menu_title=None,
        options=["Add Expense", "Check Expense (Month-wise)", "Remaining Budget", "Profile"],
        icons=["pencil-fill", "bar-chart-fill", "cash", "person-circle"],
        orientation="vertical",
    )

    # Add Expense Page
    if selected == "Add Expense":
        st.header("Add New Expense")
        category = st.selectbox("Category", ["Housing", "Food", "Transportation", "Entertainment", "Medical", "Breverages",
                                             "Utilities", "Clothing", "Household Items", "Gifts", "Miscellaneous"])
        description = st.text_input("Description (optional)").title()
        amount = st.number_input("Amount", min_value=100)
        date = st.date_input("Date", value=datetime.today())
        
        if st.button("Add Expense"):
            add_expense(user_id, category, description, amount, date)
            st.success("Expense added successfully!")

    # Check Expenses (Month-wise)
    elif selected == "Check Expense (Month-wise)":
        st.header("Monthly Expense Overview")
        month = st.selectbox("Month", range(1, 13), format_func=lambda x: datetime(1900, x, 1).strftime('%B'))
        year = st.selectbox("Year", range(2024, datetime.today().year + 1))
        
        expenses = get_expenses(user_id, month, year)
        if expenses:
            df = pd.DataFrame(expenses, columns=["Category", "Description", "Amount", "Date"])
            st.write(df)

            # Plotting expenses
            fig, ax = plt.subplots()
            df.groupby("Category").sum()["Amount"].plot(kind="bar", ax=ax)
            st.pyplot(fig)
        else:
            st.info("No expenses recorded for this month.")

    # Remaining Budget
    elif selected == "Remaining Budget":
        st.header("Remaining Budget")
        total_expenses = sum([exp[2] for exp in get_expenses(user_id, datetime.today().month, datetime.today().year)])
        remaining_budget = budget - total_expenses
        
        col1, col2 = st.columns(2)
        col1.metric("Total Expenses", f"${total_expenses}")
        col2.metric("Remaining Budget", f"${remaining_budget}")

    # User Profile Page
    # User Profile Page
    elif selected == "Profile":
        st.header("User Profile")
        st.text(f"Username: {username}")
        st.text(f"Monthly Budget: ${budget}")

        if st.button("Logout"):
            st.session_state.user = None
            st.success("You have been logged out!")
            st.experimental_rerun()

