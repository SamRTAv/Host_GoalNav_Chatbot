# utils.py
import os
import json
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from configure import USER_DATA_PATH, RAG_BASE_DIRECTORY, RAG_CATEGORIES
import shutil
from dotenv import load_dotenv



def LLMChunking():
    pass




# LLM setup
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=4000
)

# Text splitter
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ".", " ", ""],
    chunk_size=500,
    chunk_overlap=100,
    length_function=len
)
# text_splitter = LLMChunking()

# Embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Load user data
def load_user_data():
    try:
        if os.path.exists(USER_DATA_PATH) and os.path.getsize(USER_DATA_PATH) > 0:
            with open(USER_DATA_PATH, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {"users": {}, "user_info": {}}

# Save user data
def save_user_data(data):
    with open(USER_DATA_PATH, 'w') as f:
        json.dump(data, f, indent=2)

# Initialize RAG with per-category vector stores and QA chains
def initialize_rag():
    vector_stores = {}
    qa_chains = {}
    
    # Updated prompt template for advice-focused responses
    custom_prompt_template = """
    You are a {category} wellness expert. Provide helpful advice with specific actions:
    
    1. Start with a brief empathetic response to the user's concern
    2. Offer 1-3 actionable suggestions with brief explanations
    3. End with an open-ended question to continue conversation
    
    Guidelines:
    - Keep responses conversational and supportive
    - Avoid clinical jargon
    - Focus on practical, implementable advice
    - Maintain hopeful and encouraging tone
    
    Context:
    {context}
    
    Question: {question}
    """
    
    # Create vector stores and QA chains for each category
    # Assume all your variables like RAG_CATEGORIES, embeddings, llm, etc.
# are defined above this block.

    for category in RAG_CATEGORIES:
        persist_dir = f"./chroma_db_{category}"
        vector_store = None  # Initialize vector_store to None

        # --- 1. Check if Vector Store Already Exists ---
        if os.path.exists(persist_dir):
            print(f"Found existing vector store for {category}. Attempting to load...")
            try:
                # Load the existing vector store from disk
                vector_store = Chroma(
                    persist_directory=persist_dir,
                    embedding_function=embeddings  # Must provide the same embedding function
                )
                vector_stores[category] = vector_store
            except Exception as e:
                print(f"Error loading existing store {persist_dir}: {e}")
                print("Will delete and attempt to re-build.")
                shutil.rmtree(persist_dir)
        
        # --- 2. Create Vector Store if it Doesn't Exist (or failed to load) ---
        if vector_store is None: 
            print(f"No valid vector store for {category} found. Creating new one...")
            
            # Process documents (Your original logic)
            dir_path = os.path.join(RAG_BASE_DIRECTORY, category)
            docs = []
            if os.path.exists(dir_path):
                for filename in os.listdir(dir_path):
                    if filename.endswith('.txt'):
                        file_path = os.path.join(dir_path, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                text = f.read()
                            chunks = text_splitter.split_text(text)
                            for chunk in chunks:
                                if chunk.strip():
                                    metadata = {
                                        "source": filename,
                                        "category": category
                                    }
                                    docs.append(Document(
                                        page_content=chunk.strip(),
                                        metadata=metadata
                                    ))
                        except Exception as e:
                            print(f"Error processing {file_path}: {e}")
            
            # Create vector store (Your original logic)
            if docs:
                vector_store = Chroma.from_documents(
                    documents=docs,
                    embedding=embeddings,
                    persist_directory=persist_dir
                )
                vector_store.persist()
                vector_stores[category] = vector_store
                print(f"Created and persisted new vector store for {category} with {len(docs)} documents.")
            else:
                print(f"No documents found for {category}. Skipping QA chain setup.")
                continue  # Skip to the next category

        # --- 3. Create QA Chain (if vector_store was loaded or created) ---
        if vector_store:
            # Create QA chain with updated prompt
            prompt = PromptTemplate(
                template=custom_prompt_template.replace("{category}", category),
                input_variables=["context", "question"]
            )
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
                chain_type_kwargs={"prompt": prompt},
                return_source_documents=True
            )
            qa_chains[category] = qa_chain
            print(f"Initialized {category} QA chain.")

# The rest of your code
    return qa_chains

# Classify question to category
def classify_question_category(question):
    prompt = f"""
    Classify this question into one category: {', '.join(RAG_CATEGORIES)}
    Question: {question}
    Respond with only the category name.
    """
    response = llm.invoke(prompt)
    print(response)
    return response.content.strip()

# Get RAG response using category-specific QA chain
def get_rag_response(question, qa_chains):
    # Classify question
    category = classify_question_category(question)
    
    if category not in qa_chains:
        # Fallback to first available chain
        category = list(qa_chains.keys())[0]
    
    # Get response
    result = qa_chains[category].invoke({"query": question})
    return result['result']


# Classify user input
def classify_input(user_input):
    prompt = f"""
    Classify the following user input into one of these categories:
    1. "question" - If the user is asking a factual question that could be answered with knowledge
    2. "general" - If the user is just chatting or expressing feelings

    User Input: {user_input}

    Respond with only one word: either "question" or "general"
    """
    response = llm.invoke(prompt)
    return response.content.strip().lower()