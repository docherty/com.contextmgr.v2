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

st.title("ContextMgr")

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

# Initialize session state for multi-step workflow
if "workflow_step" not in st.session_state:
    st.session_state.workflow_step = 1  # 1: Initial brief, 2: Clarification, 3: Final brief, 4: Work packages

if "project_description" not in st.session_state:
    st.session_state.project_description = ""
    
if "clarification_questions" not in st.session_state:
    st.session_state.clarification_questions = []
    
if "clarification_answers" not in st.session_state:
    st.session_state.clarification_answers = {}
    
if "refined_brief" not in st.session_state:
    st.session_state.refined_brief = ""
    
if "work_packages" not in st.session_state:
    st.session_state.work_packages = []

if "loading_state" not in st.session_state:
    st.session_state.loading_state = False

# Helper functions for workflow navigation
def go_to_clarification():
    st.session_state.loading_state = True
    st.rerun()

def process_clarification():
    planner = get_planner()
    questions = run_async(planner.generate_clarification_questions, 
                         st.session_state.project_description)
    st.session_state.clarification_questions = questions
    st.session_state.workflow_step = 2
    st.session_state.loading_state = False
    
def go_to_refined_brief():
    st.session_state.loading_state = True
    st.rerun()

def process_refined_brief():
    planner = get_planner()
    refined = run_async(planner.generate_refined_brief, 
                       st.session_state.project_description,
                       st.session_state.clarification_answers)
    st.session_state.refined_brief = refined
    st.session_state.workflow_step = 3
    st.session_state.loading_state = False
    
def go_to_work_packages():
    st.session_state.loading_state = True
    st.rerun()

def process_work_packages():
    planner = get_planner()
    plan_result = run_async(planner.generate_plan, 
                           st.session_state.refined_brief)
    st.session_state.work_packages = plan_result
    st.session_state.workflow_step = 4
    st.session_state.loading_state = False
    
def reset_workflow():
    st.session_state.workflow_step = 1
    st.session_state.project_description = ""
    st.session_state.clarification_questions = []
    st.session_state.clarification_answers = {}
    st.session_state.refined_brief = ""
    st.session_state.work_packages = []
    st.session_state.loading_state = False

# Process any loading state actions
if st.session_state.loading_state:
    if st.session_state.workflow_step == 1:
        process_clarification()
    elif st.session_state.workflow_step == 2:
        process_refined_brief()
    elif st.session_state.workflow_step == 3:
        process_work_packages()

