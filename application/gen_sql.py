# File: gen_sql.py
# Description: this is the agent
#  
#
# Copyright (c) 2025 Michael Powers
#
# Usage: to be used with streamlit app, not run directly
#   
# 
#
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import chromadb
from llama_index.core import VectorStoreIndex, QueryBundle
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.schema import NodeWithScore
from internal_db import update_process_status, delete_process_status
from typing import List
import sys
from datetime import datetime
import json
import re




#########################################################################
# ▗▄▄▖ ▗▄▖ ▗▖  ▗▖▗▄▄▄▖▗▄▄▄▖ ▗▄▄▖
#▐▌   ▐▌ ▐▌▐▛▚▖▐▌▐▌     █  ▐▌   
#▐▌   ▐▌ ▐▌▐▌ ▝▜▌▐▛▀▀▘  █  ▐▌▝▜▌
#▝▚▄▄▖▝▚▄▞▘▐▌  ▐▌▐▌   ▗▄█▄▖▝▚▄▞▘
#########################################################################
from injest import get_vector_storage_index, CHROMA_DB_PATH, SCHEMA_COLLECTION_NAME, BUSINESS_TERMS_COLLECTION_NAME
from prompts import CLEAN_QUESTION_PROMPT_V4, SQL_GEN_PROMPT_TEMPLATE, CLEAN_SQL_PROMPT_V4, FILTERING_PROMPT_V3, CALCULATIONS_PROMPT_V3, GROUPING_PROMPT_V3, TABLE_COLUMN_PROMPT_V4, SQL_GEN_PROMPT_TEMPLATE_V4, JOIN_PROMPT_V4

GEMINI_API_KEY = "YOUR_API_KEY_OR_OS_VARIABLE"
GEMINI_PRO_MODEL = "gemini-2.5-pro"
GEMINI_MODEL = 'gemini-2.5-flash-lite-preview-06-17'
OLLAMA_MODEL = "my-phi4:latest" #"llama3.1:8b" 
#RERANK_MODEL = "BAAI/bge-reranker-base" 
RERANK_MODEL = None
MIN_RELEVANCE_SCORE = 0.0005

USE_GEMINI = False



def get_llm(model_name = OLLAMA_MODEL, json_mode=False, output_cls = None):

    if output_cls is None:
        llm = Ollama(model=model_name, request_timeout=720, temperature=0.0, json_mode=json_mode)
    else:
        llm = Ollama(model=model_name, request_timeout=720, temperature=0.0, json_mode=json_mode, output_cls=output_cls)
    return llm

def set_reranker():
    try:
        reranker = SentenceTransformerRerank(
            model=RERANK_MODEL,
            top_n=5 # Keep top 5 after reranking
        )
        print(f"Successfully loaded reranker model: {RERANK_MODEL}")
    except Exception as e:
        print(f"Could not load reranker model ({RERANK_MODEL}). Retrieval quality might be lower. Error: {e}")
        reranker = None # Set to None if loading fails
    return reranker

reranker = None

