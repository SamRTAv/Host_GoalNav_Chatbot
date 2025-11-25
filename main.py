#FAST API deployment
# main.py
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.memory import ConversationBufferMemory
from perplexity import Perplexity

from utils import load_user_data, llm
from input_to_llm import extract_chats, extract_goalfocus


DATA_PATH = os.getenv("PERSISTENT_DATA_PATH", ".")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

app = FastAPI()


perplexity_client = Perplexity(api_key=PERPLEXITY_API_KEY)


class ChatRequest(BaseModel):
    user_id: str
    message: str
    username: str = "User" # Default to "User" if not provided

def get_user_files(user_id: str):
    """Generates unique file paths for each user so they don't clash."""
    return {
        "history": os.path.join(DATA_PATH, f"chat_history_{user_id}.jsonl"),
        "focus": os.path.join(DATA_PATH, f"focus_goal_{user_id}.jsonl")
    }

def load_memory_from_file(history_path: str) -> ConversationBufferMemory:
    """Rebuilds LangChain memory from the saved JSONL file."""
    memory = ConversationBufferMemory()
    if os.path.exists(history_path):
        with open(history_path, 'r', encoding='utf-8') as f:
    
            try:
        
                 pass 
            except Exception:
                pass
    return memory


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        user_id = request.user_id
        user_input = request.message
        username = request.username
        
        files = get_user_files(user_id)
        
        if os.path.exists(files['history']):
             last_three_convos = extract_chats(files['history'])
        else:
             last_three_convos = "No conversation history yet."

        if os.path.exists(files['focus']):
             prev_goalandfocus = extract_goalfocus(files['focus'])
        else:
             prev_goalandfocus = "Goal: Establish initial contact. Topic: Introduction."
      
        memory = ConversationBufferMemory() 

        # Note: We use your existing extract_chats but point it to the user-specific file
        last_three_convos = extract_chats(files['history']) if os.path.exists(files['history']) else "No history yet."
        prev_goalandfocus = extract_goalfocus(files['focus']) if os.path.exists(files['focus']) else "No focus yet."
        ncon = 3
        focus_context = f'''
        Ohk, so you are an expert in navigating paths through human conversations. So, let's say if someone is telling you about how they are feeling, what they did
        what other people did to them, what are their problems, what are their goals and aspirations in life and all that stuff.
        Now based on all the above information, you need to figure that as a teacher/Guru (which you are for the person) 
        what should be the topic (or the broad thing that is going on currently as a part of discussion - it could discussion about office, or marriage or house problems or anything) you've to figure this out from based on previous converstaion history.
        At the same time, you have to ask/suggest/recommend further to the person as well right. So for that you have to define a goal (that is basically what should be the exact next step in this conversation - should you be asking a quuestion or should be recommending something or maybe just chatting normally). again this also you've to decide. But goal has to be something which defines the next step
        whereas topic is something which is broad and overall defines what is going on in the converstaion.
        Your response format should be like this:
        "Topic":" <topic> ",
        "Goal":" <goal> "

        Don't output anything else other than this format.
        Here is the conversation history of past {ncon} conversations: {last_three_convos}
        also, here;s the current user question: {user_input}
        You can also look upon what was the topic and goal defined just previously to get better idea.
        previous topic and goal : {prev_goalandfocus}
        Try updating goal on each instance but topic can remain same if the converstaion is still revolving around the same thing. Because obviusly you've to dig deeper with the user, you can't be doing the same thign in the goal
        ALso, if the user isn't talking anymore about the previous topic, you can change the topic as well. Thats why i am providin gyou the previous focus and goal

        '''
 
        
        focus_response = llm.invoke(focus_context)
        
   
        try:
            json_string_to_parse = "{" + focus_response.content + "}"
            parsed_json = json.loads(json_string_to_parse)
            with open(files['focus'], 'a', encoding='utf-8') as f:
                json.dump([parsed_json], f)
                f.write('\n')
        except json.JSONDecodeError:
            print("Warning: Could not parse focus/goal JSON from LLM")

     
        current_goalandfocus = extract_goalfocus(files['focus'])
        
        # We need to manually load history if we want it in the prompt 
        # since we didn't fully rebuild ConversationBufferMemory

        main_context = f"""
            User Context:
            - Name: {username}
            
            Conversation History:
            {memory.load_memory_variables({})['history']}
            
            Current Query: {user_input}
            
            Provide a helpful, supportive response.
            There's a lot of data avaiable and we have run rag on the data to get the best possible answer:
            utilise this to give the answer
            Also, at each step we are determining the topic and goal of the conversation to give a proper direction to the chats. This is to help you (who is acting as a guru to the user)
            to guide him better
            goal is something which defines the next step which you should be taking in the converstaion, don't very rigidly follow it but try to take the direction from it
            whereas topic is something which is broad and overall defines what is going on in the converstaion
            here's the current topic and goal : {current_goalandfocus}
             Here is the conversation history of past {ncon} conversations: {last_three_convos}, use this very wisely to extract the best out of them and then follow the goal and focus to guide the user further
            If you recieve nothing as goal and focus that means convessation has just started shaping
            Based on user current input, the current topic and goal, and the RAG output, provide a response. It could be anything, maybe a question a follow up you've to carefully decide on that
            Also at the end, always end with this
            "Also, here is something you will surely like, only for you"
        """

        response = llm.invoke(main_context)
        bot_reply = response.content


        new_interaction = [{
             "human": user_input,
             "ai": bot_reply
        }]
        
        with open(files['history'], 'a', encoding='utf-8') as f:
            # Verify if your extract_chats expects a list of lists or just objects per line
            json.dump(new_interaction, f) 
            f.write('\n') 

        search_query = f'''Suggest some stories,podacsts, videos, blogs 
        This is your list of user history based on his current question {user_input} and also the current response as generated by another LLM: {response}. Now based on this you need to figure if even it is necessary to give any resources. 
        If really necessary and find high quality, very good resources otherwise just output a very very good quote of the day in the format
        "Quote of the day: <quote>" 
        '''
    
        search_results = []
        try:
             search = perplexity_client.search.create(
                query=search_query,
                max_results=2
             )
             for result in search.results:
                 search_results.append({"title": result.title, "url": result.url})
        except Exception as e:
            print(f"Perplexity search failed: {e}")

        return {
            "bot_reply": bot_reply,
            "resources": search_results,
            "current_focus": parsed_json if 'parsed_json' in locals() else None
        }

    except Exception as e:
        # This ensures if something crashes, the frontend gets an error message
        # instead of just timing out.
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Standard boilerplate to run locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)






