import streamlit as st
import pandas as pd
import sqlite3
import os
import re
from io import BytesIO

st.set_page_config(page_title="Command Center", layout="wide")

def create_safe_folder_name(name):
    clean_name = re.sub(r'[^a-zA-Z0-9\u0370-\u03FF -]', '_', name.strip())
    return clean_name.replace(' ', '_')

def save_uploaded_file(uploadedfile, category, folder_name):
    if uploadedfile is not None and folder_name:
        safe_folder = create_safe_folder_name(folder_name)
        base_path = os.path.join("uploads", category, safe_folder)
        
        if not os.path.exists(base_path):
            os.makedirs(base_path)
            
        file_path = os.path.join(base_path, uploadedfile.name)
        with open(file_path, "wb") as f:
            f.write(uploadedfile.getbuffer())
        return file_path
    return ""

conn = sqlite3.connect('command_center.db', check_same_thread=False)

try:
    projects_df = pd.read_sql_query('SELECT * FROM projects', conn)
except:
    projects_df = pd.DataFrame(columns=['Ονομασία', 'Προθεσμία', 'Διαδρομή_Αρχείου'])
    projects_df.to_sql('projects', conn, index=False)

try:
    expenses_df = pd.read_sql_query('SELECT * FROM expenses', conn)
except:
    expenses_df = pd.DataFrame(columns=['Ταξίδι', 'Περιγραφή', 'Ποσό', 'Διαδρομή_Αρχείου'])
    expenses_df.to_sql('expenses', conn, index=False)

st.title("Academic Command Center")
st.subheader("Οργάνωση, Projects και Ταξίδια")

col1, col2 = st.columns(2)

with col1:
    st.header("Ενεργά Projects")
    
    new_project = st.text_input("Όνομα Project")
    new_deadline = st.date_input("Προθεσμία")
    proj_file = st.file_uploader("Συνημμένο Αρχείο Project", type=["pdf", "docx", "png", "jpg", "xlsx"])
    
    if st.button("Αποθήκευση Project"):
        if new_project:
            file_path = save_uploaded_file(proj_file, "Projects", new_project)
            new_row = pd.DataFrame([{'Ονομασία': new_project, 'Προθεσμία': str(new_deadline), 'Διαδρομή_Αρχείου': file_path}])
            projects_df = pd.concat([projects_df, new_row], ignore_index=True)
            projects_df.to_sql('projects', conn, if_exists='replace', index=False)
            st.success("Το project και ο φάκελος δημιουργήθηκαν!")
            st.rerun()
        else:
            st.error("Βάλε πρώτα ένα όνομα για το Project.")

    st.write("Επεξεργασία Projects")
    edited_projects = st.data_editor(projects_df, num_rows="dynamic", key="proj_editor")
    if st.button("Αποθήκευση Αλλαγών Projects"):
        edited_projects.to_sql('projects', conn, if_exists='replace', index=False)
        st.success("Οι αλλαγές αποθηκεύτηκαν!")
        st.rerun()

with col2:
    st.header("Ταξίδια & Έξοδα")
    
    trip_name = st.text_input("Όνομα Ταξιδιού (π.χ. Συνέδριο Παρίσι)")
    expense_desc = st.text_input("Περιγραφή Εξόδου")
    expense_amount = st.number_input("Ποσό σε Ευρώ", min_value=0.0, format="%.2f")
    exp_file = st.file_uploader("Απόδειξη ή Εισιτήριο", type=["pdf", "png", "jpg", "jpeg"])
    
    if st.button("Καταχώρηση Εξόδου"):
        if trip_name:
            file_path = save_uploaded_file(exp_file, "Trips", trip_name)
            new_row = pd.DataFrame([{'Ταξίδι': trip_name, 'Περιγραφή': expense_desc, 'Ποσό': expense_amount, 'Διαδρομή_Αρχείου': file_path}])
            expenses_df = pd.concat([expenses_df, new_row], ignore_index=True)
            expenses_df.to_sql('expenses', conn, if_exists='replace', index=False)
            st.success("Το έξοδο καταχωρήθηκε στον φάκελο του ταξιδιού!")
            st.rerun()
        else:
            st.error("Γράψε το όνομα του ταξιδιού για να ξέρουμε σε ποιον φάκελο να μπει.")

    st.write("Επεξεργασία Εξόδων")
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
            label="Κατέβασμα λίστας εξόδων (Excel)",
            data=output.getvalue(),
            file_name="exoda_taxidion.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
