from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import json
import os
from gemini_multiagent_framework import GeminiAgent
from openai_multiagent_framework import OpenAIAgent
from datasets import load_dataset
import pandas as pd
import re
import math

def instantiate_agents_gpt(model="gpt-4o-mini"):
    prompt_builder = OpenAIAgent(
                name="Prompt Builder",
                system_instruction="Build a prompt for the problem provided."
                "The prompt should be clear and concise, and should be able to generate the code for the problem.",
                model=model
                )
    code_writer = OpenAIAgent(
                name="Code Writer",
                system_instruction="You are a programmer and you solve python coding problems.",
                model=model
                )
    test_writer = OpenAIAgent(
                name="Test Writer",
                system_instruction="You are a test designer and are good at providing test cases for python coding problems."
                "In some cases it might be asked you to correct tests that you previously generated if they are wrong.",
                model=model
                )
    return prompt_builder, code_writer, test_writer


def instantiate_agents_gemini():
    prompt_builder = GeminiAgent(
                name="Prompt Builder",
                system_instruction="Build a prompt for the problem provided."
                "The prompt should be clear and concise, and should be able to generate the code for the problem.",
                )
    code_writer = GeminiAgent(
                name="Code Writer",
                system_instruction="Write the code for the problem provided and return just the full code."
                "If it is told you what you are doing is wrong, try to fix it and rewrite the code again fixing the errors."
                "Do not explain nothing about the code, just return the full code.",
                )
    test_writer = GeminiAgent(
                name="Test Writer",
                system_instruction="Write 5 tests for the code that is provided."
                "The tests should cover the main cases and should be able to test the code."
                "Return the tests in a list format.",
                )
    return prompt_builder, code_writer, test_writer

def log_file(text, filename):
    with open(filename, "a") as log_open:
        log_open.write(text + "\n")
    
def build_prompt(entry, prompt_builder, prompt_path = "./prompts_v1/promptbuilder_code.md"):
    
    with open(prompt_path, "r") as f:
        code_writer_prompt = f.read()
    requirement = entry["prompt"]
    
    prompt = f"""
{code_writer_prompt}
```python
{requirement}
```
"""
    res = prompt_builder.process_message(message=prompt)
    entry["prompt_built"] = res
    log_file("-" * 20 + "[PROMPT]"+ "-" * 20 + "\n" +res, "log.txt") # DEBUG
    return entry

def extract_code(text):
    if f"```python" in text:
        text = text[text.find(f"```python")+len(f"```python"):]
        text = text[:text.find("```")]
    else:
        print("Error: No code block found")
    return text

def generate_code(entry, code_writer):
    prompt = entry["prompt_built"]
    res = code_writer.process_message(message=prompt)
    code = extract_code(res) 
    entry["generated_code"] = code
    log_file("-" * 20 + "[CODE WRITER PROMPT]"+ "-" * 20 + "\n"+prompt, "log.txt") # DEBUG
    log_file("-" * 20 + "[CODE WRITER RESPONSE]"+ "-" * 20 + "\n"+res, "log.txt") # DEBUG
    return entry


def generate_tests(entry, test_writer, prompt_path = "./prompts_v1/testwriter_code.md", different_test_writer=None):
    with open(prompt_path, "r") as f:
        test_writer_prompt = f.read()
    requirement = entry["prompt"]
    prompt = f"""
{test_writer_prompt}
```python
{requirement}
```
"""
    if different_test_writer is not None:
        res = different_test_writer.process_message(message=prompt)
    else:
        res = test_writer.process_message(message=prompt)
        
    tests = extract_code(res) 
    tests = tests.split("\n")
    # Filter out empty strings
    tests = [test for test in tests if test]
    entry["generated_tests"] = tests
    log_file("-" * 20 + "[TESTS WRITER PROMPT]"+ "-" * 20 + "\n"+ prompt, "log.txt") # DEBUG
    log_file("-" * 20 + "[TESTS WRITER RESPONSE]"+ "-" * 20 + "\n"+ res, "log.txt") # DEBUG
    return entry

