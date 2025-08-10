# File: prompt_tests.py
# Description: systematically test prompts
#  
#
# Copyright (c) 2025 Michael Powers
#
# Usage: Configure 'main' section below with jsonl to your test data
#   
# 
#

from gen_sql import generate_thinking_agent_response
import json
from datasets import Dataset
from datetime import datetime
import time


def run_prompt_tests(test_filename = "./sql_test_set.jsonl", use_gemini=False, use_pro=False):


    jsonl_file = []
    results = []

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    results_filename = f"results_{timestamp_str}"

    with open(test_filename, 'r') as f:
        for line in f:
            jsonl_file.append(json.loads(line.strip()))


    for i, query in enumerate(jsonl_file):
        question = query.get('question')
        instance_id = query.get('instance_id')
        print(f"\n\n!!!Generating results for prompt evaluation: {i+1}/{len(jsonl_file)}\n\n")

        sql = generate_thinking_agent_response(question, user_id="default_user", use_gemini=use_gemini, save_logs=True, test_id=instance_id, use_pro=use_pro)

        # CLEAN?

        results.append({
            "instance_id": instance_id,
            "question": question,
            "answer": sql,
            })

        #save temp results
        filename = f"{i}_temp_results_{timestamp_str}"
        temp_results = Dataset.from_list(results)
        temp_results.save_to_disk(filename)
        print(f"Temp results saved as : {filename}")

        # deal with rate limits
        if use_gemini:
            print("Waiting one min for rate limits.")
            time.sleep(60)
            

    # SAVE RESULTS
    results_dataset = Dataset.from_list(results)
    results_dataset.save_to_disk(results_filename)
    print(f"Results saved as: {results_filename}")


    print("\n\n ------- DONE RUN PROMPT TEST ------------")


def run_prompt_model_tests(test_filename = "./sql_test_set.jsonl"):


    jsonl_file = []
    results = []

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    results_filename = f"results_{timestamp_str}"

    with open(test_filename, 'r') as f:
        for line in f:
            jsonl_file.append(json.loads(line.strip()))


    for i, query in enumerate(jsonl_file):
        question = query.get('question')
        instance_id = query.get('instance_id')
        print(f"\n\n!!!Generating results for model evaluation for each prompt : {i+1}/{len(jsonl_file)}\n\n")

        #model_list = ["Gemini", "Gemini", "Gemini, "Gemini"]
        #for y in range(0,3):
        # for item in ["my-phi4:latest", "llama3.1:8b"]:
        #.  model_list[y] = item
       

        #sql = generate_thinking_agent_response(question, user_id="default_user", use_gemini=True, save_logs=True, test_id=instance_id, use_pro=False, model_list=model_list)

        # CLEAN?

        results.append({
            "instance_id": instance_id,
            "question": question,
            "answer": sql,
            })

        #save temp results
        filename = f"{i}_temp_results_{timestamp_str}"
        temp_results = Dataset.from_list(results)
        temp_results.save_to_disk(filename)
        print(f"Temp results saved as : {filename}")

        # deal with rate limits
        if use_gemini:
            time.sleep(60)
            print("\n\n!!!!! Waiting one min for rate limits.")

    # SAVE RESULTS
    results_dataset = Dataset.from_list(results)
    results_dataset.save_to_disk(results_filename)
    print(f"Results saved as: {results_filename}")


    print("\n\n ------- DONE RUN PROMPT TEST ------------")


if __name__ == "__main__":
    run_prompt_tests("../sql_test_set.jsonl", True,False)