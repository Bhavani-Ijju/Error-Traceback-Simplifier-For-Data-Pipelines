from fastapi import FastAPI
from pydantic import BaseModel
import re
import spacy

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Initialize FastAPI
app = FastAPI()

# Define request model
class ErrorLog(BaseModel):
    log_text: str

# Function to extract errors from a traceback log
def parse_log(log_text):
    """Extracts multiple errors from a traceback log, handling nested exceptions separately."""
    
    log_sections = re.split(r'During handling of the above exception.*?\n', log_text)
    errors = []
    
    for section in log_sections:
        pattern = r'File "(.*?)", line (\d+), in (.*?)\n(?:.*?)\n(\w+Error): (.*)'
        match = re.search(pattern, section, re.DOTALL)
        
        if match:
            errors.append({
                "file": match.group(1),
                "line": int(match.group(2)),
                "function": match.group(3),
                "error_type": match.group(4),
                "error_message": match.group(5).strip()
            })

    return errors if errors else None

# Function to simplify error messages
def simplify_error(error_type, error_message):
    """Converts technical error messages into human-readable explanations."""
    
    error_explanations = {
        "FileNotFoundError": "The system cannot find the file. Please check if it exists in the correct directory.",
        "PermissionError": "Permission denied. Try running the script with admin privileges or check file permissions.",
        "KeyError": "A dictionary key is missing. Ensure the key exists before accessing it.",
        "TypeError": "Invalid data type used. Check if you are using the correct type.",
        "ValueError": "Incorrect value provided. Verify that the input is valid.",
        "IndexError": "Trying to access an index that doesn't exist in the list.",
        "ZeroDivisionError": "You are trying to divide by zero, which is not allowed.",
        "NameError": "A variable or function name is undefined. Ensure it is declared before use.",
        "ModuleNotFoundError": "The required module is missing. Install it using `pip install <module_name>`.",
        "ImportError": "The module or function being imported does not exist. Check the spelling and module documentation."
    }

    if error_type in error_explanations:
        return error_explanations[error_type]

    # If error type is not in predefined explanations, use NLP to simplify it
    doc = nlp(error_message)
    simplified_text = "This error occurred because: " + " ".join([token.text for token in doc if not token.is_punct])
    
    return simplified_text

# API endpoint to parse and simplify errors
@app.post("/parse_errors")
def get_parsed_errors(request: ErrorLog):
    errors = parse_log(request.log_text)
    if errors:
        for error in errors:
            error["simplified_message"] = simplify_error(error["error_type"], error["error_message"])
        return {"errors": errors}
    return {"message": "No errors found in log."}
