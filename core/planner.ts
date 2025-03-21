import fs from 'fs';
import path from 'path';
import { config } from '../config';
import { ModelRouter } from '../models/router';

export class ProjectPlanner {
  private modelRouter: ModelRouter;
  
  constructor() {
    this.modelRouter = new ModelRouter();
    
    // Ensure plans directory exists
    if (!fs.existsSync(config.paths.plans)) {
      fs.mkdirSync(config.paths.plans, { recursive: true });
    }
  }
  
  /**
   * Generate a new development plan from user requirements
   */
  async generatePlan(projectDescription: string) {
    const prompt = `
      Create a detailed development plan for the following project:
      
      ${projectDescription}
      
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
    `;
    
    const response = await this.modelRouter.executePrompt('planner', prompt);
    
    // Save plan to file
    const planPath = path.join(config.paths.plans, `plan-${Date.now()}.md`);
    fs.writeFileSync(planPath, response.content);
    
    return {
      plan: response.content,
      path: planPath
    };
  }
}