#########################################################################
#▗▄▄▖  ▗▄▖  ▗▄▄▖
#▐▌ ▐▌▐▌ ▐▌▐▌   
#▐▛▀▚▖▐▛▀▜▌▐▌▝▜▌
#▐▌ ▐▌▐▌ ▐▌▝▚▄▞▘             
#########################################################################
def get_rag_context(user_question: str) -> tuple[str, str, List[NodeWithScore], List[NodeWithScore]]:
    """
    Retrieves context from both schema and business terms collections.
    Returns schema_context_str, business_terms_context_str, schema_nodes, business_terms_nodes.
    The nodes are returned for potential re-use in the SQL cleaning step.
    """

    print("About to retrieve context from schema collection...")

    schema_index = get_vector_storage_index(SCHEMA_COLLECTION_NAME)
    schema_retriever = VectorIndexRetriever(
        index=schema_index,
        similarity_top_k=7, # Retrieve more to allow reranker to work
    )
    schema_nodes = schema_retriever.retrieve(QueryBundle(user_question))

    

    ###########
    print(f"\nInitial retrieved schema nodes (before reranking, top {len(schema_nodes)}):")
    for i, node_with_score in enumerate(schema_nodes):
        print(f"  Node {i+1} (Original Similarity Score: {node_with_score.score:.4f}): {node_with_score.text[:10]}...")
    print("-" * 30)
    ##########



    if reranker:
        reranked_nodes = reranker.postprocess_nodes(schema_nodes, query_bundle=QueryBundle(user_question))

        for i, node_with_score in enumerate(reranked_nodes):
            score_to_print = node_with_score.score # Fallback to initial score if reranker didn't add 'relevance_score'

            print(f"Node {i+1} (Reranked Raw Score: {score_to_print:.4f}): Content: {node_with_score.text[:10]}...") 



        filtered_schema_nodes = [
            node_with_score
            for node_with_score in reranked_nodes
            if node_with_score.score >= MIN_RELEVANCE_SCORE
            #if hasattr(node_with_score, 'relevance_score') and node_with_score.score is not None and node_with_score.score >= MIN_RELEVANCE_SCORE
        ]
        schema_nodes = filtered_schema_nodes

        print(f"Reranked schema nodes. Top {len(schema_nodes)} selected.")
    else:
        print(f"Retrieved top {len(schema_nodes)} schema nodes (no reranker).")

    schema_context = "\n\n".join([n.text for n in schema_nodes])
    if not schema_context.strip():
        print("No relevant schema context found.")
        schema_context = "No database schema information found."


    # Retrieve context from Business Terms Collection
    print("Retrieving context from business terms collection...")
    business_terms_index = get_vector_storage_index(BUSINESS_TERMS_COLLECTION_NAME)
    business_terms_retriever = VectorIndexRetriever(
        index=business_terms_index,
        similarity_top_k=7, # Retrieve more to allow reranker to work
    )
    business_terms_nodes = business_terms_retriever.retrieve(QueryBundle(user_question))

    if reranker:
        reranked_nodes = reranker.postprocess_nodes(business_terms_nodes, query_bundle=QueryBundle(user_question))
        
        filtered_business_terms_nodes = [
            node_with_score
            for node_with_score in reranked_nodes
            if node_with_score.score >= MIN_RELEVANCE_SCORE
            #if hasattr(node_with_score, 'relevance_score') and node_with_score.score is not None and node_with_score.score >= MIN_RELEVANCE_SCORE
        ]
        business_terms_nodes = filtered_business_terms_nodes
        print(f"Reranked & filtered business terms nodes. Top {len(business_terms_nodes)} selected.")
    else:
        print(f"Retrieved top {len(business_terms_nodes)} business terms nodes (no reranker).")

    business_terms_context = "\n\n".join([n.text for n in business_terms_nodes])
    if not business_terms_context.strip():
        print("No relevant business terms context found.")
        business_terms_context = "No specific business terms or definitions found."
        
    return schema_context, business_terms_context, schema_nodes, business_terms_nodes



#########################################################################
#▗▖ ▗▖▗▄▄▄▖▗▖   ▗▄▄▖ ▗▄▄▄▖▗▄▄▖ 
#▐▌ ▐▌▐▌   ▐▌   ▐▌ ▐▌▐▌   ▐▌ ▐▌
#▐▛▀▜▌▐▛▀▀▘▐▌   ▐▛▀▘ ▐▛▀▀▘▐▛▀▚▖
#▐▌ ▐▌▐▙▄▄▖▐▙▄▄▖▐▌   ▐▙▄▄▖▐▌ ▐▌
#########################################################################
def clean_response(response):
    response = response.strip()
    if response.startswith("```json") and response.endswith("```"):
        response = response[len("```json"): -len("```")].strip()
    elif response.startswith("```") and response.endswith("```"):
        response = response[len("```"): -len("```")].strip()

    return response


def strip_key_from_json(data, key_to_strip='reasoning'):
    if isinstance(data, dict) and key_to_strip in data:
        del data[key_to_strip]
    return data


def ask_gemini_json(prompt, use_json=True, model='models/gemini-2.0-flash-lite'):
    import os
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(model)
    if use_json:
        generation_config = genai.GenerationConfig(response_mime_type="application/json")
        response = model.generate_content(prompt, generation_config=generation_config)
    else:
        response = model.generate_content(prompt)
    return response.text

def get_llm_response(prompt, model_name=OLLAMA_MODEL, json_mode=False):
    try:
        if USE_GEMINI:
            response = ask_gemini_json(prompt, use_json=json_mode, model=GEMINI_MODEL)
            cleaned = clean_response(response)
        else:
            llm = get_llm(model_name, json_mode=json_mode)
            response = llm.complete(prompt)
            cleaned = clean_response(str(response))
        print(f"Response: '{cleaned}'")
        return cleaned
    except Exception as e:
        print(f"Error with LLM response: {e}")
        return ""


