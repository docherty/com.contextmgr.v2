import streamlit as st
import asyncio
import sys
import os
import json
from pathlib import Path

from src.ui.components.development_plan import display_work_packages
from src.ui.components.styling import add_custom_css

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

add_custom_css()

# Initialize project history in session state if not exists
if "project_history" not in st.session_state:
    # Try to load from file if exists
    history_file = config.PATHS["data"] / "project_history.json"
    if history_file.exists():
        try:
            with open(history_file, "r") as f:
                st.session_state.project_history = json.load(f)
        except:
            st.session_state.project_history = []
    else:
        st.session_state.project_history = []

if "current_project_id" not in st.session_state:
    st.session_state.current_project_id = None

# Function to save project history
def save_project_history():
    history_file = config.PATHS["data"] / "project_history.json"
    with open(history_file, "w") as f:
        json.dump(st.session_state.project_history, f)

# Function to add project to history
def add_project_to_history(project_name, plan_path, brief):
    import uuid
    project_id = str(uuid.uuid4())
    project = {
        "id": project_id,
        "name": project_name,
        "plan_path": plan_path,
        "brief": brief,
        "created_at": str(Path(plan_path).name).replace("plan-", "").replace(".md", "")
    }
    st.session_state.project_history.append(project)
    st.session_state.current_project_id = project_id
    save_project_history()
    return project_id

# Function to load project data
def load_project_data(project_id):
    for project in st.session_state.project_history:
        if project["id"] == project_id:
            # Load plan data
            plan_path = project["plan_path"]
            try:
                with open(plan_path, "r") as f:
                    plan_content = f.read()
                    
                # Set session state for the loaded project
                st.session_state.workflow_step = 4  # Go directly to work packages view
                st.session_state.refined_brief = project["brief"]
                
                # Parse the plan content to recreate work_packages structure
                planner = get_planner()
                plan_data = planner.parse_markdown_plan(plan_content)
                st.session_state.work_packages = plan_data
                st.session_state.current_project_id = project_id
                
                return True
            except Exception as e:
                st.error(f"Failed to load project: {str(e)}")
                return False
    return False

st.title("ContextMgr")

# Sidebar with project history
with st.sidebar:
    st.title("Projects")
    
    # Project history section (scrollable)
    st.subheader("Project History")
    
    # Create a container for the scrolling list
    history_container = st.container()
    with history_container:
        for project in st.session_state.project_history:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"{project['name']}", key=f"proj_{project['id']}"):
                    load_project_data(project['id'])
            with col2:
                st.caption(project['created_at'][0:8])
    
    # Navigation panel at the bottom (sticky)
    st.markdown("---")
    st.subheader("Navigation")
    page = st.radio("Go to", ["Project Planning", "Context Search", "Settings"])

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
    
    # Add project to history
    # Extract project name from the brief or use a default
    brief_lines = st.session_state.refined_brief.strip().split('\n')
    project_name = "Untitled Project"
    for line in brief_lines:
        if line.strip() and not line.startswith('#'):
            project_name = line.strip()[:40]
            break
    
    add_project_to_history(
        project_name,
        plan_result.get("path", ""),
        st.session_state.refined_brief
    )
    
def reset_workflow():
    st.session_state.workflow_step = 1
    st.session_state.project_description = ""
    st.session_state.clarification_questions = []
    st.session_state.clarification_answers = {}
    st.session_state.refined_brief = ""
    st.session_state.work_packages = []
    st.session_state.loading_state = False
    st.session_state.current_project_id = None

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
        
        # Step 4: Work packages and tasks with drag and drop
        elif st.session_state.workflow_step == 4:
            st.header("Development Plan")
            
            # Display work packages
            if st.session_state.work_packages:
                # Save to context
                vector_store = get_vector_store()
                if "path" in st.session_state.work_packages and st.session_state.work_packages["path"]:
                    run_async(vector_store.add_context, 
                        st.session_state.work_packages["plan"],
                        {"type": "plan", "path": st.session_state.work_packages["path"]}
                    )
                
                tabs = st.tabs(["Overview", "Work Packages"])
                
                with tabs[0]:
                    st.markdown(st.session_state.work_packages["overview"])
                
                # Inside your tabs[1] section (assuming work packages is the second tab)
                with tabs[1]:
                    display_work_packages()
                    
                    # Add export and new project buttons if needed
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.download_button(
                            "Export Plan", 
                            data=st.session_state.work_packages.get("plan", ""),
                            file_name="development_plan.md",
                            mime="text/markdown"
                        ):
                            pass
                    
                    with col2:
                        # Adjust this to match your actual reset function name
                        if st.button("Start New Project"):
                            if "reset_workflow" in locals() or "reset_workflow" in globals():
                                reset_workflow()
                            else:
                                st.warning("Reset function not found")
            
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
    
    # Management options
    st.subheader("Management")
    if st.button("Clear Project History"):
        st.session_state.project_history = []
        save_project_history()
        st.success("Project history cleared")
        st.rerun()

# Handle message passing from JavaScript
if st.session_state.workflow_step == 4:
    # Listen for reorder events using components.html
    st.components.v1.html("""
<script>
    // Listen for messages from parent
    window.addEventListener('message', function(event) {
        const data = event.data;
        
        if (data.type === 'reorderWorkPackages') {
            // Send to Streamlit
            window.parent.Streamlit.setComponentValue({
                type: 'reorderWorkPackages',
                order: data.order
            });
        } 
        else if (data.type === 'moveTask') {
            // Send to Streamlit
            window.parent.Streamlit.setComponentValue({
                type: 'moveTask',
                sourceWpId: data.sourceWpId,
                targetWpId: data.targetWpId,
                taskOrder: data.taskOrder,
                taskId: data.taskId
            });
        }
        else if (data.type === 'deleteWorkPackage') {
            // Send to Streamlit
            window.parent.Streamlit.setComponentValue({
                type: 'deleteWorkPackage',
                wpId: data.wpId
            });
        }
        else if (data.type === 'deleteTask') {
            // Send to Streamlit
            window.parent.Streamlit.setComponentValue({
                type: 'deleteTask',
                wpId: data.wpId,
                taskId: data.taskId
            });
        }
    });
</script>
""", height=0)