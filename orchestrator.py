from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
import requests
import json, asyncio, time
import pandas as pd
from typing import Optional, Dict, Any, List, Union
from custom_tools import get_web_search_result, calculator
from agents import ai_tutor_tool, exam_guide_crew
from llm_models import azure_llm
from configs import config
from crewai.utilities.events.llm_events import LLMStreamChunkEvent
from crewai.utilities.events.base_event_listener import BaseEventListener


tools = [get_web_search_result, ai_tutor_tool, calculator]
llm_with_tools = azure_llm.bind_tools(tools)


def convert_to_langchain_messages(messages_raw: List[Dict]) -> List[Union[SystemMessage, HumanMessage, AIMessage]]:
    """
    Convert raw message format to LangChain message objects.
    
    Supports:
    - Text-only messages
    - Multimodal messages (text + images)
    - System, human/user, assistant/ai message types
    """
    messages_cleaned = []
    
    for msg in messages_raw:
        role = msg.get("role", "").lower()
        content = msg.get("content")
        
        if role == "system":
            messages_cleaned.append(SystemMessage(content=content))
            
        elif role in ["human", "user"]:
            # Handle multimodal content (text + images)
            if isinstance(content, list):
                # Content is a list of content blocks (text, images)
                messages_cleaned.append(HumanMessage(content=content))
            else:
                # Simple text
                messages_cleaned.append(HumanMessage(content=content))
                
        elif role in ["assistant"]:
            messages_cleaned.append(AIMessage(content=content))
            
        else:
            # Default to HumanMessage for unknown roles
            print(f"Warning: Unknown role '{role}', treating as human message")
            messages_cleaned.append(HumanMessage(content=content))
    
    return messages_cleaned


async def orchestrator_agent(messages):
    """
    Process messages through LLM with tools and yield streaming responses
    """
    chat_history = messages.copy()
    chat_history = [{"role": "system",
                    "content": f"""You are an experienced AI Tutor helping Users prepare for their SEBI Certification Exams.\
                        Always repond in {config.user_language} Language irrespective of the language of the user query.\
                            Maintain a postive tone always. follow all information and instructions received from tools.\
                    IMPORTANT: If there are any questions which are not related to SEBI or SEBI certification exam topics then let user know that you can not answer this."""}] + chat_history
    chat_history = convert_to_langchain_messages(chat_history)
    chunks = []
    try:
        # Collect all chunks first
        for chunk in llm_with_tools.stream(chat_history):
            chunks.append(chunk)
        
        # Process chunks and handle tool calls
        if chunks:
            full_response = chunks[0]
            for chunk in chunks[1:]:
                full_response = full_response + chunk
            
            chat_history.append(full_response)
            
            # Check if tools were called
            if hasattr(full_response, 'tool_calls') and full_response.tool_calls:
                for tool_call in full_response.tool_calls:
                    tool_name = tool_call['name']
                    
                    # Execute the appropriate tool
                    try:
                        if tool_name == 'get_web_search_result':
                            # Yield tool usage notification
                            tool_data = {
                                "type": "tool_usage",
                                "content": f"\\nSearching the Web for information",
                                # "tool_name": tool_name
                            }
                            yield f"data: {json.dumps(tool_data, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0.01)
                            result = get_web_search_result.invoke(tool_call['args'])
                            tool_message = ToolMessage(
                                content=result,
                                tool_call_id=tool_call['id'],
                                name=tool_name
                            )
                            chat_history.append(tool_message)
                        elif tool_name == 'ai_tutor_tool':
                            # Yield tool usage notification
                            tool_data = {
                                "type": "tool_usage",
                                "content": f"\\nCalling AI Tutor Agent for information",
                                # "tool_name": tool_name
                            }
                            yield f"data: {json.dumps(tool_data, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0.01)
                            result = ai_tutor_tool.invoke(tool_call['args'])
                            tool_message = ToolMessage(
                                content= str(result),
                                tool_call_id=tool_call['id'],
                                name=tool_name
                            )
                            chat_history.append(tool_message)
                            # print("after_tool_chat_history", str(chat_history))
                        elif tool_name == 'calculator':
                            # Yield tool usage notification
                            tool_data = {
                                "type": "tool_usage",
                                "content": f"\\nUsing the Calculator",
                                # "tool_name": tool_name
                            }
                            yield f"data: {json.dumps(tool_data, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0.01)
                            result = calculator.invoke(tool_call['args'])
                            tool_message = ToolMessage(
                                content=result,
                                tool_call_id=tool_call['id'],
                                name=tool_name
                            )
                            chat_history.append(tool_message)
                    
                    except Exception as e:
                        error_data = {
                            "type": "error",
                            "content": f"Error executing tool {tool_name}: {e}"
                        }
                        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                
                # Send newline before final response
                yield f"data: {json.dumps({'type': 'newline', 'content': '\\n'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'newline', 'content': 'Generating Final Response'}, ensure_ascii=False)}\n\n"
                # Stream the final response after tool execution
                for chunk in llm_with_tools.stream(chat_history):
                    if chunk.content:
                        data = {
                            "type": "final_content",
                            "content": chunk.content
                        }
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.01)
            else:
                # No tools needed - stream the response immediately
                for chunk in chunks:
                    if chunk.content:
                        data = {
                            "type": "content",
                            "content": chunk.content
                        }
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.01)

    except Exception as e:
        error_data = {
            "type": "error", 
            "content": f"Error in chat processing: {str(e)}"
        }
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    # Send completion signal
    if config.kb_results:
        # Remove page_content from each source, keeping only metadata
        sources = []
        for obj in config.kb_results:
            # obj.pop('page_content', None)  # Remove page_content
            sources.append({"document_name": obj.get("document_name"),
                            "page_number": obj.get("page_number")})
        
        source_data = {
            "type": "source",
            "content": sources
        }
        yield f"data: {json.dumps(source_data, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.01)

    yield "data: [DONE]\n\n"

