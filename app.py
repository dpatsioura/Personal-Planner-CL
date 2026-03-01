import streamlit as st

st.set_page_config(page_title="Command Center", layout="wide")

st.title("Academic Command Center")
st.subheader("Οργάνωση, Projects και Ταξίδια")

col1, col2 = st.columns(2)

with col1:
    st.header("Ενεργά Projects & Deadlines")
    st.info("Αξιολόγηση ερευνητικού προγράμματος - Λήγει: 15 Μαρτίου")
    st.warning("Κατάθεση εξόδων συνεδρίου στο Παρίσι - Εκκρεμεί")
    
    st.text_input("Νέο Project / Εργασία")
    st.date_input("Προθεσμία")
    st.button("Προσθήκη Εργασίας")

with col2:
    st.header("Travel & Reimbursement Vault")
    st.write("Ανέβασε εδώ αποδείξεις, εισιτήρια και τιμολόγια από τα ταξίδια.")
    
    uploaded_file = st.file_uploader("Επιλογή αρχείου", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        st.success("Το αρχείο ανέβηκε με επιτυχία. Είναι έτοιμο για το επόμενο claim!")