def clean_user_question(original_question: str) -> str:
    """
    Uses an LLM to rephrase and clarify the user's question.
    """
    print(f"Cleaning user question: '{original_question}'")
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = CLEAN_QUESTION_PROMPT_V4.format(original_question=original_question, current_date=current_date)
    
    response = get_llm_response(prompt, OLLAMA_MODEL, True)

    try:
        info_json = json.loads(response)
        return info_json
    except Exception as e:
        return None


def generate_sql_query(query_str: str, schema_context: str, business_terms_context: str) -> str:
    """
    Generates a SQL query using the LLM based on the cleaned question and RAG context.
    """
    print(f"Generating SQL for cleaned question: '{query_str}'")

    full_prompt = SQL_GEN_PROMPT_TEMPLATE.format(
        schema_context=schema_context,
        business_terms_context=business_terms_context,
        query_str=query_str
    )

    print(f"Full prompt for SQL generation LLM:\n{full_prompt}")

    return get_llm_response(full_prompt)


def clean_generated_sql(generated_sql: str, schema_nodes: List[NodeWithScore], business_terms_nodes: List[NodeWithScore]) -> str:
    """
    Uses an LLM to review and clean the generated SQL query.
    """
    if not generated_sql.strip():
        return "" # No SQL to clean

    #print(f"Cleaning generated SQL: '{generated_sql}'")

    # Reconstruct contexts from the nodes for the SQL cleaning prompt
    schema_context_for_cleaning = "\n\n".join([n.text for n in schema_nodes])
    business_terms_context_for_cleaning = "\n\n".join([n.text for n in business_terms_nodes])

    prompt = CLEAN_SQL_PROMPT_V4.format(
        schema_context=schema_context_for_cleaning,
        business_terms_context=business_terms_context_for_cleaning,
        generated_sql=generated_sql
    )

    #print(f"Full prompt for SQL cleaning LLM:\n{prompt}")

    response = get_llm_response(prompt)
    if response == "":
        print("error cleaning sql")
        return generated_sql

    return response



def get_value_alt(data, key1, key2):
    try:
        value = data.get(key1)
        return data.get(key2) if value is None else value
    except Exception as e:
        print(f"Couldn't fix malformed json: {e}")
        return None


def get_thinking_step_response(prompt, key, alt_key, model_name=OLLAMA_MODEL):
    response = get_llm_response(prompt, model_name=model_name, json_mode=True)

    try:
        info_json = json.loads(response)


        # Lets try to clean up incorrect json schema adherence 
        info_json[key] = get_value_alt(info_json, key, alt_key)
        info_json['reasoning'] = get_value_alt(info_json, 'reasoning', 'reason')
       
        return info_json

    except json.JSONDecodeError:
        print(f"LLM failed to output valid JSON : {response}")
        return None

#########################################################################
#▗▄▄▄  ▗▄▖     ▗▄▄▄▖▗▄▄▄▖    ▗▄▄▄▖▗▄▖     ▗▄▄▄▖▗▄▄▄▖
#▐▌  █▐▌ ▐▌      █    █        █ ▐▌ ▐▌      █    █  
#▐▌  █▐▌ ▐▌      █    █        █ ▐▌ ▐▌      █    █  
#▐▙▄▄▀▝▚▄▞▘    ▗▄█▄▖  █        █ ▝▚▄▞▘    ▗▄█▄▖  █ 
#########################################################################


def get_model_for_step(step, model_list):
    global USE_GEMINI

    if model_list is None:
        return OLLAMA_MODEL

    value = model_list[step]

    if  value == 'Gemini':
        USE_GEMINI = True
        return "Gemini"
    else:
        USE_GEMINI = False
        return value



#
#
# 
#
#

