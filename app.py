import streamlit as st
import pandas as pd
import sqlite3
import os
import re
from datetime import date, datetime

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

conn = sqlite3.connect('command_center_v6.db', check_same_thread=False)

conn.execute('''CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, proposal_deadline TEXT, date_from TEXT, date_to TEXT, total_funding REAL)''')
conn.execute('''CREATE TABLE IF NOT EXISTS stakeholders (id INTEGER PRIMARY KEY, project_name TEXT, name TEXT, funding REAL, role TEXT)''')
conn.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, project_name TEXT, stakeholder_name TEXT, quarter TEXT, description TEXT, deadline TEXT)''')

conn.execute('''CREATE TABLE IF NOT EXISTS trips (id INTEGER PRIMARY KEY, name TEXT, project TEXT, date_from TEXT, date_to TEXT, location TEXT)''')
conn.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, trip_name TEXT, description TEXT, amount REAL, file_path TEXT)''')

conn.execute('''CREATE TABLE IF NOT EXISTS personal_tasks (id INTEGER PRIMARY KEY, title TEXT, deadline TEXT, progress INTEGER, notes TEXT, file_path TEXT)''')
conn.commit()

st.title("Academic Command Center")

tab1, tab2, tab3 = st.tabs(["Έργα & Προτάσεις", "Ταξίδια & Έξοδα", "Personal Planner"])

