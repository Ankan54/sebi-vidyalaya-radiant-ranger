from langchain_core.tools import tool
from crewai_tools import BaseTool
import pandas as pd
from datetime import datetime, timedelta
import requests, re, json, traceback, chromadb
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from collections import defaultdict
from embeddings import get_embeddings
import math, calendar
import numexpr
import numpy as np
from scipy import stats
# from agents import ai_tutor_crew
from configs import config


def clean_text(text):
    """Clean text by removing multiple consecutive newlines and extra whitespace"""
    # Remove multiple consecutive newlines and replace with single newline
    text = re.sub(r'\n\s*\n+', '\n', text)
    # Remove multiple consecutive spaces
    text = re.sub(r' +', ' ', text)
    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    # Remove empty lines and join
    cleaned_lines = [line for line in lines if line]
    return '\n'.join(cleaned_lines)

@tool
def get_web_search_result(query: str):
    """
    Search the web using Serper API and retrieve full content from search result pages.
    
    Use this tool when you need current information from the internet that may not be \
    in your training data, such as:
    - Recent news, events, or developments
    - Current policies, statistics, or data
    - Latest circulars or policy documentation
    
    Args:
        query (str): The search query to find relevant web content. Be specific for better results \
            (e.g., "Python machine learning libraries 2024" instead of just "machine learning"). \
                Write the query in English, based on what you want to find from internet.
    
    Returns:
        A json string of search results, each containing:
            - title (str): Page title from search results
            - url (str): Source URL of the content
            - full_content (str): Complete cleaned text content from the webpage 
                                (truncated to 5000 chars for efficiency)
    """
    print('here')
    serper_url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": config.SERPER_API_KEY}
    payload = {"q": query}
    
    response = requests.post(serper_url, json=payload, headers=headers)
    search_results = response.json()
    
    full_content_results = []
    
    for result in search_results.get('organic', []):
        url = result['link']
        try:
            # Fetch the full page content
            page_response = requests.get(url, timeout=10)
            soup = BeautifulSoup(page_response.content, 'html.parser')
            
            full_text = soup.get_text()
            
            cleaned_text = clean_text(full_text)

            full_content_results.append({
                'title': result['title'],
                'url': url,
                'full_content': cleaned_text[:5000]  # Limit to first 5000 chars
            })
        except Exception as e:
            # print(f"Error fetching {url}: {e}")
            continue
    
    return json.dumps(full_content_results)


def display_results(results):
    """Display query results in a readable format"""
    
    if not results or not results['documents'][0]:
        return []
        
    document_list = []
    
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        metadata = results['metadatas'][0][i]
        distance = results['distances'][0][i]
        doc_id = results['ids'][0][i]
        
        # Create document JSON object
        document_json = {
            "page_content": doc,
            "document_name": metadata['file_name'],
            "page_number": metadata['page_number'],
        }
        
        # Convert to JSON string and add to list
        document_list.append(document_json)
    
    return json.dumps(document_list, ensure_ascii=False)


@tool
def search_knowledge_base(query: str):
    """
    This tool performs semantic search in a vector database which contains the study materials to prepare \
    for various SEBI certification exams.
    Use this tool find aforesaid kind of information from the vector db.
    
    Args:
        query (str): The search query which will be used to perform semantic search. \
            so, ensure to use correct terms with correct phrases without using unnecessary stop words.
        
    Returns:
        json string containing: semantic search results with source document name and page number.
    """
    # Connect to ChromaDB
    client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
    
    try:
        collection_name = config.exam_name if config.exam_name else "invest_advisor"
        # Get the collection
        collection = client.get_collection(name=collection_name)

        # Generate embedding for the query
        print("search_query", query)
        query_embedding = get_embeddings(query)
        # Perform semantic search
        results = collection.query(
            query_embeddings=[query_embedding],  # Use embedding instead of text
            n_results= 10
        )
        return display_results(results)
        
    except Exception as e:
        print(f"Error querying collection: {str(e)}\n {traceback.format_exc()}")
        return f"Error: {str(e)}"