exam_questions_dict = {"mf_foundation": 
                        {"exam_name": "NISM-Series-V-B: Mutual Fund Foundation Certification",
                        "file_path": r"./data/mf_foundation_test_questions.json"},
                    "investor_awareness":
                        {"exam_name": "SEBI Investor Awareness Certification",
                        "file_path": r"./data/investor_awareness_test_questions.json"},
                    "invest_advisor":
                        {"exam_name": "NISM-Series-X-A: Investment Adviser (Level 1) Certification",
                        "file_path": r"./data/invest_advisor_test_questions.json"},
                    }

def question_generator(prev_questions: list[Dict, str], exam_type: str, is_initial: bool = False) -> str:
    """
    Generate next question based on previous questions and exam type
    
    Args:
        prev_questions: List of previous question dictionaries with user responses
        exam_type: Type of exam (investor_awareness, mf_foundation, invest_advisor)
        is_initial: Whether this is the first question request
    """
    # Convert messages list to text string
    messages_text = ""
    
    if prev_questions:
        for i, question_data in enumerate(prev_questions):
            messages_text += f"Question {i + 1}:\n"
            messages_text += f"{json.dumps(question_data, indent=2)}\n"
            messages_text += "-" * 50 + "\n"
    
    exam_details = exam_questions_dict[exam_type]
    sample_questions = ""
    with open(exam_details["file_path"], 'r', encoding='utf-8') as file:
            json_list = json.load(file)
            for i, obj in enumerate(json_list, 1):
                sample_questions += f"Question {i}: {json.dumps(obj, ensure_ascii=False)}" + "\n"

    prompt = f"""You are an experienced Examiner who makes the questions for various certification exams conducted by SEBI.\
        You will be given some questions for an exam, you will select the questions from them based on the adaptability of the examinee,\
        that is, if the examinee is able to answer questions about any Topic then you ask another question from the same topic with increased difficulty,\
        it examinee is able to answer that question as well, then you will move to another topic. You will be given what are the previous questions \
        attempted by the examinee and whether they answered it correctly or not. Based on that information you will gradually increase the difficulty level \
            and make sure all the topics are getting covered.

        EXAM NAME: {exam_details['exam_name']}

        SAMPLE QUESTIONS: 
        {sample_questions}

        PREVIOUSLY ASKED QUESTIONS and RESULTS:
        {"This is the first question, so no previous questions are available" if is_initial else messages_text}
        
        You will only select a new question from the given sample questions. you will never repeat same questions asked previously.

        the output will be json format following this example format:
       {{
    "question": "",
    "options": [
        {{"a": "option a text"}},
        {{"b": "option b text"}},
        {{"c": "option c text"}},
        {{"d": "option d text"}}
    ],
    "correct_option": "b",
    "topic_name": "topic name",
    "difficulty": ""
    }}

        QUESTION:
        """
    question = azure_llm.invoke(prompt)
        
    return question.content


async def explain_question_stream(question: str):
    config.kb_results = []

    final_reponse = exam_guide_crew.kickoff(inputs={"question_details": question, "user_language": config.user_language})
    
    res_chunk = {
        "type": "final_content",
        "content": str(final_reponse)
    }
    yield f"data: {json.dumps(res_chunk, ensure_ascii=False)}\n\n"
    await asyncio.sleep(0.01)
    
    if config.kb_results:
        # Remove page_content from each source, keeping only metadata
        sources = []
        for obj in config.kb_results:
            obj.pop('page_content', None)  # Remove page_content
            sources.append(obj)  # Keep document_name and page_number
        
        source_data = {
            "type": "source",
            "content": sources
        }
        yield f"data: {json.dumps(source_data, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.01)

    yield "data: [DONE]\n\n"