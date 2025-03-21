import streamlit as st
import os
from src.storage.file_manager import CodebaseManager

def render_file_explorer():
    """Render the file explorer component in Streamlit"""
    # Initialize the codebase manager
    if 'codebase_manager' not in st.session_state:
        st.session_state.codebase_manager = CodebaseManager()
    
    manager = st.session_state.codebase_manager
    
    # Sidebar for workspace selection
    st.sidebar.header("Workspaces")
    
    # Option to add a new workspace
    with st.sidebar.expander("Add Workspace"):
        col1, col2 = st.columns([1, 1])
        option = col1.selectbox("Method", ["Clone Git Repo", "Create New"])
        
        if option == "Clone Git Repo":
            repo_url = st.text_input("Git Repository URL")
            name = st.text_input("Workspace Name (optional)")
            if st.button("Clone Repository"):
                try:
                    manager.clone_repository(repo_url, name if name else None)
                    st.success("Repository cloned successfully!")
                except Exception as e:
                    st.error(f"Error cloning repository: {str(e)}")
        else:
            name = st.text_input("Workspace Name")
            if st.button("Create Workspace"):
                try:
                    # Create an empty directory
                    path = os.path.join(manager.workspace_dir, name)
                    os.makedirs(path, exist_ok=True)
                    # Initialize git repository
                    import git
                    git.Repo.init(path)
                    st.success("Workspace created successfully!")
                except Exception as e:
                    st.error(f"Error creating workspace: {str(e)}")
    
    # Display available workspaces
    workspaces = manager.list_workspaces()
    
    if not workspaces:
        st.sidebar.info("No workspaces available. Add one to get started.")
        return
    
    # Select workspace
    workspace_names = [w["name"] for w in workspaces]
    selected_workspace = st.sidebar.selectbox("Select Workspace", workspace_names)
    
    if not selected_workspace:
        return
    
    # Display workspace contents
    workspace = manager.open_workspace(selected_workspace)
    
    # Display files in a table
    st.header(f"Files in {selected_workspace}")
    
    # Simple filtering
    filter_text = st.text_input("Filter files", "")
    
    files = workspace["files"]
    if filter_text:
        files = [f for f in files if filter_text.lower() in f["path"].lower()]
    
    # Display as a table with clickable links
    if files:
        # Convert to a format suitable for display
        file_table = []
        for f in files:
            file_table.append({
                "File": f["path"],
                "Size (KB)": round(f["size"] / 1024, 2)
            })
        
        # Use a dataframe for display
        import pandas as pd
        df = pd.DataFrame(file_table)
        
        # Display the table
        selected_indices = st.data_editor(
            df,
            hide_index=True,
            use_container_width=True,
            disabled=True,
            key="file_table"
        )
        
        # Handle file selection
        if st.session_state.get('selected_file_index') is not None:
            selected_file = files[st.session_state.selected_file_index]
            st.session_state.current_file = selected_file
            
            # Display file content
            st.subheader(f"Editing: {selected_file['path']}")
            content = manager.read_file(selected_workspace, selected_file['path'])
            
            # Determine file type for syntax highlighting
            file_extension = os.path.splitext(selected_file['path'])[1].lower()
            if file_extension in ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json']:
                language = file_extension[1:]  # Remove the dot
            else:
                language = 'text'
            
            # File editor
            new_content = st.text_area(
                "File Content", 
                value=content, 
                height=500, 
                key=f"editor_{selected_file['path']}",
                help="Edit the file content"
            )
            
            # Save button
            if st.button("Save Changes"):
                try:
                    manager.write_file(selected_workspace, selected_file['path'], new_content)
                    st.success("File saved successfully!")
                except Exception as e:
                    st.error(f"Error saving file: {str(e)}")
    else:
        st.info("No files match your filter or the workspace is empty.")