class StudyMaterialSearchTool(BaseTool):
    name: str = "Study Material Search Tool"
    description: str = ("""This tool searches a vectorized knowledge base which contains all the study materials \
        to prepare for various SEBI certification exams.
    
    Args:
        query (str): The search query which will be used to perform semantic search. \
            so, ensure to use correct terms with correct phrases without using unnecessary stop words.
        
    Returns:
        json string containing: semantic search results with source document name and page number.
    """)
    
    def _run(self, query: str) -> str:
        output = search_knowledge_base(query)
        config.kb_results = json.loads(output)
        return output


# exam_details_dict = {"mf_foundation": 
#                         {"exam_name": "NISM-Series-V-B: Mutual Fund Foundation Certification",
#                         "file_path": r"/home/radiant_ranger_gcphackathon/sebi_vidyalaya/data/Mutual Fund Foundation Certification Examination.txt"},
#                     "investor_awareness":
#                         {"exam_name": "SEBI Investor Awareness Certification",
#                         "file_path": r"/home/radiant_ranger_gcphackathon/sebi_vidyalaya/data/sebi_investor_awareness_exam_overview.txt"},
#                     "invest_advisor":
#                         {"exam_name": "NISM-Series-X-A: Investment Adviser (Level 1) Certification",
#                         "file_path": r"/home/radiant_ranger_gcphackathon/sebi_vidyalaya/data/Investment Adviser (Level 1).txt"},
#                     }

# @tool
# def ai_tutor_tool(user_query: str):
#     """
#     Use this tool when you are answering any questions regarding SEBI certification Exams. \
#         the question can be regarding exam process, syllabus, or can be about any particular topic or concept that can be part of the Exam.
        
#     Args:
#         user_query (str): The question asked by the user. rewrite it if it contains vague or indirect reference to anything from the chat history,\
#             if the question is clear use as it is.
    
#     Returns:
#         The infromation required to Answer the question in Text format.
#     """
#     if not config.exam_name:
#         config.exam_name = "invest_advisor"
#     if not config.user_language:
#         config.user_language = 'English'
#     if not config.chroma_collection_name:
#         config.chroma_collection_name = config.exam_name
    
#     exam_type = exam_details_dict[config.exam_name]
#     exam_overview = ""

#     with open(exam_type['file_path'], "r") as file:
#         exam_overview = file.read()
    
#     result = ai_tutor_crew.kickoff(inputs={"user_query": user_query,
#                                         "exam_name": exam_type["exam_name"], "exam_overview": exam_overview,
#                                         "user_language": config.user_language})

#     return result



class WebSearchTool(BaseTool):
    name: str ="Web Search Tool"
    description: str = ("""Search the web using Serper API and retrieve full content from search result pages.
    Use this tool when you need current information from the internet that may not be \
    in your training data, such as:
    - Recent news, events, or developments
    - Current policies, statistics, or data
    - Latest circulars or policy documentation
    
    Args:
        query (str): The search query to find relevant web content. Be specific for better results \
            (e.g., "Python machine learning libraries 2024" instead of just "machine learning"). \
                Write the query in English, based on what you want to find from internet.
    
    Returns:
        A json string of search results, each containing:
            - title (str): Page title from search results
            - url (str): Source URL of the content
            - full_content (str): Complete cleaned text content from the webpage 
                                (truncated to 5000 chars for efficiency)
    """)
    
    def _run(self, query: str) -> str:
        return get_web_search_result(query)
        

