import streamlit as st
import asyncio
from src.core.planner import ProjectPlanner
from src.storage.vector_store import ContextVectorStore

# Initialize components
planner = ProjectPlanner()
vector_store = ContextVectorStore()

# Set up the Streamlit page
st.set_page_config(
    page_title="AI Context Manager",
    page_icon="🧠",
    layout="wide"
)

st.title("AI Context Manager")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Project Planning", "Context Search", "Settings"])

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
                # Run the async function in a non-async context
                loop = asyncio.new_event_loop()
                plan_result = loop.run_until_complete(planner.generate_plan(project_description))
                loop.close()
                
                st.success("Plan generated!")
                
                # Display the plan
                st.markdown(plan_result["plan"])
                
                # Save to context
                loop = asyncio.new_event_loop()
                loop.run_until_complete(vector_store.add_context(
                    plan_result["plan"],
                    {"type": "plan", "path": plan_result["path"]}
                ))
                loop.close()

elif page == "Context Search":
    st.header("Search Development Context")
    
    query = st.text_input("Search query")
    
    if query:
        with st.spinner("Searching..."):
            # Search the vector store
            loop = asyncio.new_event_loop()
            results = loop.run_until_complete(vector_store.search_context(query))
            loop.close()
            
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
    
    # Placeholder for future settings
    st.subheader("Storage Settings")
    st.text("SQLite database location: " + str(config.PATHS["vector_store"] / "context.db"))