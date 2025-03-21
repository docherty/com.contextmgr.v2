import streamlit as st
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import config early to avoid import issues
from src.config import config

# Lazy initialization for components
_planner = None
_vector_store = None

def get_planner():
    """Lazily initialize the planner only when needed"""
    global _planner
    if _planner is None:
        from src.core.planner import ProjectPlanner
        _planner = ProjectPlanner()
    return _planner

def get_vector_store():
    """Lazily initialize the vector store only when needed"""
    global _vector_store
    if _vector_store is None:
        from src.storage.vector_store import ContextVectorStore
        _vector_store = ContextVectorStore()
    return _vector_store

# Set up the Streamlit page
st.set_page_config(
    page_title="ContextMgr",
    page_icon="🧠",
    layout="wide"
)

st.title("AI Context Manager")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Project Planning", "Context Search", "Settings"])

# Function to safely run async functions in Streamlit
def run_async(async_func, *args, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(async_func(*args, **kwargs))
    loop.close()
    return result

if page == "Project Planning":
    st.header("Generate Development Plan")
    
    with st.form("plan_form"):
        project_description = st.text_area(
            "Project Description", 
            height=200,
            placeholder="Describe your project or development task..."
        )
        submitted = st.form_submit_button("Generate Plan")
        
        if submitted and project_description:
            with st.spinner("Generating plan..."):
                # Initialize components only when needed
                planner = get_planner()
                vector_store = get_vector_store()
                
                # Use the safe async runner
                plan_result = run_async(planner.generate_plan, project_description)
                
                st.success("Plan generated!")
                
                # Display the plan
                st.markdown(plan_result["plan"])
                
                # Save to context
                run_async(vector_store.add_context, 
                    plan_result["plan"],
                    {"type": "plan", "path": plan_result["path"]}
                )

elif page == "Context Search":
    st.header("Search Development Context")
    
    query = st.text_input("Search query")
    
    if query:
        with st.spinner("Searching..."):
            # Initialize vector store only when needed
            vector_store = get_vector_store()
            
            # Search the vector store
            results = run_async(vector_store.search_context, query)
            
            # Display results
            for i, doc in enumerate(results):
                with st.expander(f"Result {i+1}"):
                    st.markdown(doc.page_content)
                    st.json(doc.metadata)

elif page == "Settings":
    st.header("Settings")
    
    st.subheader("Model Configuration")
    
    # Simple model selection UI
    st.selectbox(
        "Planner Model",
        ["local-llama3", "local-mistral", "gpt-4o", "claude-3-opus"],
        index=0
    )
    
    st.selectbox(
        "Coder Model",
        ["local-codellama", "local-llama3", "claude-3-opus", "gpt-4o"],
        index=0
    )
    
    st.selectbox(
        "Reviewer Model",
        ["local-codellama", "local-llama3", "gpt-4o", "claude-3-opus"],
        index=0
    )
    
    # Update to show Chroma DB location
    st.subheader("Storage Settings")
    st.text("Chroma database location: " + str(config.PATHS["vector_store"] / "chroma_db"))