def validate_code(entry, code_writer, max_attempts=3):
    code = entry["generated_code"]
    out = ""
    counter = max_attempts

    while counter > 0:
        try:
            exec(code, {"math": math})
            log_file("-" * 20 + "[VALIDATION]: Code is valid", "log.txt") # DEBUG
            break
        except Exception as e:
            s = str(e)
            out = f"ERROR: {s}"
            prompt = f"""
The following code cannot be executed. Please fix the code without changing the logic.
```python
{code}
```
{out}

"""
            res = code_writer.process_message(message=prompt)
            code = extract_code(res) # REVISE
            counter -= 1
            log_file("-" * 20 + "[VALIDATION]\n"+out, "log.txt") # DEBUG
    
    entry["generated_code"] = code
    return entry

# 1) EACH TIME ALL THE TESTS ARE RUN
# 2) TEST REGENERATION SINCE ITERATION 0
# NEW) KEEP TRACK OF THE CODE SOLUTIONS OF EACH ITERATION (OR MAKE IT GENERATE MANY CODE SOLUTIONS FROM THE BEGINNING)
def iterate_tests(entry, code_writer, max_attempts=3,
                  prompt_path = "./prompts_v1/codewriter_fix.md", test_writer=None, test_regeneration = False, 
                  intermediate_results=False, reg_prompt_path = "./prompts_v2/testwriter_fix.md", mbpp = False):
    code = entry["generated_code"]
    tests = entry["generated_tests"]
    counter = max_attempts
    idx_passed_tests = {idx: False for idx in range(len(tests))}  # Initialize as dict
    iteration = 0
    # Load prompt
    with open(prompt_path, "r") as f:
        codewriter_fix = f.read()
        
    if test_regeneration:
        with open(reg_prompt_path, "r") as f:
            test_regeneration_prompt = f.read()
    
    if intermediate_results:
        if mbpp:
            entry = check_solution_intermediate_results_mbpp(entry, code, iteration)
        else:
            entry = check_solution_intermediate_results(entry, code, iteration)
  
    while counter > 0:
        error_list = []
    # ----- START OF WHILE LOOP --------------------------------------------------------------------------------------------------
        for idx, test in enumerate(tests):
        # ----- START OF FOR LOOP (execution and collection of results)------------------------------------------------------------
        #   if idx_passed_tests[idx]:  # Check if test has passed
        #       continue
            try:
                code_to_exec = code + "\n" + test
                log_file("-" * 20 + "[TEST " + str(idx) + "]"+ "-" * 20 + "\n"+code_to_exec, "log.txt") # DEBUG
                exec(code_to_exec, {"math": math})
                idx_passed_tests[idx] = True  # Mark test as passed
                
                log_file("-" * 20 + "[TEST PASSED]\n", "log.txt") # DEBUG
            except Exception as e:
                s = str(e)
                error_list.append(f"{s} \n")
                log_file("-" * 20 + "[ERROR]\n"+s, "log.txt") # DEBUG
        # ----- END OF FOR LOOP -------------------------------------------------------------------------------------------
        
        if all(idx_passed_tests.values()):
            log_file("-" * 20 + "ALL PASSED, BREAK THE WHILE LOOP" + "-" * 20, "log.txt")# DEBUG!
            break # Break if all tests passed
        
        else: # if some tests didn't pass
            # Filter tests to include only those that haven't passed
            non_passed_tests = [tests[i] for i, passed in idx_passed_tests.items() if not passed]
            non_passed_tests_string = "\n".join(non_passed_tests)
            
            # regenerate failed tests in even iterations (every two iterations)
            if ((test_regeneration) and ((max_attempts - counter)%2 == 0)):# and (max_attempts != counter) :
                requirement = entry["prompt"]
                if mbpp:
                    prompt = f"""
{test_regeneration_prompt}
{requirement}
Signature of the function: {extract_signature(entry["code"])}
```python
{non_passed_tests_string}
```
"""
                else:
                    prompt = f"""
{test_regeneration_prompt}
```python
{requirement}
{non_passed_tests_string}
```
"""
     
                res = test_writer.process_message(message=prompt)
                log_file("-" * 20 + "[TEST REGENERATOR PROMPT]\n"+prompt, "log.txt") # DEBUG
                log_file("-" * 20 + "[TEST REGENERATOR RESPONSE]\n"+res, "log.txt") # DEBUG
                regenerated_tests = extract_code(res)
                log_file("-" * 20 + "[REGENERATED TESTS LIST]\n"+regenerated_tests, "log.txt") # DEBUG
                regenerated_tests = regenerated_tests.split("\n")
                # Filter out empty strings
                regenerated_tests = [test for test in regenerated_tests if test]
                # substitute the failed tests with the regenerated tests
                for idx, test in enumerate(tests):
                    if not idx_passed_tests[idx]:
                        if regenerated_tests:
                            tests[idx] = regenerated_tests.pop(0)
                        else:
                            break
                entry["generated_tests"] = tests # update tests
                
                # add an entry that keeps track of how many of the regenerated tests are accurate
                
                
                log_file("-" * 20 + "[UPDATED TESTS LIST]\n"+ "\n".join(entry["generated_tests"]), "log.txt") # DEBUG
            # regenerate the code (always if test_regeneration is False) when we are in the first or an odd iteration    
            else:
            # IMPORTANT: ADD MBPP VERSION
                requirement = entry["prompt"]
                if mbpp:
                    prompt = f"""
{codewriter_fix}
Original problem:
{requirement}
Proposed solution:
```python
{code}
```
Tests failed by the proposed solution:
```python
{non_passed_tests_string}
Errors:
{error_list}
```
"""
                else:
                    prompt = f"""
{codewriter_fix}
Original problem:
```python
{requirement}
```
Proposed solution:
```python
{code}
```
Tests failed by the proposed solution:
```python
{non_passed_tests_string}
```
"""
                    
                res = code_writer.process_message(message=prompt)
                code = extract_code(res)
                log_file("-" * 20 + "[CODE REGENERATOR PROMPT]\n"+ "-"*20 + "\n" + prompt, "log.txt") # DEBUG
                log_file("-" * 20 + "[CODE REGENERATOR RESPONSE]\n"+res, "log.txt") # DEBUG
            
        
                if intermediate_results:
                # CHECK INTERMEDIATE RESULTS ONLY IF THE CODE IS REGENERATED
                    iteration += 1
                    if mbpp:
                        entry = check_solution_intermediate_results_mbpp(entry, code, iteration)
                    else:
                        entry = check_solution_intermediate_results(entry, code, iteration)
        
        counter -= 1
            
    # ----- END OF WHILE LOOP -----------------------------------------------------------------------------------------
        
    # after optimization loop (final solution)
    passed_tests = [test for i, test in enumerate(tests) if idx_passed_tests[i]]
    entry["generated_code"] = code
    entry["validated_tests"] = passed_tests
    return entry





