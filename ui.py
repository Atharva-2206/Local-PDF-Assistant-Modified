# ui.py
import streamlit as st
import requests
import time
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Multi-Document Chat", layout="wide")
st.title("📄 Chat with your Documents")

def display_job_status(job_id):
    st.info(f"Processing job ID: {job_id}. This window will update automatically.")
    with st.empty():
        while True:
            try:
                response = requests.get(f"{BACKEND_URL}/status/{job_id}")
                if response.status_code == 200:
                    job_data = response.json()
                    status = job_data.get("status")
                    details = job_data.get("details")

                    if status == "complete":
                        st.success("✔️ Processing complete!")
                        st.session_state.processed_data = details # Save the entire result object
                        del st.session_state.job_id
                        break
                    elif status == "failed":
                        st.error(f"❌ Processing Failed: {details}")
                        del st.session_state.job_id
                        break
                    else:
                        st.write(f"⏳ Status: {status} - {details}")
                else:
                    time.sleep(2)
            except requests.exceptions.RequestException:
                st.write("Connecting to backend...")
            time.sleep(2)
    st.rerun()

# --- Sidebar for File Upload ---
with st.sidebar:
    st.header("1. Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload a ZIP or multiple files",
        type=['pdf', 'docx', 'txt', 'csv', 'xlsx', 'zip'],
        accept_multiple_files=True
    )
    if st.button("Process Files") and uploaded_files:
        with st.spinner("Submitting files..."):
            files_to_send = [("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files]
            try:
                response = requests.post(f"{BACKEND_URL}/process/", files=files_to_send)
                if response.status_code == 202:
                    job_id = response.json().get("job_id")
                    st.session_state.job_id = job_id
                    if 'processed_data' in st.session_state:
                        del st.session_state['processed_data']
                    st.rerun()
                else:
                    st.error(f"Failed to start processing: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the backend: {e}")

# --- Main Page Logic ---

# If a job is active, show the status.
if 'job_id' in st.session_state:
    display_job_status(st.session_state.job_id)

# If processing is complete, set up the chat interface.
elif 'processed_data' in st.session_state:
    st.header("2. Chat about your Documents")
    
    # Create a dictionary for the user to select from
    processed_files = st.session_state.processed_data['files']
    master_id = st.session_state.processed_data['master_id']
    
    chat_options = {"All Documents": master_id}
    for file_info in processed_files:
        chat_options[file_info['filename']] = file_info['transaction_id']
        
    # Create the dropdown menu (selectbox)
    selected_doc_name = st.selectbox(
        "Choose a document to chat with:",
        options=list(chat_options.keys())
    )
    
    # Get the corresponding transaction ID for the selected document
    selected_txn_id = chat_options[selected_doc_name]
    
    # Use a unique key for the chat history based on the selected document
    chat_history_key = f"messages_{selected_txn_id}"
    if chat_history_key not in st.session_state:
        st.session_state[chat_history_key] = []

    # Display past messages for the selected document
    for author, message in st.session_state[chat_history_key]:
        with st.chat_message(author):
            st.markdown(message)

    if prompt := st.chat_input(f"Ask about {selected_doc_name}..."):
        st.session_state[chat_history_key].append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        history_for_api = [(q, a) for q, a in st.session_state[chat_history_key] if a is not None]

        chat_data = {
            "query": prompt,
            "transaction_id": selected_txn_id, # Use the selected ID
            "chat_history": history_for_api
        }
        
        with st.spinner("Thinking..."):
            response = requests.post(f"{BACKEND_URL}/chat/", json=chat_data)
            if response.status_code == 200:
                ai_response = response.json().get("response")
                st.session_state[chat_history_key].append(("assistant", ai_response))
                st.rerun() # Rerun to display the new message immediately
            else:
                st.error(f"Error from chat backend: {response.text}")

# If no job is active, show the initial message.
else:
    st.info("Please upload and process your documents in the sidebar to begin chatting.")