def generate_thinking_agent_response(user_question: str, user_id: str = "default_user", use_gemini: bool = False, save_logs=False, test_id=None, use_pro=False, model_list = None) -> str: 
    global reranker, USE_GEMINI, GEMINI_MODEL

    USE_GEMINI = use_gemini

    TABLE_PROMPT_VER = "V4"
    GROUPING_PROMPT_VER = "V4"
    CALCULATIONS_PROMPT_VER = "V3"
    FILTERING_PROMPT_VER = "V3"
    JOIN_PROMPT_VER = "V4"

    COMPLICATED_CALLS = False


    if model_list is not None:
        COMPLICATED_CALLS = True

    print("\n\n------------------------------------")
    if use_pro:
        GEMINI_MODEL = GEMINI_PRO_MODEL
        print("Using Gemini Pro")
    elif use_gemini:
        print("Using Gemini Flash")

    
    #reset status for user
    delete_process_status(user_id)

    update_process_status(user_id, {'user_question': user_question})

    reranker = set_reranker()

    print("\n--- Step 1: cleaning user question ---")
    cleaned_question_info = clean_user_question(user_question)

    cancel_process = get_value_alt(cleaned_question_info, 'cancel_process', 'cancel')
    if cancel_process:
        print('\n\nLLM DETERMINED INVALID QUESTION: CANCEL PROCESS')
        return

    cleaned_question = cleaned_question_info.get('rephrased_question')

    if not cleaned_question:
        #print("Clean question prompt did not return valid 'rephrased_question'")
        cleaned_question = cleaned_question_info.get('rephrased')
        if not cleaned_question:
            cleaned_question = cleaned_question_info.get('rephr_question')
            if not cleaned_question:
                print("Clean question prompt did not return a valid response.")
                cleaned_question = user_question

    cleaned_question_info['rephrased_question'] = cleaned_question
    update_process_status(user_id, {'cleaned_question': json.dumps(cleaned_question_info)})

    print("\n--- Step 2: RAG CALL ---")
    schema_context_str, business_terms_context_str, schema_nodes, business_terms_nodes = get_rag_context(cleaned_question)

    #tables and columns
    print("\n--- Step 3: Determining Tables and Columns ---")
    tables_prompt = TABLE_COLUMN_PROMPT_V4.format(
        schema_context=schema_context_str,
        query_str=cleaned_question
    )
    #print(f'\n --- DEBUG TABLES PROMPT:\n\n{tables_prompt}\n---------------------\n')

    model = get_model_for_step(0,model_list)
    tables_and_columns = get_thinking_step_response(tables_prompt, 'tables', 'table', model_name=model)

    update_process_status(user_id, {'tables': json.dumps(tables_and_columns)})

   
    # Determine Joins
    print("\n--- Step 4: Determining Joins ---")
    join_prompt = JOIN_PROMPT_V4.format(
        schema_context=schema_context_str,
        query_str=cleaned_question,
        identified_tables_columns_json=json.dumps(strip_key_from_json(tables_and_columns))
    )
    model = get_model_for_step(1,model_list)
    join_info =get_thinking_step_response(join_prompt, "joins","join", model_name=model)
    update_process_status(user_id, {'joins': json.dumps(join_info)})

    # Determine Grouping
    print("\n--- Step 5: Determining Grouping ---")
    group_prompt = GROUPING_PROMPT_V3.format(
        schema_context=schema_context_str,
        business_terms_context=business_terms_context_str,
        query_str=cleaned_question,
        identified_tables_columns_json=json.dumps(strip_key_from_json(tables_and_columns))
    )

    model = get_model_for_step(2,model_list)

    grouping_info = get_thinking_step_response(group_prompt, "group_by_columns", 'group_by', model_name = model)
    aggregate_info = get_value_alt(grouping_info, 'aggregations', 'aggregation')
    #complex_aggregate_info =get_value_alt(grouping_info, "complex_aggregations", "complex_aggregation")
    complex_aggregate_info =""

    update_process_status(user_id, {'grouping': json.dumps(grouping_info)})


    # Determine Calculations
    print("\n--- Step 6: Determining Calculations ---")
    calculations_prompt = CALCULATIONS_PROMPT_V3.format(
        schema_context=schema_context_str,
        business_terms_context=business_terms_context_str,
        query_str=cleaned_question,
        aggregate_info=aggregate_info,
        identified_tables_columns_json=json.dumps(strip_key_from_json(tables_and_columns))
    )

    model = get_model_for_step(3,model_list)
    calculations_info = get_thinking_step_response(calculations_prompt, "calculations", 'calculation', model_name = model)

    update_process_status(user_id, {'calculations': json.dumps(calculations_info)})


    # Determine Filtering
    print("\n--- Step 7: Determining Filtering ---")
    filtering_prompt = FILTERING_PROMPT_V3.format(
        schema_context=schema_context_str,
        business_terms_context=business_terms_context_str,
        query_str=cleaned_question,
        aggregate_info=aggregate_info,
        identified_tables_columns_json=json.dumps(strip_key_from_json(tables_and_columns))
    )

    model = get_model_for_step(4,model_list)
    filtering_info = get_thinking_step_response(filtering_prompt, "filters", 'filtering', model_name=model)

    update_process_status(user_id, {'filtering': json.dumps(filtering_info)})
    
    print("\n--- Step 8: SQL Generation ---")
    # Final SQL Generation prompt would then consolidate all these decisions
    final_sql_gen_prompt = SQL_GEN_PROMPT_TEMPLATE_V4.format( 
        schema_context=schema_context_str,
        business_terms_context=business_terms_context_str,
        original_question=cleaned_question,
        identified_tables_columns=json.dumps(strip_key_from_json(tables_and_columns)),
        grouping_details=json.dumps(grouping_info),
        calculation_details=json.dumps(calculations_info),
        filtering_details=json.dumps(filtering_info),
        aggregate_info=aggregate_info,
        complex_aggregate_info=complex_aggregate_info,
        join_info=json.dumps(join_info),
        )

    raw_sql = get_llm_response(final_sql_gen_prompt)
        
    if not raw_sql:
        print("Error: could not generate SQL for that question.")
        return "\nCould not generate a SQL query for that question based on the available context."
    
    print("\n--- Step 9: CLEANED SQL  ---")
    final_sql = clean_generated_sql(raw_sql, schema_nodes, business_terms_nodes)

    update_process_status(user_id, {'sql': final_sql})


    if save_logs:
        log_response_json = {
            "ID":test_id,
            "table prompt ver": TABLE_PROMPT_VER,
            "table prompt result": json.dumps(tables_and_columns),
            "grouping prompt ver": GROUPING_PROMPT_VER,
            "grouping prompt result": json.dumps(grouping_info),
            "calculations prompt ver": CALCULATIONS_PROMPT_VER,
            "calculations prompt result": json.dumps(calculations_info),
            "filtering prompt ver": FILTERING_PROMPT_VER,
            "filtering prompt result": json.dumps(filtering_info),
            "join prompt ver": JOIN_PROMPT_VER,
            "join prompt result": json.dumps(join_info),
        }
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d_%H-%M")
        filename = f"./prompt_logs/prompt_log_{timestamp_str}.json"
        with open(filename, 'w') as f:
            json.dump(log_response_json, f, indent=4)
        print(f'Prompt Logs saved to: {filename}')


    if final_sql:
        return final_sql
    else:
        return f"\nFailed to clean SQL, or the generated SQL was invalid. Original generated SQL:\n{raw_sql}"