def generate_report(entry):
    tests = entry["generated_tests"]
    validated_tests = entry["validated_tests"]
    solution_valid = entry["solution_valid"]
        # Calculate the number of tests passed
    num_tests = len(tests)
    num_passed_tests = len(validated_tests)
    num_failed_tests = num_tests - num_passed_tests
    
    # Calculate the percentage of tests passed
    percentage_passed = num_passed_tests / num_tests * 100
# Generate the report
    report = f"""
Report:
- Total tests: {num_tests}
- Passed tests: {num_passed_tests}
- Failed tests: {num_failed_tests}
- Percentage passed: {percentage_passed}%

Solution is valid: {solution_valid}
"""
    entry["report"] = report
    return entry

def is_test_valid(entry_point, code, test):
    try:
        exec(code + "\n" + test + "\n" + "check(" + entry_point + ")" + "\n", {"math": math})
        return True
    except Exception:
        return False


def extract_check_function(test_str):
    # Use regular expression to find the check function within the string
    match = re.search(r'def check\(.*?\):.*?assert.*', test_str, re.DOTALL)
    if match:
        return match.group(0)
    else:
        return None

def check_solution(entry):
    code = entry["generated_code"]
    test_function = extract_check_function(entry["test"])
    valid = is_test_valid(entry["entry_point"], code, test_function)
    entry["solution_valid"] = valid
    return entry

def check_solution_intermediate_results(entry, code, iteration):
    # returns a boolean instead of updating the entry
    to_execute = create_function_definition(entry)
    count, total = test_accuracy(entry, to_execute)
    test_count = f"test_count_{iteration}"
    test_total = f"test_total_{iteration}"
    entry[test_count] = count
    entry[test_total] = total
    test_function = extract_check_function(entry["test"])
    valid_key = f"valid_{iteration}"
    valid = is_test_valid(entry["entry_point"], code, test_function)
    entry[valid_key] = valid
    return entry