with tab1:
    with st.expander("Δημιουργία Νέου Έργου ή Πρότασης"):
        with st.form("new_project_form", clear_on_submit=True):
            new_project = st.text_input("Όνομα Έργου / Ακρωνύμιο")
            new_funding = st.number_input("Συνολική Χρηματοδότηση σε Ευρώ", min_value=0.0, format="%.2f")
            
            st.write("Χρονοδιάγραμμα")
            new_deadline = st.date_input("Deadline Υποβολής Πρότασης", format="DD/MM/YYYY")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                new_proj_from = st.date_input("Έναρξη Έργου (Αν εγκριθεί)", format="DD/MM/YYYY")
            with col_p2:
                new_proj_to = st.date_input("Λήξη Έργου", format="DD/MM/YYYY")
            
            submitted_proj = st.form_submit_button("Δημιουργία Φακέλου Έργου")
            if submitted_proj:
                if new_project:
                    conn.execute('INSERT INTO projects (name, proposal_deadline, date_from, date_to, total_funding) VALUES (?, ?, ?, ?, ?)', 
                               (new_project, new_deadline.strftime('%d/%m/%Y'), new_proj_from.strftime('%d/%m/%Y'), new_proj_to.strftime('%d/%m/%Y'), new_funding))
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
                with st.form("new_stakeholder_form", clear_on_submit=True):
                    sh_name = st.text_input("Όνομα Φορέα ή Εταίρου")
                    sh_role = st.text_input("Ρόλος (π.χ. Συντονιστής)")
                    sh_funding = st.number_input("Προϋπολογισμός Εταίρου", min_value=0.0, format="%.2f")
                    
                    submitted_sh = st.form_submit_button("Προσθήκη Stakeholder")
                    if submitted_sh:
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
                    st.info("Πρόσθεσε πρώτα stakeholders στην προηγούμενη καρτέλα.")
                else:
                    st.write("Ανάθεση Task")
                    with st.form("new_task_form", clear_on_submit=True):
                        task_sh = st.selectbox("Επιλογή Stakeholder", sh_list)
                        task_q = st.selectbox("Τρίμηνο", ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"])
                        task_desc = st.text_input("Περιγραφή Task ή Παραδοτέου")
                        task_dead = st.date_input("Αυστηρό Deadline Task", format="DD/MM/YYYY")
                        
                        submitted_task = st.form_submit_button("Προσθήκη Task")
                        if submitted_task:
                            conn.execute('INSERT INTO tasks (project_name, stakeholder_name, quarter, description, deadline) VALUES (?, ?, ?, ?, ?)', 
                                       (selected_project, task_sh, task_q, task_desc, task_dead.strftime('%d/%m/%Y')))
                            conn.commit()
                            st.success("Το task ανατέθηκε!")
                            st.rerun()
                        
                tasks_df = pd.read_sql_query('SELECT quarter as Quarter, stakeholder_name as Εταίρος, description as Περιγραφή, deadline as Προθεσμία FROM tasks WHERE project_name = ? ORDER BY quarter', conn, params=(selected_project,))
                if not tasks_df.empty:
                    st.dataframe(tasks_df)

            with ptab3:
                with st.form("new_proj_file_form", clear_on_submit=True):
                    proj_file = st.file_uploader("Προσθήκη Αρχείου", type=["pdf", "docx", "png", "jpg", "xlsx"])
                    submitted_pfile = st.form_submit_button("Ανέβασμα Αρχείου Έργου")
                    if submitted_pfile:
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
        with st.form("new_trip_form", clear_on_submit=True):
            new_trip_project = st.text_input("Έργο / Project (Για το οποίο γίνεται το ταξίδι)")
            new_trip_location = st.text_input("Προορισμός / Τοποθεσία")
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                new_trip_from = st.date_input("Ημερομηνία Αναχώρησης", format="DD/MM/YYYY")
            with col_d2:
                new_trip_to = st.date_input("Ημερομηνία Επιστροφής", format="DD/MM/YYYY")
                
            submitted_trip = st.form_submit_button("Δημιουργία Φακέλου Ταξιδιού")
            if submitted_trip:
                if new_trip_location:
                    formatted_date = new_trip_from.strftime("%d-%m-%Y") 
                    generated_trip_name = f"{new_trip_location} ({formatted_date})"
                    
                    conn.execute('INSERT INTO trips (name, project, date_from, date_to, location) VALUES (?, ?, ?, ?, ?)', 
                               (generated_trip_name, new_trip_project, new_trip_from.strftime('%d/%m/%Y'), new_trip_to.strftime('%d/%m/%Y'), new_trip_location))
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
            
            with st.form("new_expense_form", clear_on_submit=True):
                expense_desc = st.text_input("Περιγραφή Εξόδου (π.χ. Ταξί)")
                expense_amount = st.number_input("Ποσό", min_value=0.0, format="%.2f")
                exp_file = st.file_uploader("Απόδειξη", type=["pdf", "png", "jpg"])
                
                submitted_exp = st.form_submit_button("Προσθήκη Εξόδου")
                if submitted_exp:
                    file_path = save_uploaded_file(exp_file, "Trips", selected_trip) if exp_file else ""
                    conn.execute('INSERT INTO expenses (trip_name, description, amount, file_path) VALUES (?, ?, ?, ?)', 
                               (selected_trip, expense_desc, expense_amount, file_path))
                    conn.commit()
                    st.success("Το έξοδο καταχωρήθηκε στον φάκελο!")
                    st.rerun()
            
            trip_expenses = pd.read_sql_query('SELECT id, description, amount, file_path FROM expenses WHERE trip_name = ?', conn, params=(selected_trip,))
            
            if not trip_expenses.empty:
                st.write("Λίστα Εξόδων Ταξιδιού:")
                
                col_h1, col_h2, col_h3, col_h4 = st.columns([3, 2, 2, 1])
                col_h1.write("Περιγραφή")
                col_h2.write("Ποσό")
                col_h3.write("Αρχείο")
                col_h4.write("Διαγραφή")
                
                for index, row in trip_expenses.iterrows():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    col1.write(row['description'])
                    col2.write(f"{row['amount']:.2f} €")
                    
                    file_p = row['file_path']
                    if pd.notna(file_p) and file_p != "":
                        if os.path.exists(file_p):
                            with open(file_p, "rb") as file:
                                file_content = file.read()
                            file_name = os.path.basename(file_p)
                            col3.download_button(label="📄", data=file_content, file_name=file_name, key=f"dl_exp_{row['id']}")
                        else:
                            col3.write("Λείπει")
                    else:
                        col3.write("-")
                        
                    if col4.button("🗑️", key=f"del_exp_{row['id']}"):
                        conn.execute('DELETE FROM expenses WHERE id = ?', (row['id'],))
                        conn.commit()
                        if pd.notna(file_p) and file_p != "" and os.path.exists(file_p):
                            os.remove(file_p)
                        st.rerun()

with tab3:
    st.header("Ειδοποιήσεις & Επείγοντα")
    ptasks_df = pd.read_sql_query('SELECT * FROM personal_tasks ORDER BY deadline', conn)
    
    today = date.today()
    has_alerts = False
    
    for index, row in ptasks_df.iterrows():
        if row['progress'] < 100:
            try:
                task_date = datetime.strptime(row['deadline'], '%d/%m/%Y').date()
                days_left = (task_date - today).days
                if days_left < 0:
                    st.error(f"Έληξε: {row['title']} (Είχε προθεσμία στις {row['deadline']})")
                    has_alerts = True
                elif days_left <= 7:
                    st.warning(f"Πλησιάζει: {row['title']} (Λήγει σε {days_left} μέρες)")
                    has_alerts = True
            except ValueError:
                pass
                
    if not has_alerts:
        st.info("Δεν υπάρχουν επείγουσες εκκρεμότητες για τις επόμενες 7 ημέρες.")
        
    st.divider()

    with st.expander("Προσθήκη Νέας Εργασίας"):
        with st.form("new_personal_task_form", clear_on_submit=True):
            ptask_title = st.text_input("Τίτλος Εργασίας")
            ptask_deadline = st.date_input("Προθεσμία", format="DD/MM/YYYY")
            ptask_progress = st.slider("Πρόοδος (%)", 0, 100, 0)
            ptask_notes = st.text_area("Σχόλια / Σημειώσεις")
            ptask_file = st.file_uploader("Συνημμένο Αρχείο", type=["pdf", "docx", "png", "jpg", "xlsx"])
            
            submitted_ptask = st.form_submit_button("Αποθήκευση Εργασίας")
            if submitted_ptask:
                if ptask_title:
                    file_path = save_uploaded_file(ptask_file, "Planner", ptask_title) if ptask_file else ""
                    conn.execute('INSERT INTO personal_tasks (title, deadline, progress, notes, file_path) VALUES (?, ?, ?, ?, ?)', 
                               (ptask_title, ptask_deadline.strftime('%d/%m/%Y'), ptask_progress, ptask_notes, file_path))
                    conn.commit()
                    st.success("Η εργασία προστέθηκε στο πλάνο σου!")
                    st.rerun()
                else:
                    st.error("Γράψε έναν τίτλο για την εργασία.")
                    
    st.subheader("Η Λίστα μου")
    
    if not ptasks_df.empty:
        for index, row in ptasks_df.iterrows():
            with st.container():
                col_t1, col_t2 = st.columns([4, 1])
                with col_t1:
                    st.write(f"📌 {row['title']} (Λήξη: {row['deadline']})")
                with col_t2:
                    if st.button("🗑️ Διαγραφή", key=f"del_ptask_{row['id']}"):
                        conn.execute('DELETE FROM personal_tasks WHERE id = ?', (row['id'],))
                        conn.commit()
                        if pd.notna(row['file_path']) and row['file_path'] != "" and os.path.exists(row['file_path']):
                            os.remove(row['file_path'])
                        st.rerun()
                
                st.progress(row['progress'] / 100.0)
                
                if pd.notna(row['notes']) and row['notes'].strip() != "":
                    st.caption("Σημειώσεις:")
                    st.write(row['notes'])
                    
                if pd.notna(row['file_path']) and row['file_path'] != "":
                    if os.path.exists(row['file_path']):
                        with open(row['file_path'], "rb") as file:
                            file_content = file.read()
                        file_name = os.path.basename(row['file_path'])
                        st.download_button(label=f"📄 Λήψη Αρχείου: {file_name}", data=file_content, file_name=file_name, key=f"dl_ptask_{row['id']}")
                st.divider()
    else:
        st.write("Η λίστα είναι άδεια.")
