import os
import git
from pathlib import Path
from typing import List, Dict, Optional

class CodebaseManager:
    """Manages access to local codebases with future remote hosting in mind"""
    
    def __init__(self, workspace_dir: str = None):
        """Initialize with a workspace directory"""
        self.workspace_dir = workspace_dir or os.path.expanduser("~/ai-context-workspaces")
        os.makedirs(self.workspace_dir, exist_ok=True)
        
    def list_workspaces(self) -> List[Dict]:
        """List available workspaces (Git repositories)"""
        workspaces = []
        for item in os.listdir(self.workspace_dir):
            path = os.path.join(self.workspace_dir, item)
            if os.path.isdir(path) and os.path.exists(os.path.join(path, ".git")):
                # It's a git repository
                try:
                    repo = git.Repo(path)
                    workspaces.append({
                        "name": item,
                        "path": path,
                        "active_branch": repo.active_branch.name,
                        "modified": len(repo.index.diff(None)) > 0
                    })
                except git.InvalidGitRepositoryError:
                    # Not a valid git repo
                    pass
        return workspaces
    
    def open_workspace(self, name: str) -> Dict:
        """Open a specific workspace"""
        path = os.path.join(self.workspace_dir, name)
        if not os.path.exists(path):
            raise ValueError(f"Workspace {name} does not exist")
        
        return {
            "name": name,
            "files": self._list_files(path),
            "path": path
        }
    
    def _list_files(self, directory: str) -> List[Dict]:
        """List files in a directory with metadata"""
        files = []
        for root, dirs, filenames in os.walk(directory):
            # Skip .git directory
            if ".git" in dirs:
                dirs.remove(".git")
            
            rel_path = os.path.relpath(root, directory)
            if rel_path == ".":
                rel_path = ""
                
            for filename in filenames:
                full_path = os.path.join(root, filename)
                files.append({
                    "name": filename,
                    "path": os.path.join(rel_path, filename) if rel_path else filename,
                    "full_path": full_path,
                    "size": os.path.getsize(full_path),
                    "modified": os.path.getmtime(full_path)
                })
        return files
    
    def read_file(self, workspace: str, file_path: str) -> str:
        """Read contents of a file in a workspace"""
        full_path = os.path.join(self.workspace_dir, workspace, file_path)
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            raise ValueError(f"File {file_path} does not exist in workspace {workspace}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_file(self, workspace: str, file_path: str, content: str) -> bool:
        """Write contents to a file in a workspace"""
        full_path = os.path.join(self.workspace_dir, workspace, file_path)
        directory = os.path.dirname(full_path)
        
        # Create directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    
    def clone_repository(self, git_url: str, workspace_name: Optional[str] = None) -> Dict:
        """Clone a git repository into the workspace"""
        if not workspace_name:
            # Extract name from git URL
            workspace_name = git_url.split("/")[-1]
            if workspace_name.endswith(".git"):
                workspace_name = workspace_name[:-4]
        
        target_path = os.path.join(self.workspace_dir, workspace_name)
        if os.path.exists(target_path):
            raise ValueError(f"Workspace {workspace_name} already exists")
        
        # Clone the repository
        repo = git.Repo.clone_from(git_url, target_path)
        
        return {
            "name": workspace_name,
            "path": target_path,
            "active_branch": repo.active_branch.name
        }