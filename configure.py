# # config.py
# import os


# # Paths
# USER_DATA_PATH = "/home/sracha/Sattvastha/pipeline/new_pipeline/user_data.json"
# RAG_BASE_DIRECTORY = "/home/sracha/Sattvastha/pipeline/all_content"
# RAG_CATEGORIES = ["Ayurveda", "Lifestyle", "psychology", "Yoga", "Mental_health"]
# # Prompt templates
# QUESTION_CLASSIFICATION_PROMPT = """
# Classify the following user input into one of these categories:
# 1. "question" - If the user is asking a factual question that could be answered with knowledge
# 2. "general" - If the user is just chatting or expressing feelings

# User Input: {user_input}

# Respond with only one word: either "question" or "general"
# """

# config.py
import os
from dotenv import load_dotenv
import json
# Load environment variables from .env file
load_dotenv()


def read_txt(path):
    with open(path, 'r') as f:
        document = f.read()
    return document

def read_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    story = (data["Mental Health Stories"]["Depression"]["S1"])
    guided_meditation = (data["Meditation"]["Guided Meditation"]["M1"])
    asanas = (data["Yoga"]["Asanas"]["A1"])
    return story, guided_meditation, asanas


def llm_prompt():
    story, guided_meditation, asanas = read_json("categories.json")
    document = read_txt("sample.txt")
    LLM_PROMPT = f'''
            So the task we are now performing is a smart chunking task. You don't have to modify any stuff. I'll give you a complete book that contains a large amount of text which will be related to mental heatl or ayurveda or lifestyle or any other topic as well which is basically somehow connected to overall well beign of a human body
            Now your task is to extract out/or we can say that chunk the big piece of text into smaller pieces.
            Now the results fater chunking that you'll create could be a story, a moral line, or poems or even any shlokas. From an exercise book, it could be methods of how to perform a particular asan or exercise. 
            For a meditation guide, it could be the steps to perform a particular meditation. I'll be giving you the examples of how the chunked results should look like. And also what are the categories
            So currently we have 3 categories:
            1. Mental Health Stories: These are stories related to mental health issues like depression, anxiety, stress, etc. Example of chunked result:
            {story}
            2. Meditation: These are guided meditation scripts that help in relaxation and mindfulness. Example of chunked result:
            {guided_meditation}
            3. Yoga: These are yoga asanas and practices for physical and mental well-being. Example of chunked result:
            {asanas}    

            Now This is the document from which you have to extract the similar related chunks. Remember that it is not necessary that the text will match exactly but if for example there's a story the essence of text will be same as I gave and similarly for other categories
            Document: {document}
            '''
    return LLM_PROMPT

# Paths
USER_DATA_PATH = "/home/surajracha/sameer/thon/user_data.json"
RAG_BASE_DIRECTORY = "/home/surajracha/sameer/thon/all_content"
RAG_CATEGORIES = ["Ayurveda", "Lifestyle", "psychology", "Yoga", "Mental_health"]

# Prompt templates
QUESTION_CLASSIFICATION_PROMPT = """
Classify the following user input into one of these categories:
1. "question" - If the user is asking a factual question that could be answered with knowledge
2. "general" - If the user is just chatting or expressing feelings

User Input: {user_input}

Respond with only one word: either "question" or "general"
"""