## Note
odoo_api_demo.py was not optimised by me so take a look for yourself

# Odoo CRM Chatbot Integration with Google Gemini 2.5-flash
![Odoo CRM Chatbot](https://img.shields.io/badge/Odoo-CRM-blue)
![Google Gemini](https://img.shields.io/badge/Google-Gemini-2.5--flash)
![Python](https://img.shields.io/badge/Python-3.x-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.13.0-red)

## Overview
This is a standalone chatbot module that integrates with your Odoo CRM instance using the Google Gemini API. It allows natural dialogue with users, collects lead information (name, email, phone, requirements), validates inputs, and automatically creates leads in Odoo CRM.

## Requirements
- Python 3.x
- Google Gemini API key from [aistudio.google.com](https://aistudio.google.com)
- Running Odoo instance at http://localhost:8069
- Odoo database credentials

## Installation
1. Navigate to the project directory: `..\aicrm`
2. Install dependencies: `pip install -r requirements.txt`

## Usage
1. Run the chatbot: `python -m streamlit run chatbot.py`
2. Open your browser and go to http://localhost:8501
3. In the sidebar, enter your Google Gemini API key and Odoo credentials.
4. Start chatting in the main window. The bot will guide you to provide necessary information.
5. Once all information is collected, it will create a lead in Odoo CRM.

## Features
- Natural conversational flow using Gemini AI
- Information collection and validation
- Automatic lead creation in Odoo via XML-RPC
- Context maintenance across conversation
- Error handling for API calls and extractions

## Deployment
This module can be deployed on any server alongside your Odoo setup. Ensure the server has Python and the required libraries installed. Run the Streamlit app as a service for production use.

## Notes
- Make sure your Odoo instance allows XML-RPC connections.
- For production, secure the API keys and credentials appropriately.
- The chatbot uses Gemini 2.5-flash model; you can change it in the code if needed.