def generate_agent_response(user_question: str) -> str: 
    cleaned_question = clean_user_question(user_question)
    if not cleaned_question:
        print('Warning: failed to clean the uesr question!')
        cleaned_question = user_question

    schema_context, business_terms_context, schema_nodes, business_terms_nodes = get_rag_context(cleaned_question)
    raw_sql = generate_sql_query(cleaned_question, schema_context, business_terms_context)
        
    if not raw_sql:
        print("Error: could not generate SQL for that question.")
        return "\nCould not generate a SQL query for that question based on the available context."
    
    final_sql = clean_generated_sql(raw_sql, schema_nodes, business_terms_nodes)


    

    if final_sql:
        return final_sql
    else:
        return f"\nFailed to clean SQL, or the generated SQL was invalid. Original generated SQL:\n{raw_sql}"


#########################################################################
#▗▄▄▄▖▗▄▄▄▖ ▗▄▄▖▗▄▄▄▖
#  █  ▐▌   ▐▌     █  
#  █  ▐▛▀▀▘ ▝▀▚▖  █  
#  █  ▐▙▄▄▖▗▄▄▞▘  █  
#########################################################################




if __name__ == "__main__":
    print("Welcome to the RAG to SQL Agent!")
    print("Type your question and press Enter. Type 'exit' to quit.")

    while True:
        question = input("\nYour question: ")
        if question.lower() == 'exit':
            break

        if not question.strip():
            print("Please enter a question.")
            continue

        sql_result = generate_thinking_agent_response(question)
        if sql_result:
            print(f"\nGenerated SQL:\n{sql_result}")
        else:
            print("\nCould not generate a SQL query for that question based on the available context.")