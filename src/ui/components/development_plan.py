import streamlit as st

def update_plan_markdown():
    """Update the markdown plan based on current work packages"""
    if not st.session_state.work_packages:
        return
    
    md_content = "# Development Plan\n\n"
    
    # Add overview section
    if "overview" in st.session_state.work_packages:
        md_content += st.session_state.work_packages["overview"]
    
    md_content += "\n\n# Work Packages\n\n"
    
    # Add work packages
    for i, wp in enumerate(st.session_state.work_packages["work_packages"]):
        md_content += f"## WP{i+1:03d}: {wp['title']}\n\n"
        for j, task in enumerate(wp["tasks"]):
            md_content += f"- [ ] WP{i+1:03d}-{chr(65+j)}: {task}\n"
        md_content += "\n"
    
    # Update the plan in session state
    st.session_state.work_packages["plan"] = md_content
    
    # If we have a path, write to file
    if "path" in st.session_state.work_packages and st.session_state.work_packages["path"]:
        try:
            with open(st.session_state.work_packages["path"], "w") as f:
                f.write(md_content)
        except Exception as e:
            st.error(f"Failed to save plan to file: {e}")

def display_work_packages():
    if not st.session_state.work_packages:
        return
    
    # Initialize the editing state if not already present
    if "editing_wp" not in st.session_state:
        st.session_state.editing_wp = None  # Format: (wp_index, None) or None
    if "editing_task" not in st.session_state:
        st.session_state.editing_task = None  # Format: (wp_index, task_index) or None
    
    for i, wp in enumerate(st.session_state.work_packages["work_packages"]):
        with st.container():
            col1, col2, col3 = st.columns([0.05, 0.85, 0.1])
            
            # Handle work package title editing
            with col1:
                st.write("☰")  # Drag handle representation
            
            with col2:
                if st.session_state.editing_wp == i:
                    new_title = st.text_input(
                        f"Edit WP{i+1:03d} Title",
                        value=wp["title"],
                        key=f"edit_wp_title_{i}"
                    )
                else:
                    st.subheader(f"WP{i+1:03d}: {wp['title']}")
            
            with col3:
                if st.session_state.editing_wp == i:
                    if st.button("Save", key=f"save_wp_{i}"):
                        st.session_state.work_packages["work_packages"][i]["title"] = new_title
                        st.session_state.editing_wp = None
                        update_plan_markdown()
                        st.rerun()
                    if st.button("Cancel", key=f"cancel_wp_{i}"):
                        st.session_state.editing_wp = None
                        st.rerun()
                else:
                    col3_1, col3_2 = st.columns(2)
                    with col3_1:
                        if st.button("✏️", key=f"edit_wp_{i}"):
                            st.session_state.editing_wp = i
                            st.rerun()
                    with col3_2:
                        if st.button("🗑️", key=f"delete_wp_{i}"):
                            if i < len(st.session_state.work_packages["work_packages"]):
                                st.session_state.work_packages["work_packages"].pop(i)
                                # Update the markdown plan
                                update_plan_markdown()
                                st.rerun()
            
            # Display tasks for this work package
            for j, task in enumerate(wp["tasks"]):
                with st.container():
                    task_col1, task_col2, task_col3 = st.columns([0.05, 0.85, 0.1])
                    
                    with task_col1:
                        st.write("⋮")  # Task drag handle representation
                    
                    with task_col2:
                        if st.session_state.editing_task == (i, j):
                            new_task = st.text_input(
                                f"Edit task WP{i+1:03d}-{chr(65+j)}",
                                value=task,
                                key=f"edit_task_{i}_{j}"
                            )
                        else:
                            st.write(f"WP{i+1:03d}-{chr(65+j)}: {task}")
                    
                    with task_col3:
                        if st.session_state.editing_task == (i, j):
                            if st.button("Save", key=f"save_task_{i}_{j}"):
                                st.session_state.work_packages["work_packages"][i]["tasks"][j] = new_task
                                st.session_state.editing_task = None
                                # Update the markdown plan
                                update_plan_markdown()
                                st.rerun()
                            if st.button("Cancel", key=f"cancel_task_{i}_{j}"):
                                st.session_state.editing_task = None
                                st.rerun()
                        else:
                            task_col3_1, task_col3_2 = st.columns(2)
                            with task_col3_1:
                                if st.button("✏️", key=f"edit_task_{i}_{j}"):
                                    st.session_state.editing_task = (i, j)
                                    st.rerun()
                            with task_col3_2:
                                if st.button("🗑️", key=f"delete_task_{i}_{j}"):
                                    if j < len(st.session_state.work_packages["work_packages"][i]["tasks"]):
                                        st.session_state.work_packages["work_packages"][i]["tasks"].pop(j)
                                        # Update the markdown plan
                                        update_plan_markdown()
                                        st.rerun()
            
            # Add task button
            if st.button("+ Add Task", key=f"add_task_{i}"):
                st.session_state.work_packages["work_packages"][i]["tasks"].append("New task")
                # Update the markdown plan
                update_plan_markdown()
                st.rerun()
            
            st.divider()
    
    # Add work package button
    if st.button("+ Add Work Package"):
        st.session_state.work_packages["work_packages"].append({
            "title": "New Work Package",
            "tasks": ["Task 1"]
        })
        # Update the markdown plan
        update_plan_markdown()
        st.rerun()