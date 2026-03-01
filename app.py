import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
from datetime import date, datetime

st.set_page_config(page_title="Command Center", layout="wide")

# Δημιουργία και σύνδεση με την τοπική βάση δεδομένων
conn = sqlite3.connect('command_center.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, description TEXT, amount REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, deadline DATE)''')
conn.commit()

st.title("Academic Command Center")
st.subheader("Οργάνωση, Projects και Ταξίδια")

col1, col2 = st.columns(2)

with col1:
    st.header("Ενεργά Projects & Deadlines")
    
    # Διάβασμα των projects από τη βάση και υπολογισμός ημερών
    projects_df = pd.read_sql_query('SELECT name, deadline FROM projects', conn)
    today = date.today()
    
    for index, row in projects_df.iterrows():
        deadline_date = datetime.strptime(row['deadline'], '%Y-%m-%d').date()
        days_left = (deadline_date - today).days
        
        if days_left < 0:
            st.error(f"{row['name']} (Έληξε στις {row['deadline']})")
        elif days_left <= 7:
            st.error(f"{row['name']} (Λήγει σε {days_left} μέρες! - ΕΠΕΙΓΟΝ)")
        elif days_left <= 30:
            st.warning(f"{row['name']} (Λήγει σε {days_left} μέρες)")
        else:
            st.info(f"{row['name']} (Λήγει στις {row['deadline']})")
            
    st.write("Προσθήκη Νέας Εργασίας")
    new_project = st.text_input("Τίτλος Project")
    new_deadline = st.date_input("Προθεσμία")
    
    if st.button("Αποθήκευση Εργασίας"):
        c.execute('INSERT INTO projects (name, deadline) VALUES (?, ?)', (new_project, new_deadline.strftime('%Y-%m-%d')))
        conn.commit()
        st.success("Η εργασία αποθηκεύτηκε!")
        st.rerun()

with col2:
    st.header("Travel & Reimbursement Vault")
    st.write("Καταχώρηση εξόδων")
    
    expense_name = st.text_input("Περιγραφή Εξόδου (π.χ. Ταξί αεροδρόμιο)")
    expense_amount = st.number_input("Ποσό σε Ευρώ", min_value=0.0, format="%.2f")
    
    if st.button("Προσθήκη Εξόδου"):
        c.execute('INSERT INTO expenses (description, amount) VALUES (?, ?)', (expense_name, expense_amount))
        conn.commit()
        st.success("Το έξοδο αποθηκεύτηκε μόνιμα!")
        st.rerun()
        
    expenses_df = pd.read_sql_query('SELECT description as "Περιγραφή", amount as "Ποσό" FROM expenses', conn)
    
    if not expenses_df.empty:
        st.dataframe(expenses_df)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            expenses_df.to_excel(writer, index=False, sheet_name='Έξοδα')
        processed_data = output.getvalue()
        
        st.download_button(
            label="Κατέβασμα λίστας εξόδων σε Excel",
            data=processed_data,
            file_name="exoda_taxidiou.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