# # main.py
# import os
# from langchain.memory import ConversationBufferMemory
# from perplexity import Perplexity
# import json
# from groq import Groq
# from input_to_llm import extract_chats, extract_goalfocus
# from utils import (
#     load_user_data,
#     initialize_rag,
#     classify_input,
#     get_rag_response,
#     llm
# )
# from configure import USER_DATA_PATH, llm_prompt

# PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# def main():
#     # Load user data

#     # with open("categories.json", 'r') as f:
#     #     categories = json.load(f)

#     user_data = load_user_data()

#     username = "sameer"  #in production extract the username from the user_data json file
#     # Initialize RAG
#     print("Initializing knowledge base...")
#     # qa_chains = initialize_rag()
#     print("Knowledge base ready!")
    
#     # Start conversation
#     memory = ConversationBufferMemory()
#     print(f"\nHi {username}, I am Sattva, how can I help you today?")
    
#     client = Perplexity(api_key=PERPLEXITY_API_KEY)
#     while True:
#         user_input = input("\nYou: ")

#         if user_input.lower() == "exit":
#             print("Goodbye! Your progress has been saved.")
#             break



#         #calcualting the focus and goals for the user by the LLM
#         ncon = 3
#         last_three_convos = extract_chats("chat_history.jsonl")
#         prev_goalandfocus = extract_goalfocus("focus_goal.jsonl")
#         context = f'''
#         Ohk, so you are an expert in navigating paths through human conversations. So, let's say if someone is telling you about how they are feeling, what they did
#         what other people did to them, what are their problems, what are their goals and aspirations in life and all that stuff.
#         Now based on all the above information, you need to figure that as a teacher/Guru (which you are for the person) 
#         what should be the topic (or the broad thing that is going on currently as a part of discussion - it could discussion about office, or marriage or house problems or anything) you've to figure this out from based on previous converstaion history.
#         At the same time, you have to ask/suggest/recommend further to the person as well right. So for that you have to define a goal (that is basically what should be the exact next step in this conversation - should you be asking a quuestion or should be recommending something or maybe just chatting normally). again this also you've to decide. But goal has to be something which defines the next step
#         whereas topic is something which is broad and overall defines what is going on in the converstaion.
#         Your response format should be like this:
#         "Topic":" <topic> ",
#         "Goal":" <goal> "