@tool
def calculator(expression: str) -> str:
    """Calculate mathematical and statistical expressions safely using Python's numexpr and numpy.
    
    This tool should be used whenever you need to perform mathematical calculations, \
    solve equations, evaluate numerical expressions, or compute statistical measures. \
    It can handle basic arithmetic, advanced mathematical operations, statistical functions, \
    and supports mathematical constants.
    
    WHEN TO USE:
    - Basic arithmetic: addition, subtraction, multiplication, division
    - Advanced math: exponents, roots, logarithms, trigonometric functions
    - Statistical calculations: mean, median, mode, standard deviation
    - Complex expressions with parentheses and operator precedence
    - Calculations involving mathematical constants (pi, e)
    - Any time precise numerical or statistical computation is required
    
    SUPPORTED OPERATIONS:
    - Arithmetic: +, -, *, /, %, ** (power)
    - Math functions: sin, cos, tan, log, log10, exp, sqrt, abs
    - Statistical functions: mean([1,2,3]), std([1,2,3]), median([1,2,3])
    - Constants: pi (3.14159...), e (2.71828...)
    - Parentheses for grouping: (2 + 3) * 4
    
    EXAMPLES:
    - Simple math: "2 + 3 * 4" → 14
    - With parentheses: "(2 + 3) * 4" → 20
    - Powers: "2 ** 8" → 256
    - Square root: "sqrt(16)" → 4.0
    - Mean: "mean([1, 2, 3, 4, 5])" → 3.0
    - Standard deviation: "std([1, 2, 3, 4, 5])" → 1.58
    - Median: "median([1, 2, 3, 4, 5])" → 3.0
    - Combined: "mean([1, 2, 3]) + std([4, 5, 6])" → 2.82
    
    Args:
        expression (str): A mathematical or statistical expression as a string. 
                         For statistical functions, use format: function([num1, num2, ...])
                         For basic math: use standard mathematical notation
                         Examples: "mean([1,2,3])", "2+3*4", "std([10,20,30]) + 5"
                         
    Returns:
        str: The numerical result of the calculation as a string.
    """
    # Enhanced local dictionary with statistical functions
    def mean(data_list):
        return np.mean(data_list)
    
    def median(data_list):
        return np.median(data_list)
    
    def mode(data_list):
        mode_result = stats.mode(data_list, keepdims=True)
        return float(mode_result.mode[0])
    
    def std(data_list):
        return np.std(data_list)
    
    def var(data_list):
        return np.var(data_list)
    
    def min_val(data_list):
        return np.min(data_list)
    
    def max_val(data_list):
        return np.max(data_list)
    
    local_dict = {
        "pi": math.pi, 
        "e": math.e,
        "mean": mean,
        "median": median, 
        "mode": mode,
        "std": std,
        "var": var,
        "min": min_val,
        "max": max_val,
        "sqrt": np.sqrt,
        "sin": np.sin,
        "cos": np.cos,
        "tan": np.tan,
        "log": np.log,
        "log10": np.log10,
        "exp": np.exp,
        "abs": np.abs
    }
    
    try:
        # Handle list notation by converting to numpy arrays
        expression_clean = expression.strip()
        
        # Check if expression contains statistical functions with lists
        if any(func in expression_clean for func in ['mean', 'median', 'mode', 'std', 'var', 'min', 'max']):
            # Use eval for statistical expressions (more controlled environment)
            result = eval(expression_clean, {"__builtins__": {}}, local_dict)
        else:
            # Use numexpr for simple mathematical expressions
            result = numexpr.evaluate(expression_clean, local_dict=local_dict)
            
        return str(result)
    
    except Exception as e:
        return f"Error: {str(e)}. Please check your expression format."


class CalculatorTool(BaseTool):
    name: str ="Calculator Tool"
    description: str = ("""Calculate mathematical and statistical expressions safely using Python's numexpr and numpy.
    
    This tool should be used whenever you need to perform mathematical calculations, \
    solve equations, evaluate numerical expressions, or compute statistical measures. \
    It can handle basic arithmetic, advanced mathematical operations, statistical functions, \
    and supports mathematical constants.
    
    WHEN TO USE:
    - Basic arithmetic: addition, subtraction, multiplication, division
    - Advanced math: exponents, roots, logarithms, trigonometric functions
    - Statistical calculations: mean, median, mode, standard deviation
    - Complex expressions with parentheses and operator precedence
    - Calculations involving mathematical constants (pi, e)
    - Any time precise numerical or statistical computation is required
    
    SUPPORTED OPERATIONS:
    - Arithmetic: +, -, *, /, %, ** (power)
    - Math functions: sin, cos, tan, log, log10, exp, sqrt, abs
    - Statistical functions: mean([1,2,3]), std([1,2,3]), median([1,2,3])
    - Constants: pi (3.14159...), e (2.71828...)
    - Parentheses for grouping: (2 + 3) * 4
    
    EXAMPLES:
    - Simple math: "2 + 3 * 4" → 14
    - With parentheses: "(2 + 3) * 4" → 20
    - Powers: "2 ** 8" → 256
    - Square root: "sqrt(16)" → 4.0
    - Mean: "mean([1, 2, 3, 4, 5])" → 3.0
    - Standard deviation: "std([1, 2, 3, 4, 5])" → 1.58
    - Median: "median([1, 2, 3, 4, 5])" → 3.0
    - Combined: "mean([1, 2, 3]) + std([4, 5, 6])" → 2.82
    
    Args:
        expression (str): A mathematical or statistical expression as a string. 
                         For statistical functions, use format: function([num1, num2, ...])
                         For basic math: use standard mathematical notation
                         Examples: "mean([1,2,3])", "2+3*4", "std([10,20,30]) + 5"
                         
    Returns:
        str: The numerical result of the calculation as a string.""")
    
    def _run(self, expression: str) -> str:
        return calculator(expression)


