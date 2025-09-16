import streamlit as st
import google.generativeai as genai
import xmlrpc.client
import re

# Title
st.title("Odoo CRM Chatbot with Google Gemini")

# Sidebar for configuration
st.sidebar.title("Configuration")
gemini_api_key = st.sidebar.text_input("Google Gemini API Key", type="password")
odoo_url = "http://localhost:8069"
odoo_db = st.sidebar.text_input("Odoo Database Name", value="odoo")
odoo_username = st.sidebar.text_input("Odoo Username", value="admin")
odoo_password = st.sidebar.text_input("Odoo Password", type="password")

if not gemini_api_key:
    st.info("Please enter your Google Gemini API key to continue.")
    st.stop()

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.lead_info = {"name": None, "email": None, "phone": None, "requirements": None}

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Prepare context
    context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])

    # System prompt for Gemini
    system_prompt = """
You are a helpful CRM chatbot. Engage in natural conversation with the user.
Your goal is to collect the following information:
- Name
- Email
- Phone (optional)
- Requirements

Once you have all required information (name, email, requirements), confirm with the user and end your response with the exact phrase: [CREATE_LEAD]
If information is missing, politely ask for it in a natural way.
Maintain context from previous messages.
"""

    # Generate response
    try:
        response = model.generate_content(system_prompt + "\n\nConversation:\n" + context)
        bot_response = response.text
    except Exception as e:
        bot_response = f"Error generating response: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    with st.chat_message("assistant"):
        st.markdown(bot_response)

    # Check if ready to create lead
    if "[CREATE_LEAD]" in bot_response:
        # Extract information using Gemini
        extract_prompt = f"""
From the following conversation, extract:
- Name
- Email
- Phone (if provided)
- Requirements

Conversation:
{context}

Respond in JSON format: {{"name": "...", "email": "...", "phone": "...", "requirements": "..."}}
"""
        try:
            extract_response = model.generate_content(extract_prompt)
            # Parse JSON
            match = re.search(r'\{.*\}', extract_response.text, re.DOTALL)
            if match:
                import json
                extracted = json.loads(match.group(0))
                st.session_state.lead_info = extracted

                # Connect to Odoo
                try:
                    common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
                    uid = common.authenticate(odoo_db, odoo_username, odoo_password, {})

                    if uid:
                        models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')
                        lead_id = models.execute_kw(odoo_db, uid, odoo_password, 'crm.lead', 'create', [{
                            'name': extracted.get('name', 'New Lead') + ' Lead',
                            'contact_name': extracted.get('name'),
                            'email_from': extracted.get('email'),
                            'phone': extracted.get('phone'),
                            'description': extracted.get('requirements'),
                        }])
                        st.success(f"Lead created successfully in Odoo! Lead ID: {lead_id}")
                    else:
                        st.error("Odoo authentication failed. Please check credentials.")
                except Exception as e:
                    st.error(f"Error connecting to Odoo: {str(e)}")
            else:
                st.error("Failed to extract information.")
        except Exception as e:
            st.error(f"Error extracting information: {str(e)}")