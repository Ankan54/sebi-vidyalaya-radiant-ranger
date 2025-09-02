import warnings
warnings.filterwarnings('ignore')
from crewai import Agent, Task, Crew, Process
from langchain_openai import AzureChatOpenAI
from custom_tools import WebSearchTool, StudyMaterialSearchTool, CalculatorTool, DateSearchTool
from llm_models import llm, llm_stream
from langchain_core.tools import tool
from configs import config
import os
os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'
os.environ['OTEL_SDK_DISABLED'] = 'true'

financial_tutor_agent  = Agent(
    role="Smart AI Tutor for SEBI Certification Exams",
    goal="Explain SEBI regulations, financial concepts, and securities market topics in simple," 
         "beginner-friendly language using the user's preferred Indian language." 
         "Provide accurate, exam-focused answers that help novice learners understand complex financial topics for their SEBI certification exam preparation.",
    
    backstory="""You are an experienced financial educator who has helped thousands of students pass SEBI certification exams. You specialize in breaking down complex financial regulations and market concepts into simple, easy-to-understand explanations. 

Your expertise covers:
- SEBI regulations and investor protection mechanisms
- Mutual fund concepts and operations  
- Securities market structure and participants
- Investment advisory principles
- Risk management and compliance policies and Everything else related to SEBI and Securities Market.

You have a unique ability to:
- Explain technical concepts using everyday Indian examples.
- Identify exactly what a beginner needs to know for exam success.
- Provide practical context that connects theoretical knowledge to real-world applications.

Your teaching style is patient, encouraging, and focused on building confidence in learners.""",
    verbose=True,
    allow_delegation=False,
    tools = [StudyMaterialSearchTool(), CalculatorTool(), DateSearchTool(), WebSearchTool()], 
    max_iter=2,
    llm=llm
)

doubt_resolution_task = Task(
    description="""Take the user's query about SEBI exam topics and provide a comprehensive, beginner-friendly explanation in their preferred language.

Process:
1. Analyze the user's question to identify the specific financial concept or regulation being asked about. it can be about Exam process or syllabus as well
2. Search the knowledge base or available tools for relevant SEBI study materials, regulations, and exam content
3. Extract the most pertinent information that directly answers the user's question
4. Structure the response to build understanding from basic concepts to more specific details
5. Include relevant examples using Indian financial instruments and scenarios
6. Ensure the language level is appropriate for someone new to finance
7. Add exam-specific tips or important points that commonly appear in SEBI tests
8. Only if appliable, try adding any case study related to the user's cultural background, use the user's language to identify the cultural context, so that the user may find it relatable with their life experiences.

Exam Name: {exam_name}
Exam Overview: {exam_overview}

User Query: {user_query}
User Language: {user_language}""",
    
    expected_output="""Your Response will be sent back to the Orchestrator Agent for generating the Final Reposne. \
    You will provide a clear, pointwise answer that includes:

1. **Direct Answer**: an accuracte and concise answer to the user's specific question

2. **Concept Explanation**: Break down the topic into simple terms with definition, key components, and relevance. only if the question is about conceptual topics and not general query about the exam.

3. **Case Study**: During Option Analysis above, Only if applicable, add pointers for at least one relevant case study using Indian financial instruments and local scenarios as per the user region, cultural background.

4. **Exam Focus Points**: Highlight SEBI certification-specific information including key regulations and common exam patterns. Explain the type of questions that can come in the exam from the concerned topic.

5. **Related Concepts**: Briefly mention 2-3 connected topics for further learning.

6. **Instruction for Final Answer Formatting**: Add the instructions which the orchestrators must follow to generate the final answer from your reponse mention the language as well in which the orchestrator agent should respond.

7. *Language*: Generate the reponse only in the user's preferred langauge as provided to you.

Ensure to include all relevant information/statistics (if applicable) in your points.
Write only as per these points and nothing else.""",
    agent=financial_tutor_agent,
)


ai_tutor_crew = Crew(
    agents=[financial_tutor_agent],
    tasks=[doubt_resolution_task],
    verbose=True
)