# Function to divide dataset into chunks of size n
def chunk_dataset(data, n):
    for i in range(0, len(data), n):
        yield data[i:i + n]



def extract_signature(func_str):
    # Use regex to find the function signature
    match = re.search(r'def\s+(\w+\([^)]*\))', func_str)
    if match:
        return match.group(1)
    return ""

def build_prompt_mbpp(entry, prompt_builder, prompt_path = "./prompts_v1/promptbuilder_mbpp.md"):
    
    with open(prompt_path, "r") as f:
        code_writer_prompt = f.read()
    requirement = entry["prompt"]
    
    prompt = f"""
{code_writer_prompt}
{requirement}
Signature of the function: {extract_signature(entry["code"])}
"""
    res = prompt_builder.process_message(message=prompt)
    entry["prompt_built"] = res
    log_file("-" * 20 + "[PROMPT]"+ "-" * 20 + "\n" +res, "log.txt") # DEBUG
    return entry


def generate_tests_mbpp(entry, test_writer, prompt_path = "./prompts_v1/testwriter_mbpp_prompt.md", different_test_writer=None):
    with open(prompt_path, "r") as f:
        test_writer_prompt = f.read()
    requirement = entry["prompt"]
    prompt = f"""
{test_writer_prompt}
{requirement}
Signature of the function: {extract_signature(entry["code"])}
"""
    if different_test_writer is not None:
        res = different_test_writer.process_message(message=prompt)
    else:
        res = test_writer.process_message(message=prompt)
    tests = extract_code(res) # REVISE
    tests = tests.split("\n")
    # Filter out empty strings
    tests = [test for test in tests if test]
    entry["generated_tests"] = tests
    log_file("-" * 20 + "[TESTS]"+ "-" * 20 + "\n"+ "\n".join(tests), "log.txt") # DEBUG
    return entry


def is_test_valid_mbpp(code, tests):
    try:
        for test in tests:
            exec(code + "\n" + test + "\n", {"math": math})
        return True
    except Exception:
        return False


def check_solution_mbpp(entry):
    tests = ["\n".join(entry["test_imports"]) + "\n" + test for test in entry["test_list"]]
    # Append all items in test_imports to each item in test_list
    # tests = [entry["test_imports"] + test for test in entry["test_list"]]
    # Assuming is_test_valid_mbpp takes the generated code and a list of combined tests
    valid = is_test_valid_mbpp(entry["generated_code"], tests)
    
    entry["solution_valid"] = valid
    return entry

def check_solution_intermediate_results_mbpp(entry, code, iteration):
    tests = ["\n".join(entry["test_imports"]) + "\n" + test for test in entry["test_list"]]
    valid_key = f"valid_{iteration}"
    valid = is_test_valid_mbpp(code, tests)
    entry[valid_key] = valid
    return entry


def check_correctness(entry):
    tests = [test for test in entry["test_list"]]
    
    # Assuming is_test_valid_mbpp takes the generated code and a list of combined tests
    valid = is_test_valid_mbpp(entry["code"], tests)
    
    entry["correct"] = valid
    return entry

def create_function_definition(entry):
    # Extract the function signature from the prompt
    prompt = entry["prompt"]
    signature_end = prompt.index(")") + 1
    function_signature = prompt[:signature_end].strip()
    
    # Construct the function definition
    function_def = f"{function_signature}:\n"
    function_def += entry["canonical_solution"]
    
    return function_def 


def test_accuracy(entry, solution):
    total = len(entry["generated_tests"])
    count = 0
    for test in entry["generated_tests"]:
        try:
            exec(solution + "\n" + test, {"math": math})
            count += 1
        except Exception:
            pass
    return count, total

#        to_execute = create_function_definition(entry)
#        count, total = test_accuracy(entry, to_execute)

def create_function_definition(entry):
    # Extract the function signature from the prompt
    prompt = entry["prompt"]
    signature_end = prompt.index(")") + 1
    function_signature = prompt[:signature_end].strip()
    
    # Construct the function definition
    function_def = f"{function_signature}:\n"
    function_def += entry["canonical_solution"]
    
    return function_def 