# Display workflow progress indicators
if page == "Project Planning":
    # Create progress indicator
    steps = ["Initial Brief", "Clarify Requirements", "Review Brief", "Development Plan"]
    current_step = st.session_state.workflow_step
    
    cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        with cols[i]:
            if i + 1 < current_step:
                st.markdown(f"#### ✅ {step}")
            elif i + 1 == current_step:
                st.markdown(f"#### 🔵 {step}")
            else:
                st.markdown(f"#### ⚪ {step}")
    
    st.progress((current_step - 1) / (len(steps) - 1))
    
    # If in loading state, show appropriate spinner and don't render the rest of the UI
    should_continue = True
    if st.session_state.loading_state:
        spinner_text = {
            1: "Analyzing your request and preparing clarifying questions...",
            2: "Refining your brief based on clarifications...",
            3: "Generating detailed development plan..."
        }.get(current_step, "Processing...")
        
        with st.spinner(spinner_text):
            st.markdown(f"### {spinner_text}")
            st.empty()  # Force the spinner to show
            should_continue = False  # Skip the rest of the UI while loading
    
    # Only continue rendering the UI if not in loading state
    if should_continue:
        # Step 1: Initial brief input
        if st.session_state.workflow_step == 1:
            st.header("Describe Your Project")
            
            project_description = st.text_area(
                "Project Description", 
                height=200,
                placeholder="Describe your project or development task in a few sentences..."
            )
            
            if st.button("Next: Clarify Requirements"):
                if project_description:
                    st.session_state.project_description = project_description
                    go_to_clarification()
        
        # Step 2: Clarification questions
        elif st.session_state.workflow_step == 2:
            st.header("Let's Clarify Your Requirements")
            
            # Display all questions with their inputs
            for i, question in enumerate(st.session_state.clarification_questions):
                if question["type"] == "yes_no":
                    answer = st.radio(
                        question["question"],
                        options=["Yes", "No"],
                        key=f"q_{i}"
                    )
                    st.session_state.clarification_answers[question["id"]] = answer
                    
                elif question["type"] == "multiple_choice":
                    answer = st.selectbox(
                        question["question"],
                        options=question["options"],
                        key=f"q_{i}"
                    )
                    st.session_state.clarification_answers[question["id"]] = answer
                    
                elif question["type"] == "text":
                    answer = st.text_input(
                        question["question"],
                        key=f"q_{i}"
                    )
                    st.session_state.clarification_answers[question["id"]] = answer
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Back to Project Description", type="secondary"):
                    st.session_state.workflow_step = 1
                    
            with col2:
                if st.button("Next: Review Brief"):
                    go_to_refined_brief()
        
        # Step 3: Refined brief
        elif st.session_state.workflow_step == 3:
            st.header("Review Your Project Brief")
            
            refined_brief = st.text_area(
                "Edit your project brief as needed",
                value=st.session_state.refined_brief,
                height=300
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Back to Clarifications", type="secondary"):
                    st.session_state.workflow_step = 2
                    
            with col2:
                if st.button("Generate Development Plan"):
                    st.session_state.refined_brief = refined_brief
                    go_to_work_packages()
        
        # Step 4: Work packages and tasks
        elif st.session_state.workflow_step == 4:
            st.header("Development Plan")
            
            # Display work packages
            if st.session_state.work_packages:
                # Save to context
                vector_store = get_vector_store()
                if "path" in st.session_state.work_packages:
                    run_async(vector_store.add_context, 
                        st.session_state.work_packages["plan"],
                        {"type": "plan", "path": st.session_state.work_packages["path"]}
                    )
                
                tabs = st.tabs(["Overview", "Work Packages"])
                
                with tabs[0]:
                    st.markdown(st.session_state.work_packages["overview"])
                
                with tabs[1]:
                    # Display editable work packages
                    for i, wp in enumerate(st.session_state.work_packages["work_packages"]):
                        with st.expander(f"WP{i+1:03d}: {wp['title']}", expanded=True):
                            # Edit work package title
                            new_title = st.text_input(
                                "Work Package Title", 
                                value=wp["title"], 
                                key=f"wp_title_{i}"
                            )
                            st.session_state.work_packages["work_packages"][i]["title"] = new_title
                            
                            # Add up/down buttons for reordering
                            col1, col2, col3 = st.columns([1, 1, 8])
                            if i > 0 and col1.button("↑", key=f"up_{i}"):
                                # Move work package up
                                wp_item = st.session_state.work_packages["work_packages"].pop(i)
                                st.session_state.work_packages["work_packages"].insert(i-1, wp_item)
                                st.rerun()
                            
                            if i < len(st.session_state.work_packages["work_packages"])-1 and col2.button("↓", key=f"down_{i}"):
                                # Move work package down
                                wp_item = st.session_state.work_packages["work_packages"].pop(i)
                                st.session_state.work_packages["work_packages"].insert(i+1, wp_item)
                                st.rerun()
                            
                            # Tasks for this work package
                            st.markdown("#### Tasks:")
                            for j, task in enumerate(wp["tasks"]):
                                task_col1, task_col2, task_col3, task_col4 = st.columns([1, 1, 10, 1])
                                
                                # Task ID
                                task_col1.text(f"WP{i+1:03d}-{chr(65+j)}")
                                
                                # Up/down for task
                                if j > 0 and task_col2.button("↑", key=f"t_up_{i}_{j}"):
                                    t_item = st.session_state.work_packages["work_packages"][i]["tasks"].pop(j)
                                    st.session_state.work_packages["work_packages"][i]["tasks"].insert(j-1, t_item)
                                    st.rerun()
                                
                                if j < len(wp["tasks"])-1 and task_col2.button("↓", key=f"t_down_{i}_{j}"):
                                    t_item = st.session_state.work_packages["work_packages"][i]["tasks"].pop(j)
                                    st.session_state.work_packages["work_packages"][i]["tasks"].insert(j+1, t_item)
                                    st.rerun()
                                
                                # Edit task description
                                new_task = task_col3.text_input(
                                    "", 
                                    value=task, 
                                    label_visibility="collapsed",
                                    key=f"task_{i}_{j}"
                                )
                                st.session_state.work_packages["work_packages"][i]["tasks"][j] = new_task
                                
                                # Delete button for task
                                if task_col4.button("❌", key=f"del_task_{i}_{j}"):
                                    st.session_state.work_packages["work_packages"][i]["tasks"].pop(j)
                                    st.rerun()
                            
                            # Add new task button
                            if st.button("+ Add Task", key=f"add_task_{i}"):
                                st.session_state.work_packages["work_packages"][i]["tasks"].append("New task")
                                st.rerun()
                    
                    # Add new work package button
                    if st.button("+ Add Work Package"):
                        st.session_state.work_packages["work_packages"].append({
                            "title": "New Work Package",
                            "tasks": ["Task 1"]
                        })
                        st.rerun()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        # Export plan button
                        if st.download_button(
                            "Export Plan", 
                            data=st.session_state.work_packages["plan"],
                            file_name="development_plan.md",
                            mime="text/markdown"
                        ):
                            pass
                    
                    with col2:
                        # Start new project button
                        if st.button("Start New Project"):
                            reset_workflow()
            
            # Option to go back and edit the brief
            st.button("Back to Brief", type="secondary", on_click=lambda: setattr(st.session_state, 'workflow_step', 3))

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