exam_details_dict = {"mf_foundation": 
                        {"exam_name": "NISM-Series-V-B: Mutual Fund Foundation Certification",
                        "file_path": r"./data/Mutual Fund Foundation Certification Examination.txt"},
                    "investor_awareness":
                        {"exam_name": "SEBI Investor Awareness Certification",
                        "file_path": r"./data/sebi_investor_awareness_exam_overview.txt"},
                    "invest_advisor":
                        {"exam_name": "NISM-Series-X-A: Investment Adviser (Level 1) Certification",
                        "file_path": r"/home/radiant_ranger_gcphackathon/sebi_vidyalaya/data/Investment Adviser (Level 1).txt"},
                    }

@tool
def ai_tutor_tool(user_query: str):
    """
    Use this tool when you are answering any questions regarding SEBI certification Exams. \
        the question can be regarding exam process, syllabus, or can be about any particular topic or concept that can be part of the Exam.
        
    Args:
        user_query (str): The question asked by the user. rewrite it if it contains vague or indirect reference to anything from the chat history,\
            if the question is clear use as it is.
    
    Returns:
        The infromation required to Answer the question in Text format.
    """
    config.kb_results = []
    if not config.exam_name:
        config.exam_name = "invest_advisor"
    if not config.user_language:
        config.user_language = 'English'
    if not config.chroma_collection_name:
        config.chroma_collection_name = config.exam_name
    
    exam_type = exam_details_dict[config.exam_name]
    exam_overview = ""

    with open(exam_type['file_path'], "r") as file:
        exam_overview = file.read()
    
    result = ai_tutor_crew.kickoff(inputs={"user_query": user_query,
                                        "exam_name": exam_type["exam_name"], "exam_overview": exam_overview,
                                        "user_language": config.user_language})

    return result

# user_query = "what is debt fund?"
# exam_name = "NISM-Series-X-A: Investment Adviser (Level 1) Certification Examination"
# with open("/home/radiant_ranger_gcphackathon/sebi_hackathon/Investment Adviser (Level 1).txt", "r") as file:
#     exam_overview = file.read()
# user_language = "Bengali"
# result = ai_tutor_crew.kickoff(inputs={"user_query": user_query,
#                                     "exam_name": exam_name, "exam_overview": exam_overview,
#                                     "user_language": user_language})

# print(result)


exam_guide_agent = Agent(
    role="Smart AI Tutor for SEBI Certification Exam Questions",
    goal="Explain SEBI certification exam questions by analyzing why the correct option is right and why other options are wrong, "
         "using simple, beginner-friendly language in the user's preferred Indian language. "
         "Provide accurate, exam-focused explanations that help novice learners understand complex financial topics and MCQ reasoning for their SEBI certification exam preparation.",
    
    backstory="""You are an experienced financial educator who has helped thousands of students pass SEBI certification exams. You specialize in breaking down complex financial regulations and market concepts into simple, easy-to-understand explanations, particularly for MCQ-based questions.

Your expertise covers:
- SEBI regulations and investor protection mechanisms
- Mutual fund concepts and operations  
- Securities market structure and participants
- Investment advisory principles
- Risk management and compliance policies
- Everything else related to SEBI and Securities Market
- MCQ question analysis and option elimination techniques

You have a unique ability to:
- Explain why each MCQ option is correct or incorrect using everyday Indian examples
- Identify exactly what a beginner needs to know for exam success
- Provide practical context that connects theoretical knowledge to real-world applications
- Break down complex regulatory concepts into simple, digestible explanations

Your teaching style is patient, encouraging, and focused on building confidence in learners through clear MCQ analysis.""",
    verbose=True,
    allow_delegation=False,
    tools = [StudyMaterialSearchTool(), CalculatorTool(), DateSearchTool(), WebSearchTool()],
    max_iter=2,
    llm=llm
)

