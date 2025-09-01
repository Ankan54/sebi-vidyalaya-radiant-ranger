from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
import requests
import json, asyncio
import pandas as pd
from typing import Optional, Dict, Any, List, Union
from custom_tools import get_web_search_result, calculator
from agents import ai_tutor_tool
from llm_models import llm
from configs import config


tools = [get_web_search_result, ai_tutor_tool, calculator]
llm_with_tools = llm.bind_tools(tools)


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
                            Maintain a postive tone always."""}] + chat_history
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
                            yield f"data: {json.dumps(tool_data)}\n\n"
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
                            yield f"data: {json.dumps(tool_data)}\n\n"
                            await asyncio.sleep(0.01)
                            result = ai_tutor_tool.invoke(tool_call['args'])
                            tool_message = ToolMessage(
                                content= "Strictly Adhere to the information and all the Instructions given below: \n" + result,
                                tool_call_id=tool_call['id'],
                                name=tool_name
                            )
                            chat_history.append(tool_message)
                        elif tool_name == 'calculator':
                            # Yield tool usage notification
                            tool_data = {
                                "type": "tool_usage",
                                "content": f"\\nUsing the Calculator",
                                # "tool_name": tool_name
                            }
                            yield f"data: {json.dumps(tool_data)}\n\n"
                            await asyncio.sleep(0.01)
                            result = calculator.invoke(tool_call['args'])
                            tool_message = ToolMessage(
                                content=result,
                                tool_call_id=tool_call['id'],
                                # name=tool_name
                            )
                            chat_history.append(tool_message)
                    
                    except Exception as e:
                        error_data = {
                            "type": "error",
                            "content": f"Error executing tool {tool_name}: {e}"
                        }
                        yield f"data: {json.dumps(error_data)}\n\n"
                
                # Send newline before final response
                yield f"data: {json.dumps({'type': 'newline', 'content': '\\n'})}\n\n"
                yield f"data: {json.dumps({'type': 'newline', 'content': 'Generating Final Response'})}\n\n"
                
                # Stream the final response after tool execution
                for chunk in llm_with_tools.stream(chat_history):
                    if chunk.content:
                        data = {
                            "type": "final_content",
                            "content": chunk.content
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                        await asyncio.sleep(0.01)
            else:
                # No tools needed - stream the response immediately
                for chunk in chunks:
                    if chunk.content:
                        data = {
                            "type": "content",
                            "content": chunk.content
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                        await asyncio.sleep(0.01)
    
    except Exception as e:
        error_data = {
            "type": "error", 
            "content": f"Error in chat processing: {str(e)}"
        }
        yield f"data: {json.dumps(error_data)}\n\n"
    
    # Send completion signal
    yield "data: [DONE]\n\n"