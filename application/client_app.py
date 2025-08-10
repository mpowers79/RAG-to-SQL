# File: client_app.py
# Description: Streamlit app to interact with the SQL RAG pipeline
#
# Copyright (c) 2025 Michael Powers
#
# Usage:
#   streamlit run client_app.py
# 
#
import streamlit as st
from internal_db import get_process_status, delete_process_status
from gen_sql import generate_thinking_agent_response
from streamlit_autorefresh import st_autorefresh
from streamlit_extras.stylable_container import stylable_container
import streamlit.components.v1 as components
import markdown
import json
from pathlib import Path
import base64




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

##########################################
#
#     CSS
#
##########################################

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

.step-completed-bg {
  background-color: #2d82fe;

}
.step-completed-color{
  color: #2d82fe; 
}
.step-incomplete-bg {
  background-color: #d9d9d9;
 
}
.step-incomplete-color {
  color: #d9d9d9;
}

.line-completed {
    --line-color: #2d82fe;
}

.line-incomplete {
    --line-color: #d9d9d9;
}

.progress-container { 
 
  width: 100%;  
  
  margin: 10px auto;
  padding: 10px;
  
  /* border: 1px solid #444;*/ 
  text-align: center; 
} 

.progress-bar { 
  position: relative; 
  height: 20px; 
  margin-bottom: 10px; 

} 