answer_explanation_task = Task(
    description="""Take the user's SEBI certification exam question with MCQ options and provide a comprehensive, beginner-friendly explanation in their preferred language.
Process:
1. Analyze the exam question to identify the specific financial concept or SEBI regulation being tested
2. Clearly identify which option is correct and provide detailed reasoning with regulatory references
3. For each incorrect option, explain specifically why it is wrong and what misconceptions it might represent
4. Structure the response to build understanding from basic concepts to specific MCQ analysis
5. Include relevant examples using Indian financial instruments and scenarios
6. Ensure the language level is appropriate for someone new to finance
7. Add exam-specific tips about similar question patterns that commonly appear in SEBI tests
8. Only if applicable, try adding a case study on the topic based on the user's cultural background, use the user's language to identify the cultural context

THe Question Deatils are as below,
{question_details}

User Language: {user_language}""",
    
    expected_output="""You will provide a clear, detailed answer that includes:

1. **Direct Answer**: Clearly state which option is correct and provide an accurate, concise explanation of why it's the right choice with relevant SEBI regulation references.

2. **Correct Option Analysis**: Detailed breakdown of why the correct option is right, including the underlying concept, regulatory backing, and practical significance.

3. **Incorrect Options Analysis**: For each wrong option, explain specifically why it's incorrect, what common misconception it represents, and how to avoid such errors.

4. **Concept Explanation**: Break down the topic being tested into simple terms with definition, key components, and relevance to SEBI regulations.

5. **Case Study**: During Option Analysis above, Only if applicable, add pointers for at least one relevant case study using Indian financial instruments and local scenarios as per the user region, cultural background.

6. **Exam Focus Points**: Highlight SEBI certification-specific information including key regulations, common exam patterns, and similar question types that appear in the exam from this topic.

7. **Related Concepts**: Briefly mention 2-3 connected topics if any for further learning that might appear in related questions.

8. **Language**: Generate the response only in the user's preferred language as provided to you.

Ensure to include all relevant information/statistics (if applicable) in your answer
Write only as per these points and nothing else. But don't just write in a pointwise manner, write in a free flowing easy to read manner.
Do not include any introductory statements about what you are going to say, just write the answer.""",
    agent=exam_guide_agent,
)

exam_guide_crew = Crew(
    agents=[exam_guide_agent],
    tasks=[answer_explanation_task],
    verbose=True
)


fact_checker_agent = Agent(
    role="Senior Fact Checker and Accuracy Analyst",
    goal="Verify factual accuracy of text content against provided source materials and assess answer accuracy against user questions",
    backstory="""You are an experienced fact-checker with expertise in information verification and accuracy analysis. \
    You have worked for major news organizations and research institutions, specializing in distinguishing between \
    factual claims and hypothetical examples. You understand that analogies, case studies, and hypothetical scenarios \ 
    should not be fact-checked as they are illustrative rather than factual claims.""",
    verbose=True,
    allow_delegation=False,
    memory=False, llm = llm
)

# Define the Fact Checking Task
fact_check_task = Task(
    description="""
    Analyze the provided text content for factual accuracy and completeness.
    
    **Text Content to Check:**
    {text_content}
    
    **Source Information:**
    {source_content}

    **Original User Question:**
    {user_question}

    **user_language**
    {user_language}
    
    **Instructions:**
    1. Identify factual claims in the text content (ignore analogies, hypothetical examples, case studies)
    2. Verify these claims against the provided source information
    3. If a user question is provided, assess whether the text content accurately addresses the question.
    4. Focus only on verifiable facts, not opinions or illustrative examples
    5. Consider both accuracy of facts and completeness of the answer.
    6. If no factual claims are available then only analyse the correctness of the answer against the user question.
    7. Only verify against the source content given, do not use any other external information.
    8. Always write the reason in the given user language.
    """,
    agent=fact_checker_agent,
    expected_output="""Provide your analysis as a JSON object with exactly these two fields:
    - "accurate": boolean (true if content is factually accurate and accuractely addresses the question topics, false otherwise)
    - "confidence_score": float (a value between 0 to 1, 1 being the highest confidence and 0 being the lowest confidence on accuracy.)
    - "reason": string (pointwise explanation of your findings, including specific inaccuracies or gaps if any)
    
    Do not write anything else other than the JSON."""
)

fact_checker_crew = Crew(
        agents=[fact_checker_agent],
        tasks=[fact_check_task],
        verbose=True,
        memory=False
    )