@tool
def date_calculator(operation: str, date_input: str = "") -> str:
    """Get current date, find day of week, calculate date differences, and perform date operations.
    
    This tool should be used whenever you need to work with dates, find what day \
    a specific date falls on, get today's date, calculate days between dates, \
    or perform other calendar-related calculations.
    
    WHEN TO USE:
    - Get today's date
    - Find what day of the week a specific date is
    - Calculate days between two dates
    - Add or subtract days from a date
    - Get the current day of the week
    - Find dates for specific weekdays
    - Check if a year is a leap year
    - Get month information
    
    SUPPORTED OPERATIONS:
    - "today": Get today's date
    - "day_of_week": Find what day a specific date falls on
    - "days_between": Calculate days between two dates
    - "add_days": Add specified days to a date
    - "subtract_days": Subtract specified days from a date
    - "current_weekday": Get current day of the week
    - "is_leap_year": Check if a year is leap year
    - "month_days": Get number of days in a month
    - "week_number": Get week number of the year for a date
    
    EXAMPLES:
    - Get today: operation="today" → "2025-08-18 (Monday)"
    - Day of week: operation="day_of_week", date_input="2025-12-25" → "Thursday"
    - Days between: operation="days_between", date_input="2025-08-18,2025-12-25" → "129 days"
    - Add days: operation="add_days", date_input="2025-08-18,10" → "2025-08-28 (Thursday)"
    - Current weekday: operation="current_weekday" → "Monday"
    - Leap year: operation="is_leap_year", date_input="2024" → "Yes, 2024 is a leap year"
    
    Args:
        operation (str): The date operation to perform. Must be one of the supported operations.
        date_input Optional(str): Input date(s) or parameters required for the operation.
                         Format depends on operation:
                         - Single date: "YYYY-MM-DD" (e.g., "2025-08-18")
                         - Two dates: "YYYY-MM-DD,YYYY-MM-DD" (e.g., "2025-08-18,2025-12-25")
                         - Date with number: "YYYY-MM-DD,number" (e.g., "2025-08-18,30")
                         - Year only: "YYYY" (e.g., "2024")
                         - Year and month: "YYYY,MM" (e.g., "2025,2")
                         
    Returns:
        str: The result of the date calculation or operation as a string.
    """
    try:
        today = datetime.now()
        
        if operation == "today":
            weekday = today.strftime("%A")
            return f"{today.strftime('%Y-%m-%d')} ({weekday})"
            
        elif operation == "current_weekday":
            return today.strftime("%A")
            
        elif operation == "day_of_week":
            if not date_input:
                return "Error: Please provide a date in YYYY-MM-DD format"
            date_obj = datetime.strptime(date_input.strip(), "%Y-%m-%d")
            return date_obj.strftime("%A")
            
        elif operation == "days_between":
            if not date_input or "," not in date_input:
                return "Error: Please provide two dates separated by comma (YYYY-MM-DD,YYYY-MM-DD)"
            date1_str, date2_str = date_input.split(",")
            date1 = datetime.strptime(date1_str.strip(), "%Y-%m-%d")
            date2 = datetime.strptime(date2_str.strip(), "%Y-%m-%d")
            diff = abs((date2 - date1).days)
            return f"{diff} days"
            
        elif operation == "add_days":
            if not date_input or "," not in date_input:
                return "Error: Please provide date and number of days (YYYY-MM-DD,number)"
            date_str, days_str = date_input.split(",")
            base_date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
            days_to_add = int(days_str.strip())
            result_date = base_date + timedelta(days=days_to_add)
            weekday = result_date.strftime("%A")
            return f"{result_date.strftime('%Y-%m-%d')} ({weekday})"
            
        elif operation == "subtract_days":
            if not date_input or "," not in date_input:
                return "Error: Please provide date and number of days (YYYY-MM-DD,number)"
            date_str, days_str = date_input.split(",")
            base_date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
            days_to_subtract = int(days_str.strip())
            result_date = base_date - timedelta(days=days_to_subtract)
            weekday = result_date.strftime("%A")
            return f"{result_date.strftime('%Y-%m-%d')} ({weekday})"
            
        elif operation == "is_leap_year":
            if not date_input:
                return "Error: Please provide a year"
            year = int(date_input.strip())
            is_leap = calendar.isleap(year)
            return f"{'Yes' if is_leap else 'No'}, {year} is {'a leap year' if is_leap else 'not a leap year'}"
            
        elif operation == "month_days":
            if not date_input or "," not in date_input:
                return "Error: Please provide year and month (YYYY,MM)"
            year_str, month_str = date_input.split(",")
            year = int(year_str.strip())
            month = int(month_str.strip())
            days_in_month = calendar.monthrange(year, month)[1]
            month_name = calendar.month_name[month]
            return f"{month_name} {year} has {days_in_month} days"
            
        elif operation == "week_number":
            if not date_input:
                return "Error: Please provide a date in YYYY-MM-DD format"
            date_obj = datetime.strptime(date_input.strip(), "%Y-%m-%d")
            week_num = date_obj.isocalendar()[1]
            return f"Week {week_num} of {date_obj.year}"
            
        else:
            return f"Error: Unsupported operation '{operation}'. Supported operations: today, day_of_week, days_between, add_days, subtract_days, current_weekday, is_leap_year, month_days, week_number"
            
    except ValueError as e:
        return f"Error: Invalid date format or input. Please use YYYY-MM-DD format. {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