#         Don't output anything else other than this format.
#         Here is the conversation history of past {ncon} conversations: {last_three_convos}
#         also, here;s the current user question: {user_input}
#         You can also look upon what was the topic and goal defined just previously to get better idea.
#         previous topic and goal : {prev_goalandfocus}
#         Try updating goal on each instance but topic can remain same if the converstaion is still revolving around the same thing. Because obviusly you've to dig deeper with the user, you can't be doing the same thign in the goal
#         ALso, if the user isn't talking anymore about the previous topic, you can change the topic as well. Thats why i am providin gyou the previous focus and goal
#         '''

#         response = llm.invoke(context)
#         json_string_to_parse = "{" + response.content+ "}"
#         parsed_json = json.loads(json_string_to_parse)
#         output_filename = "focus_goal.jsonl"
#         with open(output_filename, 'a', encoding='utf-8') as f:
#             json.dump([parsed_json], f)
#             f.write('\n')
#         # print(response.content)




#         goalandfocus = extract_goalfocus("focus_goal.jsonl")
#         # response = llm.invoke(user_input)
#         # rag = get_rag_response(user_input, qa_chains)
#             # here's the RAG output: {rag}
#         context = f"""
#             User Context:
#             - Name: {username}
            
#             Conversation History:
#             {memory.load_memory_variables({})['history']}
            
#             Current Query: {user_input}
            
#             Provide a helpful, supportive response.
#             There's a lot of data avaiable and we have run rag on the data to get the best possible answer:
#             utilise this to give the answer
#             Also, at each step we are determining the topic and goal of the conversation to give a proper direction to the chats. This is to help you (who is acting as a guru to the user)
#             to guide him better
#             goal is something which defines the next step which you should be taking in the converstaion, don't very rigidly follow it but try to take the direction from it
#             whereas topic is something which is broad and overall defines what is going on in the converstaion
#             here's the current topic and goal : {goalandfocus}
#             If you recieve nothing as goal and focus that means convessation has just started shaping
#             Based on user current input, the current topic and goal, and the RAG output, provide a response. It could be anything, maybe a question a follow up you've to carefully decide on that
#             Also at the end, always end with this
#             "Also, here is something you will surely like, only for you"
#             """
#         response = llm.invoke(context)

#         #     response = llm.invoke(context)
#         #     print(f"\nSatva: {response.content}")
#         # Classify input
#         # input_type = classify_input(user_input)
#         # print(input_type)
#         # if input_type == "question":
#         #     # Get RAG response with advice-focused format
#         #     response = get_rag_response(user_input, qa_chains)
#         #     print(f"\nSatva: {response}")
#         # else:
#         #     # General conversation
#         #     context = f"""
#         #     User Context:
#         #     - Name: {username}
            
#         #     Conversation History:
#         #     {memory.load_memory_variables({})['history']}
            
#         #     Current Query: {user_input}
            
#         #     Provide a helpful, supportive response.
#         #     Also at the end, always end with this
#         #     "Also, here is something you will surely like, only for you"
#         #     """

#         #     response = llm.invoke(context)
#         #     print(f"\nSatva: {response.content}")

#         memory.save_context({"input": user_input}, {"output": response.content})
#         # print(memory.chat_memory.messages)

#         history = []
#         raw_messages = memory.chat_memory.messages[-2:]
#         history.append({
#                 f"{raw_messages[0].type}": raw_messages[0].content,
#                 f"{raw_messages[1].type}": raw_messages[1].content
#         })

#         output_filename = "chat_history.jsonl"
#         with open(output_filename, 'a', encoding='utf-8') as f:
#             json.dump(history, f, indent=4)
        
#         print(f"\nSatva: {response.content}")

