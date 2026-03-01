import streamlit as st
import pandas as pd
import sqlite3
import os
import re

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

conn = sqlite3.connect('command_center_v2.db', check_same_thread=False)

conn.execute('''CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, deadline TEXT)''')
conn.execute('''CREATE TABLE IF NOT EXISTS trips (id INTEGER PRIMARY KEY, name TEXT)''')
conn.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, trip_name TEXT, description TEXT, amount REAL, file_path TEXT)''')
conn.commit()

st.title("Academic Command Center")

tab1, tab2 = st.tabs(["Projects", "Ταξίδια & Έξοδα"])

with tab1:
    with st.expander("Δημιουργία Νέου Project"):
        new_project = st.text_input("Όνομα Project")
        new_deadline = st.date_input("Προθεσμία")
        if st.button("Δημιουργία Φακέλου Project"):
            if new_project:
                conn.execute('INSERT INTO projects (name, deadline) VALUES (?, ?)', (new_project, str(new_deadline)))
                conn.commit()
                os.makedirs(os.path.join("uploads", "Projects", create_safe_folder_name(new_project)), exist_ok=True)
                st.success("Το project δημιουργήθηκε!")
                st.rerun()
            else:
                st.error("Γράψε ένα όνομα για το project.")

    projects_df = pd.read_sql_query('SELECT * FROM projects', conn)
    if not projects_df.empty:
        project_names = projects_df['name'].tolist()
        selected_project = st.selectbox("Άνοιγμα Φακέλου Project", ["Επίλεξε..."] + project_names)
        
        if selected_project != "Επίλεξε...":
            st.subheader(f"Μέσα στον φάκελο: {selected_project}")
            
            proj_file = st.file_uploader("Προσθήκη Αρχείου", type=["pdf", "docx", "png", "jpg", "xlsx"])
            if st.button("Ανέβασμα Αρχείου"):
                if proj_file:
                    save_uploaded_file(proj_file, "Projects", selected_project)
                    st.success("Το αρχείο μπήκε στον φάκελο!")
                    st.rerun()
            
            folder_path = os.path.join("uploads", "Projects", create_safe_folder_name(selected_project))
            if os.path.exists(folder_path):
                files = os.listdir(folder_path)
                if files:
                    st.write("Περιεχόμενα Φακέλου:")
                    for f in files:
                        st.write(f"- {f}")
                else:
                    st.write("Ο φάκελος δεν έχει αρχεία ακόμα.")

with tab2:
    with st.expander("Δημιουργία Νέου Ταξιδιού"):
        new_trip = st.text_input("Όνομα Ταξιδιού")
        if st.button("Δημιουργία Φακέλου Ταξιδιού"):
            if new_trip:
                conn.execute('INSERT INTO trips (name) VALUES (?)', (new_trip,))
                conn.commit()
                os.makedirs(os.path.join("uploads", "Trips", create_safe_folder_name(new_trip)), exist_ok=True)
                st.success("Ο φάκελος ταξιδιού δημιουργήθηκε!")
                st.rerun()
            else:
                st.error("Γράψε ένα όνομα για το ταξίδι.")

    trips_df = pd.read_sql_query('SELECT * FROM trips', conn)
    if not trips_df.empty:
        trip_names = trips_df['name'].tolist()
        selected_trip = st.selectbox("Άνοιγμα Φακέλου Ταξιδιού", ["Επίλεξε..."] + trip_names)
        
        if selected_trip != "Επίλεξε...":
            st.subheader(f"Μέσα στον φάκελο: {selected_trip}")
            
            expense_desc = st.text_input("Περιγραφή Εξόδου (π.χ. Ταξί)")
            expense_amount = st.number_input("Ποσό", min_value=0.0, format="%.2f")
            exp_file = st.file_uploader("Απόδειξη", type=["pdf", "png", "jpg"])
            
            if st.button("Προσθήκη Εξόδου"):
                file_path = save_uploaded_file(exp_file, "Trips", selected_trip) if exp_file else ""
                conn.execute('INSERT INTO expenses (trip_name, description, amount, file_path) VALUES (?, ?, ?, ?)', 
                           (selected_trip, expense_desc, expense_amount, file_path))
                conn.commit()
                st.success("Το έξοδο καταχωρήθηκε στον φάκελο!")
                st.rerun()
            
            trip_expenses = pd.read_sql_query('SELECT description as Περιγραφή, amount as Ποσό FROM expenses WHERE trip_name = ?', conn, params=(selected_trip,))
            
            if not trip_expenses.empty:
                st.write("Λίστα Εξόδων Ταξιδιού:")
                st.dataframe(trip_expenses)
                
                folder_path = os.path.join("uploads", "Trips", create_safe_folder_name(selected_trip))
                if os.path.exists(folder_path):
                    files = os.listdir(folder_path)
                    if files:
                        st.write("Αρχεία Φακέλου:")
                        for f in files:
                            st.write(f"- {f}")
