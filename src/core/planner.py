import os
import re
from datetime import datetime
from src.config import config
from src.models.router import ModelRouter

class ProjectPlanner:
    def __init__(self):
        self.model_router = ModelRouter()
    
    async def generate_clarification_questions(self, project_description: str):
        """Generate clarification questions based on the initial project description"""
        prompt = f"""
        Based on the following initial project description, generate a maximum of 5 important 
        clarification questions that would help refine the requirements. Format 
        each question as a JSON object with "id", "question", "type" (one of: "yes_no", 
        "multiple_choice", "text"), and for multiple_choice questions include an "options" array.
        
        Project Description:
        {project_description}
        
        Example output format:
        [
            {{
                "id": "target_platform",
                "question": "What platform will this project target?",
                "type": "multiple_choice",
                "options": ["Web", "Mobile", "Desktop", "All platforms"]
            }},
            {{
                "id": "technology_preference",
                "question": "Which technology do you prefer?",
                "options": ["Javascript", "Python", "No preference"]
            }},
            {{
                "id": "project_name",
                "question": "What do you want to call the project?",
                "type": "text"
            }},
            {{
                "id": "project_scope",
                "question": "Do you want to support VR devices?",
                "type": "yes_no"
            }}
        ]
        
        Generate appropriate questions that will help clarify the project requirements.
        """
        
        # Generate and parse the response
        response = await self.model_router.generate_response(
            "planner", 
            prompt,
            system_message="You are an expert project planner who helps refine project requirements."
        )
        
        # Parse the response as JSON
        import json
        try:
            # Find JSON content in the response
            start = response.find("[")
            end = response.rfind("]") + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            return []
        except json.JSONDecodeError:
            # If parsing fails, return empty list
            return []
    
    async def generate_refined_brief(self, project_description: str, clarification_answers: dict):
        """Generate a refined project brief based on the initial description and clarification answers"""
        
        # Format the clarification answers for the prompt
        answers_text = "\n".join([f"Q: {q_id}\nA: {answer}" for q_id, answer in clarification_answers.items()])
        
        prompt = f"""
        Based on the initial project description and the clarification answers provided,
        create a comprehensive and refined project brief. 
        
        Important: DO NOT include any preamble or phrases like "Here's a comprehensive brief" etc.
        Just write the actual brief content directly, as it will be presented to the user as-is.
        
        Initial Project Description:
        {project_description}
        
        Clarification Answers:
        {answers_text}
        
        Write a specific, detailed project brief that clearly defines scope, objectives, features, 
        and technical requirements.
        """
        
        # Generate the refined brief
        response = await self.model_router.generate_response(
            "planner", 
            prompt,
            system_message="You are an expert project requirements analyst who creates clear, comprehensive project briefs without any preamble text."
        )
        
        return response
    
    async def generate_plan(self, project_description: str):
        """Generate a new development plan from user requirements"""
        prompt = f"""
        Create a detailed development plan for the following project:
        
        {project_description}
        
        Return your response in the following JSON structure:
        {{
            "overview": "A markdown-formatted overview section with Solution Overview and Architecture subsections",
            "work_packages": [
                {{
                    "title": "Name of Work Package",
                    "tasks": [
                        "Task 1 description",
                        "Task 2 description",
                        ... more tasks
                    ]
                }},
                ... more work packages
            ]
        }}
        
        For the overview, include:
        1. A "Solution Overview" section describing the high-level approach
        2. An "Architecture" section outlining the technical architecture, components and how they interact
        
        For the work packages:
        1. Organize logically by feature area or development phase
        2. Break down each work package into specific, actionable tasks
        3. Ensure tasks are granular enough to be completed in 1-3 days
        """
        
        # Generate the plan with the new structure
        response = await self.model_router.generate_response("planner", prompt)
        
        # Parse the response as JSON
        import json
        try:
            # Find JSON content in the response
            start = response.find("{")
            end = response.rfind("}") + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                plan_data = json.loads(json_str)
                
                # Save plan to file
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                plan_path = config.PATHS["plans"] / f"plan-{timestamp}.md"
                
                # Create a markdown version for saving
                md_content = f"# Development Plan\n\n"
                md_content += plan_data["overview"]
                md_content += "\n\n# Work Packages\n\n"
                
                for i, wp in enumerate(plan_data["work_packages"]):
                    md_content += f"## WP{i+1:03d}: {wp['title']}\n\n"
                    for j, task in enumerate(wp["tasks"]):
                        md_content += f"- [ ] WP{i+1:03d}-{chr(65+j)}: {task}\n"
                    md_content += "\n"
                
                with open(plan_path, "w") as f:
                    f.write(md_content)
                
                # Return both the structured data and the markdown version
                return {
                    "overview": plan_data["overview"],
                    "work_packages": plan_data["work_packages"],
                    "plan": md_content,
                    "path": str(plan_path)
                }
            
            return {"overview": "Error parsing plan", "work_packages": [], "plan": "Error parsing plan"}
        except json.JSONDecodeError:
            # Fallback for parsing errors
            return {"overview": "Error parsing plan", "work_packages": [], "plan": response}
    
    def parse_markdown_plan(self, markdown_content: str):
        """Parse a markdown plan file back into the structured format"""
        # Extract overview section (everything between # Development Plan and # Work Packages)
        overview_match = re.search(r'# Development Plan\s+(.*?)\s+# Work Packages', 
                                  markdown_content, re.DOTALL)
        overview = overview_match.group(1).strip() if overview_match else ""
        
        # Extract work packages
        work_packages = []
        
        # Find all work package sections
        wp_sections = re.findall(r'## WP\d+: (.*?)(?=## WP\d+:|$)', markdown_content + "\n## WP999:", re.DOTALL)
        
        for wp_section in wp_sections:
            lines = wp_section.strip().split('\n')
            if not lines:
                continue
                
            title = lines[0].strip()
            tasks = []
            
            # Extract tasks
            for line in lines[1:]:
                task_match = re.search(r'- \[ \] WP\d+-[A-Z]: (.*)', line)
                if task_match:
                    tasks.append(task_match.group(1))
            
            work_packages.append({
                "title": title,
                "tasks": tasks
            })
        
        # Return in the same format as generate_plan
        return {
            "overview": overview,
            "work_packages": work_packages,
            "plan": markdown_content,
            "path": ""  # Will be filled in from history if available
        }