.progress-bar::after { 
  content: ''; 
  position: absolute; 
  top: 50%; 
  left: 50%; 
  transform: translateY(-50%); 
  /* change this value to alter how long it is: left 40% is starting point, width 50% is longer */
  width: 135%; 
  height: 3px; 
   background-color:  var(--line-color, #d9d9d9); 

} 

.square { 
  position: absolute; 
  top: 50%; 
  left: 50%; 
  transform: translate(-50%, -50%); 
  width: 20px; 
  height: 20px; 
  /* background-color: #000; */
  z-index: 1; 
  display: flex;
  align-items: center;
  justify-content: center;
} 

.checkmark {
    color: white;
    font-size: 18px;
    font-weight: bold;
    /* Prevents the checkmark from affecting the square's height */
    line-height: 1;
}

.progress-text { 
  margin-top: 20px; 
}

.last-step .progress-bar::after {
  /* display: none;    */
  --line-color: #ffffff;


}

.in-progress .progress-bar::after {
    /* display: none; */
    --line-color: #ffffff;
}
/* animation */

.in-progress::after {
    content: '';
    position: absolute;
    
    /* Position it in the same place as the static line */
    width: 110%;
   
    top: 17%; /* Adjust this value to vertically center the line */
    left: 50%;

    height: 3px; 
    --c: no-repeat linear-gradient(#2d82fe 0 0); 
    background: var(--c), var(--c), #d7b8fc;
    background-size: 60% 100%;
    animation: l16 3s infinite;
}

@keyframes l16 {
    0%   { background-position: -150% 0, -150% 0 }
    66%  { background-position: 250% 0, -150% 0 }
    100% { background-position: 250% 0, 250% 0 }
}
.status-box {
        border-radius: 8px;
        margin: auto;
        border: 0px;
        text-align: center;
        font-size: 0.8em;
    }
    .status-in-progress {
        color: #ffffff;
        background-color: #2d82fe;
    }
    .status-completed {
        color: #ffffff;
        background-color: #16a34a;
    }
    .status-pending {
        color: #ffffff;
        background-color: #d9d9d9;
    }
    .inner-container{
        border-color: #2d82fe;
        border-radius: 5px;
        border-width: 1px;
        border-style: solid;
        padding: 20px;
        
        width: 95%;
        word-break: break-all;

    }
    .code-container{
        background-color: #f5f5f5;
        border: 1px solid #2d82fe;
        border-radius: 5px;
        font-family: monospace;
        padding: 20px;
        white-space: pre-wrap;
        width: 95%
    }
    .description-container {
        color: #777777;
        font-size: 1.1em;
        font-weight: bold;
        text-align: left;
        margin-top: 7px;
    }
    .highlighted-element {
                background-color: #2d82fe;
                color: #fefefe;
                font-family: monospace;
                padding: 0.2em 0.4em;
                border-radius: 3px;
                font-size: 0.9em;
                padding: 2px;
                /* white-space: nowrap; */

            }
   

    .muted-element {
        color: rgb(200, 200, 200);
    }

</style>
"""

st.html(hide_streamlit_header_css)

######################################


def invalid_question():
    if 'invalid_question' in st.session_state.keys() and st.session_state.invalid_question:
        return True
    return False

def compose_string_from_dict_element(element):
    if element is None:
        return "NONE"
    if isinstance(element, str):
        # Split by whitespace, wrap non-empty parts, and join with original whitespace
        parts = []
        last_idx = 0
        for i, char in enumerate(element):
            if char.isspace():
                if last_idx < i:
                    parts.append(f'<span class="highlighted-element">{element[last_idx:i]}</span> ')
                parts.append(char)
                last_idx = i + 1
        if last_idx < len(element):
            parts.append(f'<span class="highlighted-element">{element[last_idx:]}</span> ')
        return "".join(parts)
    elif isinstance(element, list):
        # Recursively process each string in the list and join them
        return "".join(compose_string_from_dict_element(item) for item in element)
    else:
        return ""
        print( TypeError(f"Element must be a string or a list of strings. Type: {type(element)}"))

def check_data(value):
    if value is None:
        return False

    if not isinstance(value, str):
        return False

    try:
        data = json.loads(value)
        if isinstance(data, dict):
            return True
        else:
            return False
    except Exception as e:
        return False

def load_progress_data():
    #print("DEBUG: read from DB")
    results = get_process_status(st.session_state.user_name)

    if results is None:
        st.session_state.show_question_interface = True
        return
    else:
        st.session_state.show_question_interface = False
       # print(f"\n\nDEBUG: process status\n\n{results}")


    if results.get('user_question'):
        st.session_state.user_question_status = True
        st.session_state.user_question = f"<span class='muted-element'>{results.get('user_question')}</span>"
    else:
        st.session_state.user_question_status = False
        st.session_state.user_question = ""
 
    if check_data(results.get('cleaned_question')):
        all_data = json.loads(results.get('cleaned_question'))
        st.session_state.cleaned_question_status = True
        cancel_process = all_data.get('cancel_process')
        rephrased = all_data.get('rephrased_question')
        
        if rephrased is None:
            rephrased = all_data.get('rephrased')
        if cancel_process:
            st.session_state.cleaned_question = f"<span style='color: red;'>Process canceled: Invalid Question.</span><br>{rephrased}"
            st.session_state.invalid_question = True
        else:
            st.session_state.cleaned_question = f"<span class='muted-element'>{rephrased}</span>"
            st.session_state.invalid_question = False
    else:
        st.session_state.cleaned_question_status = False
        st.session_state.cleaned_question = ""
        st.session_state.invalid_question = False

   
   
    if check_data(results.get('tables') ):
        all_data = json.loads(results.get('tables'))
        st.session_state.tables_status = True
        tables = all_data.get('tables')
        columns = all_data.get('columns')
        st.session_state.tables = f'Tables: &nbsp;{compose_string_from_dict_element(tables)} &nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;Columns:&nbsp; {compose_string_from_dict_element(columns)}<br>Resoning: <span class="muted-element">{all_data.get("reasoning")}</span>'

    else:
        st.session_state.tables_status = False
        st.session_state.tables = ""
    
    if results.get('joins') is not None:
    #if check_data(results.get('joins')):
        st.session_state.join_status = True
        all_data = json.loads(results.get('joins'))
        joins = all_data.get('joins')

        if joins == []:
            joins = "None Needed"
        else:
            joins = f"<span class='highlighted-element'>{joins}</span>"
        st.session_state.joins=f'Joins: {joins}\n<br>Reasoning: <span class="muted-element">{all_data.get("reasoning")}'
    else:
        #print('empy joins')
        st.session_state.join_status =False
        st.session_state.joins =""

    if check_data(results.get('grouping')):
        st.session_state.grouping_status = True
        all_data = json.loads(results.get('grouping'))
        grouping = all_data.get('group_by_columns')
        
        if grouping is None:
            grouping = all_data.get('group_by')

        aggregations = all_data.get('aggregations')
        if aggregations is None:
            aggregations = all_data.get('aggregation')

        st.session_state.grouping = f"Grouping: {compose_string_from_dict_element(grouping)}<br>Aggregations: <span class='highlighted-element'>{aggregations}</span><br>Reasoning: <span class='muted-element'>{all_data.get('reasoning')}</span>"

    else:
        st.session_state.grouping_status = False
        st.session_state.grouping = ""
   
    if check_data(results.get('calculations')):
        st.session_state.calculations_status = True
        all_data = json.loads(results.get('calculations'))
        calc = all_data.get('calculations')
        if calc == []:
            calc = "None Needed"
        else:
            calc = f"<span class='highlighted-element'>{calc}</span>"
            #calc = compose_string_from_dict_element(calc)


        st.session_state.calculations = f"Calculation: {calc}<br>Reasoning: <span class='muted-element'>{all_data.get('reasoning')}</span>"

    else:
        st.session_state.calculations_status = False
        st.session_state.calculations = ""
   
    if check_data(results.get('filtering')):
        st.session_state.filtering_status = True
        all_data = json.loads(results.get('filtering'))
        filters = all_data.get('filters')
        filters = str(filters)
        
        if filters == '[]':
            filters = "None Needed"
        else:
            filters = compose_string_from_dict_element(filters)

        st.session_state.filtering = f"Filters: {filters}<br>Reasoning: <span class='muted-element'>{all_data.get('reasoning')}</span>"

    else:
        st.session_state.filtering_status = False
        st.session_state.filtering = ""

    if results.get('sql'):
        st.session_state.sql_status = True
        sql = results.get('sql')
        st.session_state.sql = sql

    else:
        st.session_state.sql_status = False
        st.session_state.sql = ""
 


#########################################################################
#▗▄▄▄▖ ▗▖ ▗▖▗▄▄▄▖ ▗▄▄▖▗▄▄▄▖▗▄▄▄▖ ▗▄▖ ▗▖  ▗▖
#▐▌ ▐▌ ▐▌ ▐▌▐▌   ▐▌     █    █  ▐▌ ▐▌▐▛▚▖▐▌
#▐▌ ▐▌ ▐▌ ▐▌▐▛▀▀▘ ▝▀▚▖  █    █  ▐▌ ▐▌▐▌ ▝▜▌
#▐▙▄▟▙▖▝▚▄▞▘▐▙▄▄▖▗▄▄▞▘  █  ▗▄█▄▖▝▚▄▞▘▐▌  ▐▌
#########################################################################
def show_question_interface():
#############
#top right
# User selection box
# regular / power mode selection -> select local llama3 or gemini
    col_1, col_2, = st.columns([0.9, 0.1])
    with col_2:
        st.session_state.model = st.selectbox(
            "Mode Selection:",
            ("Local", "Gemini"),
            )
#############
# middle , box to enter search, and search button
    css_styles="""
    { 
        /* background-color: #525965; */
        border: 1px;
        border-radius: 5px;
        color: #2d82fe;
        padding-bottom: 15px;
        box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);

    }
                """
    with stylable_container( key="main_entry", css_styles=css_styles):
        with st.container(border=True):
            st.subheader("ASK YOUR QUESTION")
            prompt = st.chat_input("Enter question here")
            if prompt:
                print("DEBUG: start")
                st.session_state.show_question_interface = False
                ount = st_autorefresh(interval=1000, limit=1000, key="refreshcounter")
                if st.session_state.model == 'Gemini':
                    generate_thinking_agent_response(prompt, st.session_state.user_name, True)
                else:
                    generate_thinking_agent_response(prompt, st.session_state.user_name, False)
                
                print("Debug: start2")
                st.rerun()
                
            


############
# bottom
# 3 columns
# 3 rows
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                """
                RECOMMENDED SEARCH 1
                """
                st.button("➡️", key='b1')
            with st.container(border=True):  
                """
                RECOMMENDED SEARCH 4
                """
                st.button("➡️", key='b2')
            with st.container(border=True):
                """
                RECOMMENDED SEARCH 7
                """
                st.button("➡️", key='b3')
        with col2:
            with st.container(border=True):
                """
                RECOMMENDED SEARCH 2
                """
                st.button("➡️", key='b4')
            with st.container(border=True):   
                """
                RECOMMENDED SEARCH 5
                """
                st.button("➡️", key='b5')
            with st.container(border=True):
                """
                RECOMMENDED SEARCH 8
                """
                st.button("➡️", key='b6')
        with col3:
            with st.container(border=True):
                """
                RECOMMENDED SEARCH 3
                """
                st.button("➡️", key='b7')
            with st.container(border=True):   
                """
                RECOMMENDED SEARCH 6
                """
                st.button("➡️", key='b8')
            with st.container(border=True):
                """
                RECOMMENDED SEARCH 9
                """
                st.button("➡️", key='b9')



#########################################################################
# ▗▄▄▖▗▄▄▄▖▗▄▖▗▄▄▄▖▗▖ ▗▖ ▗▄▄▖
#▐▌     █ ▐▌ ▐▌ █  ▐▌ ▐▌▐▌   
# ▝▀▚▖  █ ▐▛▀▜▌ █  ▐▌ ▐▌ ▝▀▚▖
#▗▄▄▞▘  █ ▐▌ ▐▌ █  ▝▚▄▞▘▗▄▄▞▘
#########################################################################




def show_top_progress_tracker(steps):
    
    last_completed_index = -1

    for i, step in enumerate(steps):
        if st.session_state.get(step["status_key"], False):
            last_completed_index = i

    left_gap, main_content, right_gap = st.columns([1, 6, 1])

    with main_content:
        cols = st.columns(len(steps))

        for i, step in enumerate(steps):
            is_completed = True if st.session_state[step["status_key"]] else False
            in_progress = True if step['running'] and not invalid_question() and not is_completed else False
            pending = True if not is_completed and not in_progress else False
            is_last = True if step['status_key'] == "sql_status" else False

            is_in_progress = (i == last_completed_index) 
            if i+1 == len(steps):
                #is_in_progress = in_progress
                is_in_progress = False


            bg_color_class = "step-completed-bg" if is_completed else "step-incomplete-bg"
            text_color_class = "step-completed-color" if is_completed else "step-incomplete-color"
            line_color_class = "line-completed" if is_completed else "line-incomplete"
            last_step_class = "last-step" if is_last else ""
            in_progress_class = "in-progress" if is_in_progress else ""
            checkmark_html = "<span class='checkmark'>✓</span>" if is_completed else ""

            label_text = step["description"]
            container_classes = f"progress-container {last_step_class} {line_color_class} {in_progress_class}"

            with cols[i]:
                html = f"""
                    <div class="{container_classes}">
                        <div class="progress-bar ">
                            <div class="square {bg_color_class}">{checkmark_html}</div>
                        </div>
                        <p class="progress-text {text_color_class}">{label_text}</p>
                    </div>
                """

                st.html(html)




def show_status_interface():
    import pandas as pd
    
    #st.html(vertical_line_css)
    col1, col2 = st.columns([0.90, 0.10], vertical_alignment="center")
    with col1:
        if invalid_question():
            st.html("<h1 style='z-index:5; position: relative; font-size: border: 0; 1.75rem; margin-bottom: 0; margin-top: 0;'>PROCESS CANCELED: INVALID QUESTION")
        else:
            st.html("<h1 style='z-index:5; position: relative; font-size: border: 0; 1.75rem; margin-bottom: 0; margin-top: 0;'>SQL GENERATION PROGRESS")
    with col2:
        #bake the button red with stylable container
        #button > div > p
        with stylable_container( key="reset_button",
            css_styles="""
                button > div{ 
                    background-color: #FF4248;
                    border: none;
                    color: white;
                    border-radius: 5px;
                    font-size: 10px;
                    padding: 4px; 

                    height: 25px;
                }
                """,
        ):
            if st.button("Reset"):
                delete_process_status(st.session_state.user_name)
    ""
    progress_steps = [
        {"status_key": "user_question_status", "description": "User Question <br><br>", "details": st.session_state.user_question, "running":False},
        {"status_key": "cleaned_question_status", "description": "System's Understanding  <br><br>", "details": st.session_state.cleaned_question, "running" : True if st.session_state.user_question_status and not st.session_state.cleaned_question_status else False},
        {"status_key": "tables_status", "description": "Identifying Relevant Data Sources", "details": st.session_state.tables, "running" : True if st.session_state.cleaned_question_status and not st.session_state.join_status else False
    },
        {"status_key": "join_status", "description": "Joining Data Sources <br><br>", "details": st.session_state.joins, "running": True if st.session_state.cleaned_question_status and not st.session_state.grouping_status else False},
        {"status_key": "grouping_status", "description": "Summarizing Data <br><br>", "details": st.session_state.grouping, "running" : True if st.session_state.join_status and not st.session_state.grouping_status else False},
        {"status_key": "calculations_status", "description": "Defining Metrics <br><br>", "details": st.session_state.calculations, "running" : True if st.session_state.grouping_status and not st.session_state.calculations_status else False},
        {"status_key": "filtering_status", "description": "Filtering the Data <br><br>", "details": st.session_state.filtering, "running" : True if st.session_state.calculations_status and not st.session_state.filtering_status else False},
        {"status_key": "sql_status", "description": "SQL <br><br><br>", "details": st.session_state.sql, "running" : True if st.session_state.filtering_status and not st.session_state.sql_status else False},
    ]
    
    show_top_progress_tracker(progress_steps)

    

    other_css="""
            <style>
            .custom-container {
                display: flex;
                justify-content: left; /* Center horizontally */
                align-items: center;    /* Center vertically */
                 height: 100%;  
                /* border: 2px dashed #007bff; */
                margin-bottom: 10px; 
                gap: 10px; /* Space between flex items */
                position: relative;
            }
            .highlighted-element {
                background-color: #2d82fe;
                color: #fefefe;
                font-family: monospace;
                padding: 0.2em 0.4em;
                border-radius: 3px;
                font-size: 0.9em;
                padding: 2px;
                /* white-space: nowrap; */
            }
            .muted-element {
                color: rgb(200, 200, 200);
            }
            .sql-element{
                color: rgb(200, 200, 200);
                background: #333333;
                border-radius: 5px;

                border-radius: 5px;
               
                padding: 5px;
               

            }
            .inner-done {
                border: 1px solid #2d82fe;
                background: #ffffff;
                /* color: #2d82fe; */
                color: #000000;
                border-radius: 5px;
                padding: 5px;
                font-weight: normal;
                margin-bottom: 20px;
            }
            .inner-running {
                background: #2d82fe;
                border-radius: 5px;
                border: 1px;
                padding: 5px:
                color: #ffffff;
                font-weight: normal;
            }
            . inner-future {
                background: #b4dcff;
                border-radius: 5px;
                border: 1px solid #b4dcff;
                padding: 5px;
                color: #ffffff;
                font-weight: normal;

            }

            /* div[data-testid="stVerticalBlock"] {
                display: flex;
                
                align-items: stretch;
            }
            div[data-testid="stHorizontalBlock"] {
                display: flex;
                
                align-items: stretch;
            }
            div[data-testid="stHorizontalBlock"] > div:first-child {
                flex-grow: 1;
                display: flex;
                flex-direction: columns;
                height: 100%;
            }
            div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
                flex-grow: 1;
                display: flex;
                flex-direction: columns;
                height: 100%
            }
            div[data-testid="stHorizontalBlock"] > div:nth-child(3) {
                flex-grow: 1;
                display: flex;
                flex-direction: columns;
                height: 100%
            }
            div[data-testid="stHorizontalBlock"] > div:nth-child(4) {
                flex-grow: 1;
                display: flex;
                flex-direction: columns;
                height: 100%
            }
            div[data-testid="stHorizontalBlock"] > div:nth-child(5) {
                flex-grow: 1;
                display: flex;
                flex-direction: columns;
                height: 100%;
            }
            div[data-testid="stHtml"] {
                flex-grow: 1;
                display: flex;
                flex-direction: columns;
                height: 100%;
            }
            div[data-testid="stHorizontalBlock"]:has(.timeline-container){}
            .timeline-container {
                position: relative;
                padding-left: 30px;
                padding-right: 15px;
            }
            .timeline-container::before {
                content: '';
                position: absolute;
                left: 15px;
                top: 0;
                bottom: 0;
                width: 3px;
                background-color: #b0c6cf;
                border-radius: 9999px;
                z-index: 0;
            } */

           """

    
   

    for step in progress_steps:
        step_done = True if st.session_state[step["status_key"]] else False
        is_completed = True if st.session_state[step["status_key"]] else False
        in_progress = True if step['running'] and not invalid_question() else False
        pending = True if not is_completed and not in_progress else False

        in_progress_class = "status-in-progress" if in_progress else ""
        completed_class = "status-completed" if is_completed else ""
        pending_class = "status-pending" if pending else ""

        status_text = "Completed" if is_completed else ("In Progess" if in_progress else "Pending")
        status_box_classes = f"status-box {in_progress_class} {completed_class} {pending_class}"

        visability = f"{step['description']}_visbility"
        if visability not in st.session_state.keys():
            st.session_state[visability] = True

       
        col1, col2, col3 = st.columns([0.05, 0.90, 0.05])
                    
        with col2:
            col_a, col_b = st.columns([0.9, 0.10])
            with col_a:
                sub_1, sub_2, sub_3 = st.columns([0.03, 0.3, 0.68])
                with sub_1:
                    val = st.toggle(label=f"{step['description']} toggle", label_visibility="collapsed", value=st.session_state[visability])
                    st.session_state[visability] = val
                with sub_2:
                    st.html(f"<div class = 'description-container'>{step['description'].strip('<br>')}</div>")
            with col_b:
               
                st.html(f"<div class='{status_box_classes}'> {status_text}</div>")

            if st.session_state[visability]:
                details = step['details']
                if details is None or details == "":
                    details = "<br><br>"
                   
                if step["status_key"] == "sql_status":
                    sub_a, sub_b = st.columns([0.96, 0.04])
                    with sub_a:
                        with st.container(border=True):
                            st.code(details, language="sql")
                else:
                    st.html(f"<div class='inner-container'>{details}</div>")

    count = st_autorefresh(interval=5000, limit=1000, key="refreshcounter")

#########################################################################
# ▗▄▄▖▗▄▄▄▖▗▄▖ ▗▄▄▖▗▄▄▄▖
#▐▌     █ ▐▌ ▐▌▐▌ ▐▌ █  
# ▝▀▚▖  █ ▐▛▀▜▌▐▛▀▚▖ █  
#▗▄▄▞▘  █ ▐▌ ▐▌▐▌ ▐▌ █  
#########################################################################


# --- Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="SQL Builder")

if 'user_name' not in st.session_state.keys():
    st.session_state.user_name = "default_user"

NAV_BAR = f"""

<nav class="navbar"  style="  position: relative; width: 100%; z-index: 9999999 !important; margin-left: 0; margin-right: 0; padding: 6px; box-shadow: 0 2px 2px 0 rgba(0,0,0,0.2);">
<span style = "color: #2d82fe; font-size: 30px; font-weight: bold;">RAG-to-SQL App</span>
<span style="float: right; padding: 10px 25px;">({st.session_state.user_name})  {show_img('default-user-icon.jpg')} 
</span>

    """
st.html(NAV_BAR)

load_progress_data()


if 'show_question_interface' not in st.session_state.keys():
    #should never happen
    print("ERROR: show_question_interface: empty")
    st.session_state.show_question_interface = True
    show_question_interface()

if st.session_state.show_question_interface:
    show_question_interface()
else:
    show_status_interface()






