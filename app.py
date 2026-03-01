import streamlit as st
import pandas as pd
import sqlite3
import os
import re
import zipfile
from datetime import date, datetime
from io import BytesIO

st.set_page_config(page_title="Personal Planner", layout="wide")

def create_safe_folder_name(name):
    clean_name = re.sub(r'[^a-zA-Z0-9\u0370-\u03FF ]', '_', name.strip())
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

conn = sqlite3.connect('command_center_v7.db', check_same_thread=False)

conn.execute('''CREATE TABLE IF NOT EXISTS trips (id INTEGER PRIMARY KEY, name TEXT, project TEXT, date_from TEXT, date_to TEXT, location TEXT)''')
conn.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, trip_name TEXT, description TEXT, amount REAL, file_path TEXT)''')
conn.execute('''CREATE TABLE IF NOT EXISTS personal_tasks (id INTEGER PRIMARY KEY, title TEXT, deadline TEXT, progress INTEGER, notes TEXT, file_path TEXT)''')
conn.commit()

st.title("Personal Planner")

tab1, tab2 = st.tabs(["Λίστα Εργασιών", "Ταξίδια & Έξοδα"])

with tab1:
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
                
                with st.expander("Επεξεργασία Εργασίας"):
                    with st.form(f"edit_ptask_{row['id']}"):
                        e_title = st.text_input("Τίτλος", value=row['title'], key=f"et_{row['id']}")
                        try:
                            e_dead_val = datetime.strptime(row['deadline'], '%d/%m/%Y').date()
                        except:
                            e_dead_val = today
                        e_deadline = st.date_input("Προθεσμία", value=e_dead_val, format="DD/MM/YYYY", key=f"ed_{row['id']}")
                        e_prog = st.slider("Πρόοδος (%)", 0, 100, int(row['progress']), key=f"ep_{row['id']}")
                        e_notes = st.text_area("Σημειώσεις", value=row['notes'] if pd.notna(row['notes']) else "", key=f"en_{row['id']}")
                        
                        if st.form_submit_button("Αποθήκευση Αλλαγών"):
                            conn.execute('UPDATE personal_tasks SET title=?, deadline=?, progress=?, notes=? WHERE id=?', 
                                         (e_title, e_deadline.strftime('%d/%m/%Y'), e_prog, e_notes, row['id']))
                            conn.commit()
                            st.rerun()
                st.divider()
    else:
        st.write("Η λίστα είναι άδεια.")

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
                    formatted_date = new_trip_from.strftime("%d_%m_%Y") 
                    generated_trip_name = f"{new_trip_location}_{formatted_date}"
                    
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
            st.subheader(f"Μέσα στον φάκελο: {selected_trip.replace('_', ' ')}")
            st.caption(f"Έργο: {trip_info['project']} | Προορισμός: {trip_info['location']} | Διάρκεια: {trip_info['date_from']} έως {trip_info['date_to']}")
            
            with st.expander("Επεξεργασία Στοιχείων Ταξιδιού"):
                with st.form("edit_trip_form"):
                    e_trip_project = st.text_input("Έργο", value=trip_info['project'])
                    e_trip_location = st.text_input("Προορισμός", value=trip_info['location'])
                    col_e1, col_e2 = st.columns(2)
                    try:
                        e_from_val = datetime.strptime(trip_info['date_from'], '%d/%m/%Y').date()
                        e_to_val = datetime.strptime(trip_info['date_to'], '%d/%m/%Y').date()
                    except:
                        e_from_val, e_to_val = today, today
                    with col_e1:
                        e_trip_from = st.date_input("Από", value=e_from_val, format="DD/MM/YYYY")
                    with col_e2:
                        e_trip_to = st.date_input("Έως", value=e_to_val, format="DD/MM/YYYY")

                    if st.form_submit_button("Αποθήκευση Αλλαγών Ταξιδιού"):
                        new_formatted_date = e_trip_from.strftime("%d_%m_%Y")
                        new_trip_name = f"{e_trip_location}_{new_formatted_date}"
                        old_trip_name = trip_info['name']

                        if new_trip_name != old_trip_name:
                            old_folder = os.path.join("uploads", "Trips", create_safe_folder_name(old_trip_name))
                            new_folder = os.path.join("uploads", "Trips", create_safe_folder_name(new_trip_name))

                            if os.path.exists(old_folder) and not os.path.exists(new_folder):
                                os.rename(old_folder, new_folder)

                            expenses_to_update = pd.read_sql_query('SELECT id, file_path FROM expenses WHERE trip_name=?', conn, params=(old_trip_name,))
                            for _, exp_row in expenses_to_update.iterrows():
                                old_fp = exp_row['file_path']
                                new_fp = old_fp
                                if pd.notna(old_fp) and old_fp != "":
                                    new_fp = old_fp.replace(create_safe_folder_name(old_trip_name), create_safe_folder_name(new_trip_name))
                                conn.execute('UPDATE expenses SET trip_name=?, file_path=? WHERE id=?', (new_trip_name, new_fp, exp_row['id']))
                            
                            conn.execute('UPDATE expenses SET trip_name=? WHERE trip_name=?', (new_trip_name, old_trip_name))
                        
                        conn.execute('UPDATE trips SET name=?, project=?, date_from=?, date_to=?, location=? WHERE id=?', 
                                     (new_trip_name, e_trip_project, e_trip_from.strftime('%d/%m/%Y'), e_trip_to.strftime('%d/%m/%Y'), e_trip_location, trip_info['id']))
                        conn.commit()
                        st.rerun()

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
                col_h4.write("Ενέργειες")
                
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
                        
                    with st.expander("Επεξεργασία Εξόδου"):
                        with st.form(f"edit_exp_{row['id']}"):
                            e_desc = st.text_input("Περιγραφή", value=row['description'], key=f"edesc_{row['id']}")
                            e_amount = st.number_input("Ποσό", value=float(row['amount']), format="%.2f", key=f"eam_{row['id']}")
                            if st.form_submit_button("Αποθήκευση Αλλαγών"):
                                conn.execute('UPDATE expenses SET description=?, amount=? WHERE id=?', (e_desc, e_amount, row['id']))
                                conn.commit()
                                st.rerun()

            folder_path = os.path.join("uploads", "Trips", create_safe_folder_name(selected_trip))
            if os.path.exists(folder_path):
                files_in_folder = os.listdir(folder_path)
                if files_in_folder:
                    st.divider()
                    st.write("Συγκεντρωτικά Αρχεία Ταξιδιού")
                    
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for file_name in files_in_folder:
                            file_full_path = os.path.join(folder_path, file_name)
                            if os.path.isfile(file_full_path):
                                zip_file.write(file_full_path, arcname=file_name)
                    
                    st.download_button(
                        label="📦 Λήψη όλων των αποδείξεων (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"{create_safe_folder_name(selected_trip)}_apodeixeis.zip",
                        mime="application/zip"
                    )
