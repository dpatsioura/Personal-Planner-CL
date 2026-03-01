import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Command Center", layout="wide")

if 'expenses' not in st.session_state:
    st.session_state.expenses = []

st.title("Academic Command Center")
st.subheader("Οργάνωση, Projects και Ταξίδια")

col1, col2 = st.columns(2)

with col1:
    st.header("Ενεργά Projects & Deadlines")
    st.info("Αξιολόγηση ερευνητικού προγράμματος (Λήγει: 15 Μαρτίου)")
    st.warning("Κατάθεση εξόδων συνεδρίου στο Παρίσι (Εκκρεμεί)")
    
    st.text_input("Νέο Project ή Εργασία")
    st.date_input("Προθεσμία")
    st.button("Προσθήκη Εργασίας")

with col2:
    st.header("Travel & Reimbursement Vault")
    st.write("Καταχώρηση εξόδων και ανέβασμα αποδείξεων.")
    
    expense_name = st.text_input("Περιγραφή Εξόδου (π.χ. Ταξί για αεροδρόμιο)")
    expense_amount = st.number_input("Ποσό σε Ευρώ", min_value=0.0, format="%.2f")
    
    if st.button("Προσθήκη Εξόδου"):
        st.session_state.expenses.append({"Περιγραφή": expense_name, "Ποσό": expense_amount})
        st.success("Το έξοδο προστέθηκε!")
        
    if st.session_state.expenses:
        df = pd.DataFrame(st.session_state.expenses)
        st.dataframe(df)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Έξοδα')
        processed_data = output.getvalue()
        
        st.download_button(
            label="Κατέβασμα λίστας εξόδων σε Excel",
            data=processed_data,
            file_name="exoda_taxidiou.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    st.write("Ανέβασε εδώ το αντίστοιχο παραστατικό:")
    uploaded_file = st.file_uploader("Επιλογή αρχείου", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        st.success("Το αρχείο ανέβηκε με επιτυχία. Είναι έτοιμο για το claim!")