class DateSearchTool(BaseTool):
    name: str ="Date Search Tool"
    description: str = ("""Get current date, find day of week, calculate date differences, and perform date operations.
    
    This tool should be used whenever you need to work with dates, find what day \
    a specific date falls on, get today's date, calculate days between dates, \
    or perform other calendar-related calculations.
    
    WHEN TO USE:
    - Get today's date
    - Find what day of the week a specific date is
    - Calculate days between two dates
    - Add or subtract days from a date
    - Get the current day of the week
    - Find dates for specific weekdays
    - Check if a year is a leap year
    - Get month information
    
    SUPPORTED OPERATIONS:
    - "today": Get today's date
    - "day_of_week": Find what day a specific date falls on
    - "days_between": Calculate days between two dates
    - "add_days": Add specified days to a date
    - "subtract_days": Subtract specified days from a date
    - "current_weekday": Get current day of the week
    - "is_leap_year": Check if a year is leap year
    - "month_days": Get number of days in a month
    - "week_number": Get week number of the year for a date
    
    EXAMPLES:
    - Get today: operation="today" → "2025-08-18 (Monday)"
    - Day of week: operation="day_of_week", date_input="2025-12-25" → "Thursday"
    - Days between: operation="days_between", date_input="2025-08-18,2025-12-25" → "129 days"
    - Add days: operation="add_days", date_input="2025-08-18,10" → "2025-08-28 (Thursday)"
    - Current weekday: operation="current_weekday" → "Monday"
    - Leap year: operation="is_leap_year", date_input="2024" → "Yes, 2024 is a leap year"
    
    Args:
        operation (str): The date operation to perform. Must be one of the supported operations.
        date_input Optional(str): Input date(s) or parameters required for the operation.
                         Format depends on operation:
                         - Single date: "YYYY-MM-DD" (e.g., "2025-08-18")
                         - Two dates: "YYYY-MM-DD,YYYY-MM-DD" (e.g., "2025-08-18,2025-12-25")
                         - Date with number: "YYYY-MM-DD,number" (e.g., "2025-08-18,30")
                         - Year only: "YYYY" (e.g., "2024")
                         - Year and month: "YYYY,MM" (e.g., "2025,2")
                         
    Returns:
        str: The result of the date calculation or operation as a string.
    """)
    
    def _run(self, operation:str, date_input:str = "") -> str:
        return date_calculator(operation, date_input)