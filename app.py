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

conn = sqlite3.connect('command_center_v4.db', check_same_thread=False)

conn.execute('''CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, proposal_deadline TEXT, date_from TEXT, date_to TEXT, total_funding REAL)''')
conn.execute('''CREATE TABLE IF NOT EXISTS stakeholders (id INTEGER PRIMARY KEY, project_name TEXT, name TEXT, funding REAL, role TEXT)''')
conn.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, project_name TEXT, stakeholder_name TEXT, quarter TEXT, description TEXT, deadline TEXT)''')

conn.execute('''CREATE TABLE IF NOT EXISTS trips (id INTEGER PRIMARY KEY, name TEXT, project TEXT, date_from TEXT, date_to TEXT, location TEXT)''')
conn.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, trip_name TEXT, description TEXT, amount REAL, file_path TEXT)''')
conn.commit()

st.title("Academic Command Center")

tab1, tab2 = st.tabs(["Έργα & Προτάσεις", "Ταξίδια & Έξοδα"])

with tab1:
    with st.expander("Δημιουργία Νέου Έργου ή Πρότασης"):
        new_project = st.text_input("Όνομα Έργου / Ακρωνύμιο")
        new_funding = st.number_input("Συνολική Χρηματοδότηση σε Ευρώ", min_value=0.0, format="%.2f")
        
        st.write("Χρονοδιάγραμμα")
        new_deadline = st.date_input("Deadline Υποβολής Πρότασης")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            new_proj_from = st.date_input("Έναρξη Έργου (Αν εγκριθεί)")
        with col_p2:
            new_proj_to = st.date_input("Λήξη Έργου")
        
        if st.button("Δημιουργία Φακέλου Έργου"):
            if new_project:
                conn.execute('INSERT INTO projects (name, proposal_deadline, date_from, date_to, total_funding) VALUES (?, ?, ?, ?, ?)', 
                           (new_project, str(new_deadline), str(new_proj_from), str(new_proj_to), new_funding))
                conn.commit()
                os.makedirs(os.path.join("uploads", "Projects", create_safe_folder_name(new_project)), exist_ok=True)
                st.success("Το έργο δημιουργήθηκε!")
                st.rerun()
            else:
                st.error("Γράψε ένα όνομα για το έργο.")

    projects_df = pd.read_sql_query('SELECT * FROM projects', conn)
    if not projects_df.empty:
        project_names = projects_df['name'].tolist()
        selected_project = st.selectbox("Άνοιγμα Φακέλου Έργου", ["Επίλεξε..."] + project_names)
        
        if selected_project != "Επίλεξε...":
            proj_info = projects_df[projects_df['name'] == selected_project].iloc[0]
            st.subheader(f"Έργο: {selected_project}")
            st.caption(f"Προϋπολογισμός: {proj_info['total_funding']}€ | Υποβολή: {proj_info['proposal_deadline']} | Διάρκεια: {proj_info['date_from']} έως {proj_info['date_to']}")
            
            ptab1, ptab2, ptab3 = st.tabs(["Συνεργάτες & Εταίροι", "Quarters & Tasks", "Αρχεία"])
            
            with ptab1:
                st.write("Προσθήκη Νέου Stakeholder")
                sh_name = st.text_input("Όνομα Φορέα ή Εταίρου")
                sh_role = st.text_input("Ρόλος (π.χ. Συντονιστής, WP Leader)")
                sh_funding = st.number_input("Προϋπολογισμός Εταίρου", min_value=0.0, format="%.2f")
                
                if st.button("Προσθήκη Stakeholder"):
                    if sh_name:
                        conn.execute('INSERT INTO stakeholders (project_name, name, funding, role) VALUES (?, ?, ?, ?)', 
                                   (selected_project, sh_name, sh_funding, sh_role))
                        conn.commit()
                        st.success("Ο συνεργάτης προστέθηκε!")
                        st.rerun()
                        
                sh_df = pd.read_sql_query('SELECT name as Εταίρος, role as Ρόλος, funding as Ποσό FROM stakeholders WHERE project_name = ?', conn, params=(selected_project,))
                if not sh_df.empty:
                    st.dataframe(sh_df)

            with ptab2:
                sh_list = pd.read_sql_query('SELECT name FROM stakeholders WHERE project_name = ?', conn, params=(selected_project,))['name'].tolist()
                
                if not sh_list:
                    st.info("Πρόσθεσε πρώτα stakeholders στην προηγούμενη καρτέλα για να τους αναθέσεις tasks.")
                else:
                    st.write("Ανάθεση Task")
                    task_sh = st.selectbox("Επιλογή Stakeholder", sh_list)
                    task_q = st.selectbox("Τρίμηνο", ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10", "Q11", "Q12"])
                    task_desc = st.text_input("Περιγραφή Task ή Παραδοτέου")
                    task_dead = st.date_input("Αυστηρό Deadline Task")
                    
                    if st.button("Προσθήκη Task"):
                        conn.execute('INSERT INTO tasks (project_name, stakeholder_name, quarter, description, deadline) VALUES (?, ?, ?, ?, ?)', 
                                   (selected_project, task_sh, task_q, task_desc, str(task_dead)))
                        conn.commit()
                        st.success("Το task ανατέθηκε!")
                        st.rerun()
                        
                tasks_df = pd.read_sql_query('SELECT quarter as Quarter, stakeholder_name as Εταίρος, description as Περιγραφή, deadline as Προθεσμία FROM tasks WHERE project_name = ? ORDER BY quarter', conn, params=(selected_project,))
                if not tasks_df.empty:
                    st.dataframe(tasks_df)

            with ptab3:
                proj_file = st.file_uploader("Προσθήκη Αρχείου", type=["pdf", "docx", "png", "jpg", "xlsx"])
                if st.button("Ανέβασμα Αρχείου Έργου"):
                    if proj_file:
                        save_uploaded_file(proj_file, "Projects", selected_project)
                        st.success("Το αρχείο αποθηκεύτηκε!")
                        st.rerun()
                
                folder_path = os.path.join("uploads", "Projects", create_safe_folder_name(selected_project))
                if os.path.exists(folder_path):
                    files = os.listdir(folder_path)
                    if files:
                        st.write("Περιεχόμενα Φακέλου:")
                        for f in files:
                            col_f1, col_f2 = st.columns([4, 1])
                            with col_f1:
                                st.write(f)
                            with col_f2:
                                if st.button("Διαγραφή", key=f"del_proj_{f}"):
                                    os.remove(os.path.join(folder_path, f))
                                    st.rerun()
                    else:
                        st.write("Ο φάκελος δεν έχει αρχεία ακόμα.")

with tab2:
    with st.expander("Δημιουργία Νέου Ταξιδιού"):
        new_trip_project = st.text_input("Έργο / Project (Για το οποίο γίνεται το ταξίδι)")
        new_trip_location = st.text_input("Προορισμός / Τοποθεσία")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            new_trip_from = st.date_input("Ημερομηνία Αναχώρησης")
        with col_d2:
            new_trip_to = st.date_input("Ημερομηνία Επιστροφής")
            
        if st.button("Δημιουργία Φακέλου Ταξιδιού"):
            if new_trip_location:
                formatted_date = new_trip_from.strftime("%d-%m-%Y")
                generated_trip_name = f"{new_trip_location} ({formatted_date})"
                
                conn.execute('INSERT INTO trips (name, project, date_from, date_to, location) VALUES (?, ?, ?, ?, ?)', 
                           (generated_trip_name, new_trip_project, str(new_trip_from), str(new_trip_to), new_trip_location))
                conn.commit()
                os.makedirs(os.path.join("uploads", "Trips", create_safe_folder_name(generated_trip_name)), exist_ok=True)
                st.success("Ο φάκελος ταξιδιού δημιουργήθηκε!")
                st.rerun()
            else:
                st.error("Γράψε έναν προορισμό για να δημιουργηθεί ο φάκελος.")

    trips_df = pd.read_sql_query('SELECT * FROM trips', conn)
    if not trips_df.empty:
        trip_names = trips_df['name'].tolist()
        selected_trip = st.selectbox("Άνοιγμα Φακέλου Ταξιδιού", ["Επίλεξε..."] + trip_names)
        
        if selected_trip != "Επίλεξε...":
            trip_info = trips_df[trips_df['name'] == selected_trip].iloc[0]
            st.subheader(f"Μέσα στον φάκελο: {selected_trip}")
            st.caption(f"Έργο: {trip_info['project']} | Προορισμός: {trip_info['location']} | Διάρκεια: {trip_info['date_from']} έως {trip_info['date_to']}")
            
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
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f)
                        with col2:
                            if st.button("Διαγραφή", key=f"del_trip_{f}"):
                                os.remove(os.path.join(folder_path, f))
                                st.rerun()
