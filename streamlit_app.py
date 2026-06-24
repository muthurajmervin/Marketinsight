import json
import requests
import streamlit as st
from typing import Generator

# ============================================================
# Configuration
# ============================================================

API_URL = "http://localhost:8000/api/chat"

# ============================================================
# Streamlit Page Config
# ============================================================

st.set_page_config(
    page_title="Market Insight",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Market Insight")
st.markdown("Ask me anything about the stock market!")

# ============================================================
# Initialize Chat History
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

# ============================================================
# Display Chat History
# ============================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ============================================================
# SSE Stream Handler
# ============================================================

def stream_chat_response(prompt: str, thread_id: str) -> Generator[str, None, None]:
    """Stream response from FastAPI backend"""
    
    import uuid
    
    payload = {
        "prompt": {
            "content": prompt,
            "id": str(uuid.uuid4()),
            "role": "user"
        },
        "threadId": thread_id,
        "responseId": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(
            API_URL,
            json=payload,
            stream=True,
            timeout=30,  # Add timeout to prevent hanging
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
        )
        
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    try:
                        # Handle both JSON and plain text responses
                        if data_str.startswith('{'):
                            data = json.loads(data_str)
                            if 'content' in data:
                                yield data['content']
                        else:
                            # Plain text response (for error messages)
                            yield data_str
                    except json.JSONDecodeError:
                        # If not JSON, yield as plain text
                        yield data_str
                        
    except requests.exceptions.Timeout:
        yield "⏱️ **Request timed out.** The server is taking longer than expected to respond. Please try again."
    except requests.exceptions.RequestException as e:
        yield f"❌ **Error connecting to backend:** {str(e)}\n\nPlease check if the backend server is running on http://localhost:8000"

# ============================================================
# Chat Input Handler
# ============================================================

if prompt := st.chat_input("Ask about stocks..."):
    # Generate thread ID if not exists
    if "thread_id" not in st.session_state:
        import uuid
        st.session_state.thread_id = str(uuid.uuid4())
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response with streaming
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Show initial loading indicator
        loading_placeholder = st.empty()
        loading_placeholder.markdown("🔍 **Analyzing your question and fetching latest market data...**")
        
        # Stream response from backend
        response_started = False
        for chunk in stream_chat_response(prompt, st.session_state.thread_id):
            # Remove loading indicator once we start getting response
            if not response_started:
                loading_placeholder.empty()
                response_started = True
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        
        # Ensure loading indicator is removed even if no response
        if not response_started:
            loading_placeholder.empty()
        
        # Final message without cursor
        message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# ============================================================
# Sidebar Info
# ============================================================

with st.sidebar:
    st.header("About")
    st.markdown("This is a stock market analysis assistant powered by AI.")
    
    st.header("Session Info")
    if "thread_id" in st.session_state:
        st.text(f"Thread ID: {st.session_state.thread_id}")
    else:
        st.text("No active session")
    
    st.header("System Status")
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ Backend Online")
        else:
            st.error("❌ Backend Error")
    except:
        st.error("❌ Backend Offline")
    
    st.header("Tips")
    st.info("💡 If you experience delays, it may be due to API rate limits. Try again in a few minutes.")
