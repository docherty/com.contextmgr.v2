import os
from datetime import datetime
from src.config import config
from src.models.router import ModelRouter

class ProjectPlanner:
    def __init__(self):
        self.model_router = ModelRouter()
    
    async def generate_plan(self, project_description: str):
        """Generate a new development plan from user requirements"""
        prompt = f"""
        Create a detailed development plan for the following project:
        
        {project_description}
        
        Provide the plan in markdown format with the following sections:
        
        # Project Overview
        
        # Architecture
        
        # Development Phases
        
        ## Phase 1: [Name]
        - [ ] Task 1
        - [ ] Task 2
        
        ## Phase 2: [Name]
        - [ ] Task 1
        - [ ] Task 2
        """
        
        # Changed from execute_prompt to generate_response
        response = await self.model_router.generate_response("planner", prompt)
        
        # Save plan to file
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        plan_path = config.PATHS["plans"] / f"plan-{timestamp}.md"
        
        # Adjust the response handling as generate_response returns a string, not an object
        with open(plan_path, "w") as f:
            f.write(response)
        
        return {
            "plan": response,
            "path": str(plan_path)
        }