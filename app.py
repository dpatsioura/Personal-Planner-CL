import streamlit as st
import pandas as pd
import sqlite3
import os
from io import BytesIO

st.set_page_config(page_title="Command Center", layout="wide")

if not os.path.exists("uploads"):
    os.makedirs("uploads")

conn = sqlite3.connect('command_center.db', check_same_thread=False)

def save_uploaded_file(uploadedfile):
    if uploadedfile is not None:
        with open(os.path.join("uploads", uploadedfile.name), "wb") as f:
            f.write(uploadedfile.getbuffer())
        return uploadedfile.name
    return ""

try:
    projects_df = pd.read_sql_query('SELECT * FROM projects', conn)
except:
    projects_df = pd.DataFrame(columns=['Ονομασία', 'Προθεσμία', 'Αρχείο'])
    projects_df.to_sql('projects', conn, index=False)

try:
    expenses_df = pd.read_sql_query('SELECT * FROM expenses', conn)
except:
    expenses_df = pd.DataFrame(columns=['Περιγραφή', 'Ποσό', 'Αρχείο'])
    expenses_df.to_sql('expenses', conn, index=False)

st.title("Academic Command Center")
st.subheader("Οργάνωση, Projects και Ταξίδια")

col1, col2 = st.columns(2)

with col1:
    st.header("Ενεργά Projects & Deadlines")
    
    new_project = st.text_input("Τίτλος Project")
    new_deadline = st.date_input("Προθεσμία")
    proj_file = st.file_uploader("Συνημμένο Project", type=["pdf", "docx", "png", "jpg"])
    
    if st.button("Προσθήκη Εργασίας"):
        file_name = save_uploaded_file(proj_file)
        new_row = pd.DataFrame([{'Ονομασία': new_project, 'Προθεσμία': str(new_deadline), 'Αρχείο': file_name}])
        projects_df = pd.concat([projects_df, new_row], ignore_index=True)
        projects_df.to_sql('projects', conn, if_exists='replace', index=False)
        st.success("Το project αποθηκεύτηκε!")
        st.rerun()

    st.write("Επεξεργασία και Διαγραφή Projects")
    edited_projects = st.data_editor(projects_df, num_rows="dynamic", key="proj_editor")
    if st.button("Αποθήκευση Αλλαγών Projects"):
        edited_projects.to_sql('projects', conn, if_exists='replace', index=False)
        st.success("Οι αλλαγές αποθηκεύτηκαν!")
        st.rerun()

with col2:
    st.header("Travel & Reimbursement Vault")
    
    expense_name = st.text_input("Περιγραφή Εξόδου")
    expense_amount = st.number_input("Ποσό σε Ευρώ", min_value=0.0, format="%.2f")
    exp_file = st.file_uploader("Απόδειξη ή Εισιτήριο", type=["pdf", "png", "jpg", "jpeg"])
    
    if st.button("Προσθήκη Εξόδου"):
        file_name = save_uploaded_file(exp_file)
        new_row = pd.DataFrame([{'Περιγραφή': expense_name, 'Ποσό': expense_amount, 'Αρχείο': file_name}])
        expenses_df = pd.concat([expenses_df, new_row], ignore_index=True)
        expenses_df.to_sql('expenses', conn, if_exists='replace', index=False)
        st.success("Το έξοδο αποθηκεύτηκε!")
        st.rerun()

    st.write("Επεξεργασία και Διαγραφή Εξόδων")
    edited_expenses = st.data_editor(expenses_df, num_rows="dynamic", key="exp_editor")
    if st.button("Αποθήκευση Αλλαγών Εξόδων"):
        edited_expenses.to_sql('expenses', conn, if_exists='replace', index=False)
        st.success("Οι αλλαγές αποθηκεύτηκαν!")
        st.rerun()
        
    if not edited_expenses.empty:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_expenses.to_excel(writer, index=False, sheet_name='Έξοδα')
        
        st.download_button(
            label="Κατέβασμα λίστας εξόδων σε Excel",
            data=output.getvalue(),
            file_name="exoda_taxidiou.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
