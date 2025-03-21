import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";
import { config } from "../config";

type ModelRole = 'planner' | 'coder' | 'reviewer';

/**
 * Routes requests to appropriate LLM based on the required role
 */
export class ModelRouter {
  private models: Map<string, any> = new Map();
  
  constructor() {
    // Initialize models based on config
    this.models.set('gpt-4o', new ChatOpenAI({ modelName: "gpt-4o" }));
    this.models.set('claude-3-opus-20240229', new ChatAnthropic({ 
      modelName: "claude-3-opus-20240229" 
    }));
  }
  
  /**
   * Get the appropriate model for a given role
   */
  getModelForRole(role: ModelRole) {
    const modelName = config.models[role];
    if (!this.models.has(modelName)) {
      throw new Error(`Model ${modelName} for role ${role} not configured`);
    }
    return this.models.get(modelName);
  }
  
  /**
   * Execute a prompt with the appropriate model for a role
   */
  async executePrompt(role: ModelRole, prompt: string) {
    const model = this.getModelForRole(role);
    const response = await model.invoke(prompt);
    return response;
  }
}