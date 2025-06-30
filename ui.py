import streamlit as st
import requests
import os

# Define the base URL for the FastAPI backend
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Chat with your Documents", layout="wide")
st.title("📄 Chat with your Documents")

# --- FILE UPLOADER AND PROCESSING ---
with st.sidebar:
    st.header("1. Upload Documents")
    # Allow multiple files to be uploaded
    uploaded_files = st.file_uploader(
        "Upload your files (.pdf, .docx, .txt, .csv, .xlsx, .zip)", 
        type=['pdf', 'docx', 'txt', 'csv', 'xlsx', 'zip'],
        accept_multiple_files=True
    )

    if st.button("Process Files") and uploaded_files:
        with st.spinner("Processing files... This may take a moment."):
            # Prepare files for the multipart/form-data request
            files_to_send = []
            for file in uploaded_files:
                files_to_send.append(("files", (file.name, file.getvalue(), file.type)))
            
            try:
                # Make the request to the backend's /process/ endpoint
                response = requests.post(f"{BACKEND_URL}/process/", files=files_to_send)
                
                if response.status_code == 200:
                    # Store the successful transaction_id in the session state
                    st.session_state.transaction_id = response.json().get("transaction_id")
                    st.session_state.messages = [] # Reset chat history
                    st.success(f"Files processed successfully! Transaction ID: {st.session_state.transaction_id}")
                else:
                    st.error(f"Error processing files: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the backend: {e}")

# --- CHAT INTERFACE ---
st.header("2. Chat about your Documents")

# Only show the chat interface if files have been successfully processed
if "transaction_id" in st.session_state:
    
    # Initialize chat history in session state if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display past chat messages
    for author, message in st.session_state.messages:
        with st.chat_message(author):
            st.markdown(message)

    # The chat input box at the bottom of the screen
    if prompt := st.chat_input("Ask a question about your documents..."):
        
        # Add user's message to the chat history and display it
        st.session_state.messages.append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare the chat history for the API call
        history_for_api = []
        for i in range(0, len(st.session_state.messages) - 1, 2):
            user_msg = st.session_state.messages[i]
            assistant_msg = st.session_state.messages[i+1]
            if user_msg[0] == "user" and assistant_msg[0] == "assistant":
                history_for_api.append((user_msg[1], assistant_msg[1]))
        
        chat_data = {
            "query": prompt,
            "transaction_id": st.session_state.transaction_id,
            "chat_history": history_for_api
        }
        
        # Get the AI's response from the backend
        with st.spinner("Thinking..."):
            try:
                response = requests.post(f"{BACKEND_URL}/chat/", json=chat_data)
                if response.status_code == 200:
                    ai_response = response.json().get("response")
                    # Add AI's response to the chat history and display it
                    st.session_state.messages.append(("assistant", ai_response))
                    with st.chat_message("assistant"):
                        st.markdown(ai_response)
                else:
                    st.error(f"Error getting response from chat: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the backend: {e}")
else:
    st.info("Please upload and process your documents in the sidebar to begin chatting.")