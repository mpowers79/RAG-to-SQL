# File: assistant.py
# Description: this is the conversational assistant to help the user form their query
#  
#
# Copyright (c) 2025 Michael Powers
#
# Usage: 
#   
# 
#

import streamlit as st
from internal_db import get_process_status, delete_process_status
from prompts import ASSISTANT_PROMPT_TEMPLATE
from gen_sql import generate_thinking_agent_response
import json
import google.generativeai as genai
import base64
from pathlib import Path

api_key="YOUR_API_KEY"
gemini_model = 'gemini-2.5-flash-lite-preview-06-17'

def show_img(file_name):

    image_path = Path(__file__).parent / "./images" / file_name
    with open(image_path, 'rb') as img_file:
        base64_image = base64.b64encode(img_file.read()).decode()
        if file_name.lower().endswith('.png'):
            mime_type = 'image/png'
        elif file_name.lower().endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        elif file_name.lower().endswith('.gif'):
            mime_type = 'image/gif'
        else:
            mime_type = 'image/webp'
        html_string = f"""    
        <img src="data:{mime_type};base64,{base64_image}" 
             alt="My Image" style= max-height:100%; >
             
        """
        return html_string

hide_streamlit_header_css = """
<style>
/* Hide the Streamlit header (top bar with hamburger menu and deploy button) */
header {
    visibility: hidden;
    height: 0%;
    position: fixed;
}

/* Hide the hamburger menu icon */
#MainMenu {
    visibility: hidden;
}

/* Hide the "Deploy" button (often appears on localhost) */
.stDeployButton {
    display: none;
}

/* Hide the "Made with Streamlit" footer */
footer {
    visibility: hidden;
}

/* Optional: Adjust top padding if hiding the header creates unwanted space */
.block-container {
    padding-top: 0rem;
    padding-bottom: 0rem;
    padding-left: 1rem; /* Adjust as needed */
    padding-right: 1rem; /* Adjust as needed */
}

/* Also hide any anchor links next to headers if you're using st.markdown or st.header */
h1 > div > a { display: none !important; }
h2 > div > a { display: none !important; }
h3 > div > a { display: none !important; }
h4 > div > a { display: none !important; }
h5 > div > a { display: none !important; }
h6 > div > a { display: none !important; }

.navbar span {{
    float: right;
    display: inline-block;
    height: 28px;
    overflow: hidden;
}}
.navbar img {{
    max-height: 28px;
    width: auto;
    vertical-align: middle;
}}
.navbar span img { 
    max-height: 28px !important;
    width: auto;
    vertical-align: middle;
    margin-left: 5px;
}
</style>
"""


st.html(hide_streamlit_header_css)


if 'user_name' not in st.session_state.keys():
    st.session_state.user_name = "default_user"

if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": 'Start by stating your goal... "I need to find our most valuable customer segments."',
        }
    ]

if "chat_engine" not in st.session_state.keys():
    genai.configure(api_key=api_key)# api_key=os.getenv("API_KEY")
    model = genai.GenerativeModel(model_name=gemini_model, system_instruction=ASSISTANT_PROMPT_TEMPLATE)
    st.session_state.chat_engine = model.start_chat()
    st.session_state.generation_config = genai.GenerationConfig(response_mime_type="application/json")


NAV_BAR = f"""

<nav class="navbar"  style="  position: relative; width: 100%; z-index: 9999999 !important; margin-left: 0; margin-right: 0; padding: 6px; box-shadow: 0 2px 2px 0 rgba(0,0,0,0.2);">
<span style = "color: #2d82fe; font-size: 30px; font-weight: bold;">RAG-to-SQL App</span>
<span style="float: right; padding: 10px 25px;">({st.session_state.user_name})  {show_img('default-user-icon.jpg')} 
</span>

    """
st.html(NAV_BAR)

st.subheader("Ask a deeper question of your data.")
st.text("Tell us what business problem is on your mind. Our 'Insight Guide' will ask you a few questions to help you structure your analysis and find the data you need to make a decision.")


def parse_response(response):
   
    try:
        data = json.loads(response.text)
        if data.get("is_ready_for_pipeline"):
            query_components = data.get('query_components')
            problem = query_components.get("business_problem")
            primary_segment_description = query_components.get("primary_segment_description")
            metric_to_measure = query_components.get("metric_to_measure")

            query = f"Retrieve data. Purpose: {problem}. Segmentation Criteria: {primary_segment_description}. Target Metric: {metric_to_measure}."
            print(f'Sending query to pipeline: {query}')
            # CALL PIPELINE HERE
        message = data.get("message_to_user")
        return message
    except Exception as e:
        print(f"\n---Error decoding JSON Response: {e} | Response:{response.text}")
        return "Sorry: error occurred"


if prompt := st.chat_input("Ask a question"):
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        response = st.session_state.chat_engine.send_message(prompt, generation_config=st.session_state.generation_config)
        result = parse_response(response)
        st.write(result)
        message = {"role": "assistant", "content": result}
        st.session_state.messages.append(message)
        