#         search = client.search.create(
#         query= f'''Suggest some stories,podacsts, videos, blogs 
#         This is your list of user history {memory.load_memory_variables({})['history']} and based on his current question {user_input} and also the current response as generated by another LLM: {response}. Now based on this you need to figure if even it is necessary to give any resources. 
#         If really necessary and find high quality, very good resources otherwise just output a very very good quote of the day in the format
#         "Quote of the day: <quote>" ''',
#         max_results=2
#         )

#         for result in search.results:
#             print(f"{result.title}: {result.url}")

# if __name__ == "__main__":
#     main()




    

# import os
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from langchain.memory import ConversationBufferMemory
# from perplexity import Perplexity
# from dotenv import load_dotenv

# from utils import (
#     initialize_rag,
#     classify_input,
#     get_rag_response,
#     llm
# )

# # --- 1. One-Time Application Setup ---

# # Load environment variables from .env file
# load_dotenv()
# PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# if not PERPLEXITY_API_KEY:
#     raise ValueError("PERPLEXITY_API_KEY not found in environment variables.")

# # Initialize the FastAPI app
# app = FastAPI(
#     title="Satva RAG API",
#     description="An API for conversational AI and RAG-based Q&A."
# )

# # Initialize models and services once on startup
# print("Initializing knowledge base... (This may take a moment)")
# qa_chains = initialize_rag()
# print("Knowledge base ready!")

# perplexity_client = Perplexity(api_key=PERPLEXITY_API_KEY)

# # In-memory store for conversations (for demonstration purposes)
# # For production, replace this with a persistent store like Redis.
# conversation_memories = {}


# # --- 2. Define API Request and Response Models ---

# class ChatRequest(BaseModel):
#     user_id: str
#     message: str

# class Link(BaseModel):
#     title: str
#     url: str

# class ChatResponse(BaseModel):
#     response_text: str
#     source: str # "rag" or "general_conversation"
#     recommended_links: list[Link] = []
#     quote_of_the_day: str | None = None


# # --- 3. Define API Endpoints ---

# @app.get("/", tags=["Health Check"])
# def read_root():
#     return {"status": "ok", "message": "Welcome to the Satva API"}

# @app.post("/chat", response_model=ChatResponse, tags=["Conversation"])
# async def handle_chat(request: ChatRequest):
#     """
#     Handles a user's message, classifies it, and provides a response.
#     """
#     user_id = request.user_id
#     user_input = request.message

#     # Get or create conversation memory for the user
#     if user_id not in conversation_memories:
#         conversation_memories[user_id] = ConversationBufferMemory()
#     memory = conversation_memories[user_id]

#     # Classify the input to decide the logic path
#     input_type = classify_input(user_input)
    
#     if input_type == "question":
#         # Get RAG response for questions
#         rag_response = get_rag_response(user_input, qa_chains)
#         memory.save_context({"input": user_input}, {"output": rag_response})
        
#         return ChatResponse(
#             response_text=rag_response,
#             source="rag"
#         )
#     else:
#         # Handle general conversation
#         history = memory.load_memory_variables({})['history']
#         context = f"""
#         User Context:
#         - Name: {user_id}
        
#         Conversation History:
#         {history}
        
#         Current Query: {user_input}
        
#         Provide a helpful, supportive response.
#         Also at the end, always end with this
#         "Also, here is something you will surely like, only for you"
#         """
        
#         llm_response = llm.invoke(context)
#         response_text = llm_response.content
        
#         # Use Perplexity AI for curated content search
#         search_query = f"""
#         Based on the user's recent message "{user_input}" and our conversation history, suggest 2 highly relevant, high-quality resources (stories, podcasts, videos, blogs) that could be helpful.
#         If no high-quality resources are found, just output a single, very good, inspirational quote of the day in the format "Quote of the day: <quote>"
#         """
        
#         search = perplexity_client.search.create(
#             query=search_query,
#             max_results=2
#         )
        
#         links = []
#         quote = None
#         for result in search.results:
#             if "Quote of the day" in result.title:
#                 quote = result.title
#             else:
#                 links.append(Link(title=result.title, url=result.url))
        
#         memory.save_context({"input": user_input}, {"output": response_text})

#         return ChatResponse(
#             response_text=response_text,
#             source="general_conversation",
#             recommended_links=links,
#             quote_of_the_day=quote
#         )
