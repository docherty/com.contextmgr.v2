import dotenv from 'dotenv';
import path from 'path';

dotenv.config();

export const config = {
  // Model configuration
  models: {
    planner: process.env.PLANNER_MODEL || 'gpt-4o',
    coder: process.env.CODER_MODEL || 'claude-3-opus-20240229',
    reviewer: process.env.REVIEWER_MODEL || 'gpt-4o',
  },
  
  // Storage paths
  paths: {
    plans: path.join(process.cwd(), 'data', 'plans'),
    context: path.join(process.cwd(), 'data', 'context'),
    vectorStore: path.join(process.cwd(), 'data', 'vectors'),
  },
  
  // Git configuration
  git: {
    autoCommit: process.env.GIT_AUTO_COMMIT === 'true',
    commitMessage: process.env.GIT_COMMIT_MESSAGE || 'Update from context manager',
  }
};