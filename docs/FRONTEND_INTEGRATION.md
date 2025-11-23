# Frontend Integration Guide

This guide explains how to integrate a frontend application (React, Vue, Angular, or vanilla JS) with the Research Copilot backend API.

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Configuration](#api-configuration)
3. [Authentication](#authentication)
4. [Core Integration Patterns](#core-integration-patterns)
5. [React Integration Example](#react-integration-example)
6. [Vue Integration Example](#vue-integration-example)
7. [State Management](#state-management)
8. [Error Handling](#error-handling)
9. [WebSocket Support](#websocket-support)
10. [Deployment Considerations](#deployment-considerations)

---

## Quick Start

### Prerequisites

- Backend API running on `http://localhost:8000`
- Node.js and npm/yarn installed
- Frontend framework of choice (React, Vue, Angular, etc.)

### Basic Setup

1. **Install HTTP client** (choose one):

```bash
# Using axios (recommended)
npm install axios

# Using fetch (built-in, no install needed)
# Or use SWR for React
npm install swr

# Or use TanStack Query (React Query)
npm install @tanstack/react-query
```

2. **Test connection**:

```javascript
// Test API connection
fetch('http://localhost:8000/health')
  .then(res => res.json())
  .then(data => console.log('API Status:', data))
  .catch(err => console.error('API Error:', err));
```

---

## API Configuration

### Create API Client

Create a centralized API client for reusability:

```javascript
// src/api/client.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (for adding auth tokens, logging, etc.)
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor (for error handling)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error
      console.error('API Error:', error.response.data);
      
      // Handle specific status codes
      if (error.response.status === 401) {
        // Redirect to login or refresh token
        window.location.href = '/login';
      }
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Environment Configuration

Create environment files:

```bash
# .env.development
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# .env.production
REACT_APP_API_URL=https://api.your-domain.com
REACT_APP_WS_URL=wss://api.your-domain.com
```

---

## Authentication

The current API doesn't have authentication, but here's how to add it:

### Backend: Add JWT Authentication (FastAPI)

```python
# In api.py, add JWT middleware
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Protect endpoints
@app.post("/api/projects")
async def create_project(request: CreateProjectRequest, user = Depends(get_current_user)):
    # Endpoint implementation
    pass
```

### Frontend: Store and Use Tokens

```javascript
// src/api/auth.js
import apiClient from './client';

export const login = async (username, password) => {
  const response = await apiClient.post('/api/auth/login', {
    username,
    password,
  });
  
  const { access_token } = response.data;
  localStorage.setItem('auth_token', access_token);
  
  return response.data;
};

export const logout = () => {
  localStorage.removeItem('auth_token');
  window.location.href = '/login';
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('auth_token');
};
```

---

## Core Integration Patterns

### Project Management API

```javascript
// src/api/projects.js
import apiClient from './client';

export const projectAPI = {
  // Create new project
  create: async (name, researchQuestion) => {
    const response = await apiClient.post('/api/projects', {
      name,
      research_question: researchQuestion,
    });
    return response.data;
  },

  // List all projects
  list: async () => {
    const response = await apiClient.get('/api/projects');
    return response.data;
  },

  // Get project details
  get: async (projectId) => {
    const response = await apiClient.get(`/api/projects/${projectId}`);
    return response.data;
  },

  // Delete project
  delete: async (projectId) => {
    const response = await apiClient.delete(`/api/projects/${projectId}`);
    return response.data;
  },
};
```

### Workflow Execution API

```javascript
// src/api/workflow.js
import apiClient from './client';

export const workflowAPI = {
  // Run Literature Explorer
  runLiteratureExplorer: async (projectId, parameters = {}) => {
    const response = await apiClient.post('/api/workflow/literature-explorer', {
      project_id: projectId,
      parameters,
    });
    return response.data;
  },

  // Run Hypothesis Generator
  runHypothesisEngine: async (projectId, parameters = {}) => {
    const response = await apiClient.post('/api/workflow/hypothesis-engine', {
      project_id: projectId,
      parameters,
    });
    return response.data;
  },

  // Run Design Builder
  runDesignEngine: async (projectId, parameters = {}) => {
    const response = await apiClient.post('/api/workflow/design-engine', {
      project_id: projectId,
      parameters,
    });
    return response.data;
  },

  // Run Stimulus Factory
  runStimulusEngine: async (projectId, parameters = {}) => {
    const response = await apiClient.post('/api/workflow/stimulus-engine', {
      project_id: projectId,
      parameters,
    });
    return response.data;
  },

  // Run Simulation
  runSimulationEngine: async (projectId, parameters = {}) => {
    const response = await apiClient.post('/api/workflow/simulation-engine', {
      project_id: projectId,
      parameters,
    });
    return response.data;
  },

  // Run full workflow
  runFullWorkflow: async (projectId, parameters = {}) => {
    const response = await apiClient.post('/api/workflow/full', {
      project_id: projectId,
      parameters,
    });
    return response.data;
  },
};
```

### Checkpoint Management API

```javascript
// src/api/checkpoints.js
import apiClient from './client';

export const checkpointAPI = {
  // Create checkpoint
  create: async (projectId, checkpointName) => {
    const response = await apiClient.post(
      `/api/projects/${projectId}/checkpoints/${checkpointName}`
    );
    return response.data;
  },

  // Restore checkpoint
  restore: async (projectId, checkpointName) => {
    const response = await apiClient.post(
      `/api/projects/${projectId}/checkpoints/${checkpointName}/restore`
    );
    return response.data;
  },

  // List checkpoints
  list: async (projectId) => {
    const response = await apiClient.get(
      `/api/projects/${projectId}/checkpoints`
    );
    return response.data;
  },
};
```

---

## React Integration Example

### Complete React Application Structure

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.js          # Axios instance
│   │   ├── projects.js        # Project API
│   │   ├── workflow.js        # Workflow API
│   │   └── checkpoints.js     # Checkpoint API
│   ├── components/
│   │   ├── ProjectList.jsx
│   │   ├── ProjectCreate.jsx
│   │   ├── WorkflowRunner.jsx
│   │   └── ResultsViewer.jsx
│   ├── hooks/
│   │   ├── useProjects.js
│   │   └── useWorkflow.js
│   ├── context/
│   │   └── ProjectContext.jsx
│   ├── App.jsx
│   └── index.js
└── package.json
```

### Custom React Hooks

```javascript
// src/hooks/useProjects.js
import { useState, useEffect } from 'react';
import { projectAPI } from '../api/projects';

export const useProjects = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const data = await projectAPI.list();
      setProjects(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const createProject = async (name, researchQuestion) => {
    try {
      const newProject = await projectAPI.create(name, researchQuestion);
      setProjects([...projects, newProject]);
      return newProject;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const deleteProject = async (projectId) => {
    try {
      await projectAPI.delete(projectId);
      setProjects(projects.filter(p => p.id !== projectId));
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  return {
    projects,
    loading,
    error,
    createProject,
    deleteProject,
    refreshProjects: fetchProjects,
  };
};
```

```javascript
// src/hooks/useWorkflow.js
import { useState } from 'react';
import { workflowAPI } from '../api/workflow';

export const useWorkflow = (projectId) => {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const runModule = async (moduleName, parameters = {}) => {
    try {
      setRunning(true);
      setError(null);

      let response;
      switch (moduleName) {
        case 'literature':
          response = await workflowAPI.runLiteratureExplorer(projectId, parameters);
          break;
        case 'hypothesis':
          response = await workflowAPI.runHypothesisEngine(projectId, parameters);
          break;
        case 'design':
          response = await workflowAPI.runDesignEngine(projectId, parameters);
          break;
        case 'stimulus':
          response = await workflowAPI.runStimulusEngine(projectId, parameters);
          break;
        case 'simulation':
          response = await workflowAPI.runSimulationEngine(projectId, parameters);
          break;
        case 'full':
          response = await workflowAPI.runFullWorkflow(projectId, parameters);
          break;
        default:
          throw new Error(`Unknown module: ${moduleName}`);
      }

      setResult(response);
      return response;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setRunning(false);
    }
  };

  return {
    running,
    result,
    error,
    runModule,
  };
};
```

### React Components

```jsx
// src/components/ProjectCreate.jsx
import React, { useState } from 'react';
import { useProjects } from '../hooks/useProjects';

export const ProjectCreate = () => {
  const [name, setName] = useState('');
  const [researchQuestion, setResearchQuestion] = useState('');
  const { createProject } = useProjects();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const project = await createProject(name, researchQuestion);
      console.log('Created project:', project);
      
      // Reset form
      setName('');
      setResearchQuestion('');
      
      // Navigate or show success message
      alert(`Project "${project.name}" created successfully!`);
    } catch (error) {
      alert(`Error creating project: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="project-create">
      <h2>Create New Research Project</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Project Name:</label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="e.g., Attachment Study 2024"
          />
        </div>

        <div className="form-group">
          <label htmlFor="research-question">Research Question:</label>
          <textarea
            id="research-question"
            value={researchQuestion}
            onChange={(e) => setResearchQuestion(e.target.value)}
            required
            rows={4}
            placeholder="How does attachment anxiety influence emotion regulation strategies?"
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Project'}
        </button>
      </form>
    </div>
  );
};
```

```jsx
// src/components/WorkflowRunner.jsx
import React, { useState } from 'react';
import { useWorkflow } from '../hooks/useWorkflow';

export const WorkflowRunner = ({ projectId }) => {
  const { running, result, error, runModule } = useWorkflow(projectId);
  const [selectedModule, setSelectedModule] = useState('literature');

  const modules = [
    { id: 'literature', name: 'Literature Explorer', description: 'Map research landscape' },
    { id: 'hypothesis', name: 'Hypothesis Generator', description: 'Generate testable hypotheses' },
    { id: 'design', name: 'Design Builder', description: 'Create experimental design' },
    { id: 'stimulus', name: 'Stimulus Factory', description: 'Generate stimuli' },
    { id: 'simulation', name: 'Simulation', description: 'Run synthetic participant simulation' },
    { id: 'full', name: 'Full Workflow', description: 'Run all modules in sequence' },
  ];

  const handleRunModule = async () => {
    try {
      await runModule(selectedModule);
      alert(`${modules.find(m => m.id === selectedModule).name} completed successfully!`);
    } catch (err) {
      alert(`Error running module: ${err.message}`);
    }
  };

  return (
    <div className="workflow-runner">
      <h2>Run Workflow Modules</h2>

      <div className="module-selector">
        <label htmlFor="module">Select Module:</label>
        <select
          id="module"
          value={selectedModule}
          onChange={(e) => setSelectedModule(e.target.value)}
          disabled={running}
        >
          {modules.map(module => (
            <option key={module.id} value={module.id}>
              {module.name} - {module.description}
            </option>
          ))}
        </select>
      </div>

      <button onClick={handleRunModule} disabled={running}>
        {running ? 'Running...' : 'Run Module'}
      </button>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="result-display">
          <h3>Module Results</h3>
          <p><strong>Status:</strong> {result.status}</p>
          <p><strong>Message:</strong> {result.message}</p>
          {result.data && (
            <div className="result-data">
              <h4>Data:</h4>
              <pre>{JSON.stringify(result.data, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

```jsx
// src/App.jsx
import React, { useState } from 'react';
import { ProjectCreate } from './components/ProjectCreate';
import { ProjectList } from './components/ProjectList';
import { WorkflowRunner } from './components/WorkflowRunner';
import './App.css';

function App() {
  const [selectedProject, setSelectedProject] = useState(null);
  const [view, setView] = useState('list'); // 'list', 'create', 'workflow'

  return (
    <div className="App">
      <header>
        <h1>Research Copilot</h1>
        <nav>
          <button onClick={() => setView('list')}>Projects</button>
          <button onClick={() => setView('create')}>New Project</button>
        </nav>
      </header>

      <main>
        {view === 'list' && (
          <ProjectList
            onSelectProject={(project) => {
              setSelectedProject(project);
              setView('workflow');
            }}
          />
        )}

        {view === 'create' && <ProjectCreate />}

        {view === 'workflow' && selectedProject && (
          <div>
            <button onClick={() => setView('list')}>← Back to Projects</button>
            <h2>Project: {selectedProject.name}</h2>
            <WorkflowRunner projectId={selectedProject.id} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
```

---

## Vue Integration Example

### Vue 3 Composition API

```javascript
// src/composables/useProjects.js
import { ref, onMounted } from 'vue';
import { projectAPI } from '@/api/projects';

export function useProjects() {
  const projects = ref([]);
  const loading = ref(false);
  const error = ref(null);

  const fetchProjects = async () => {
    loading.value = true;
    error.value = null;

    try {
      projects.value = await projectAPI.list();
    } catch (err) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  };

  const createProject = async (name, researchQuestion) => {
    try {
      const newProject = await projectAPI.create(name, researchQuestion);
      projects.value.push(newProject);
      return newProject;
    } catch (err) {
      error.value = err.message;
      throw err;
    }
  };

  onMounted(() => {
    fetchProjects();
  });

  return {
    projects,
    loading,
    error,
    createProject,
    fetchProjects,
  };
}
```

```vue
<!-- src/components/ProjectCreate.vue -->
<template>
  <div class="project-create">
    <h2>Create New Research Project</h2>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="name">Project Name:</label>
        <input
          id="name"
          v-model="name"
          type="text"
          required
          placeholder="e.g., Attachment Study 2024"
        />
      </div>

      <div class="form-group">
        <label for="research-question">Research Question:</label>
        <textarea
          id="research-question"
          v-model="researchQuestion"
          required
          rows="4"
          placeholder="How does attachment anxiety influence emotion regulation?"
        />
      </div>

      <button type="submit" :disabled="loading">
        {{ loading ? 'Creating...' : 'Create Project' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useProjects } from '@/composables/useProjects';

const { createProject } = useProjects();

const name = ref('');
const researchQuestion = ref('');
const loading = ref(false);

const handleSubmit = async () => {
  loading.value = true;

  try {
    const project = await createProject(name.value, researchQuestion.value);
    console.log('Created project:', project);
    
    // Reset form
    name.value = '';
    researchQuestion.value = '';
    
    alert(`Project "${project.name}" created successfully!`);
  } catch (error) {
    alert(`Error creating project: ${error.message}`);
  } finally {
    loading.value = false;
  }
};
</script>
```

---

## State Management

### Using React Context

```javascript
// src/context/ProjectContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { projectAPI } from '../api/projects';

const ProjectContext = createContext();

export const ProjectProvider = ({ children }) => {
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await projectAPI.list();
      setProjects(data);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectProject = async (projectId) => {
    try {
      const project = await projectAPI.get(projectId);
      setCurrentProject(project);
    } catch (error) {
      console.error('Failed to load project:', error);
    }
  };

  const value = {
    projects,
    currentProject,
    loading,
    loadProjects,
    selectProject,
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
};

export const useProjectContext = () => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProjectContext must be used within ProjectProvider');
  }
  return context;
};
```

### Using Vuex (Vue 3)

```javascript
// src/store/projects.js
import { projectAPI } from '@/api/projects';

export default {
  namespaced: true,
  
  state: () => ({
    projects: [],
    currentProject: null,
    loading: false,
  }),
  
  mutations: {
    SET_PROJECTS(state, projects) {
      state.projects = projects;
    },
    SET_CURRENT_PROJECT(state, project) {
      state.currentProject = project;
    },
    SET_LOADING(state, loading) {
      state.loading = loading;
    },
  },
  
  actions: {
    async loadProjects({ commit }) {
      commit('SET_LOADING', true);
      try {
        const projects = await projectAPI.list();
        commit('SET_PROJECTS', projects);
      } finally {
        commit('SET_LOADING', false);
      }
    },
    
    async selectProject({ commit }, projectId) {
      const project = await projectAPI.get(projectId);
      commit('SET_CURRENT_PROJECT', project);
    },
  },
};
```

---

## Error Handling

### Centralized Error Handler

```javascript
// src/utils/errorHandler.js
export class APIError extends Error {
  constructor(message, statusCode, details) {
    super(message);
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.details = details;
  }
}

export const handleAPIError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        return new APIError('Invalid request', 400, data.detail);
      case 401:
        return new APIError('Unauthorized', 401, 'Please log in');
      case 404:
        return new APIError('Resource not found', 404, data.detail);
      case 500:
        return new APIError('Server error', 500, data.detail);
      default:
        return new APIError(`Request failed with status ${status}`, status, data.detail);
    }
  } else if (error.request) {
    // Request made but no response
    return new APIError('Network error', 0, 'No response from server');
  } else {
    // Other errors
    return new APIError('Request failed', 0, error.message);
  }
};
```

### Error Boundary Component (React)

```jsx
// src/components/ErrorBoundary.jsx
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}>
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

---

## WebSocket Support

### Real-time Updates for Long-Running Operations

```javascript
// src/api/websocket.js
class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.listeners = new Map();
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const { type, payload } = data;

      // Notify listeners
      if (this.listeners.has(type)) {
        this.listeners.get(type).forEach(callback => callback(payload));
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Reconnect after 5 seconds
      setTimeout(() => this.connect(), 5000);
    };
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
  }

  off(eventType, callback) {
    if (this.listeners.has(eventType)) {
      const callbacks = this.listeners.get(eventType);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  send(type, payload) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

const wsClient = new WebSocketClient(
  process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws'
);

export default wsClient;
```

### Using WebSocket in Components

```jsx
// src/components/WorkflowProgress.jsx
import React, { useEffect, useState } from 'react';
import wsClient from '../api/websocket';

export const WorkflowProgress = ({ projectId }) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle');

  useEffect(() => {
    // Connect to WebSocket
    wsClient.connect();

    // Listen for progress updates
    const handleProgress = (data) => {
      if (data.projectId === projectId) {
        setProgress(data.progress);
        setStatus(data.status);
      }
    };

    wsClient.on('workflow:progress', handleProgress);

    // Cleanup
    return () => {
      wsClient.off('workflow:progress', handleProgress);
    };
  }, [projectId]);

  return (
    <div className="workflow-progress">
      <h3>Workflow Progress</h3>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }}>
          {progress}%
        </div>
      </div>
      <p>Status: {status}</p>
    </div>
  );
};
```

---

## Deployment Considerations

### CORS Configuration

In production, configure CORS properly:

```python
# In api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.com",
        "http://localhost:3000"  # For development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variables

```bash
# Production frontend .env
REACT_APP_API_URL=https://api.your-domain.com
REACT_APP_WS_URL=wss://api.your-domain.com/ws
```

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://backend:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

### Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://backend:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Testing Integration

### API Mocking for Tests

```javascript
// src/api/__mocks__/projects.js
export const projectAPI = {
  create: jest.fn(() => Promise.resolve({
    id: 'mock-id',
    name: 'Mock Project',
    status: 'active',
  })),
  
  list: jest.fn(() => Promise.resolve([
    { id: '1', name: 'Project 1', status: 'active' },
    { id: '2', name: 'Project 2', status: 'completed' },
  ])),
  
  get: jest.fn((id) => Promise.resolve({
    id,
    name: 'Mock Project',
    status: 'active',
  })),
  
  delete: jest.fn(() => Promise.resolve({ status: 'success' })),
};
```

### Component Tests

```javascript
// src/components/__tests__/ProjectCreate.test.jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ProjectCreate } from '../ProjectCreate';
import { projectAPI } from '../../api/projects';

jest.mock('../../api/projects');

describe('ProjectCreate', () => {
  it('creates a project successfully', async () => {
    render(<ProjectCreate />);
    
    // Fill form
    fireEvent.change(screen.getByLabelText(/project name/i), {
      target: { value: 'Test Project' },
    });
    fireEvent.change(screen.getByLabelText(/research question/i), {
      target: { value: 'How does X affect Y?' },
    });
    
    // Submit
    fireEvent.click(screen.getByText(/create project/i));
    
    // Verify API called
    await waitFor(() => {
      expect(projectAPI.create).toHaveBeenCalledWith(
        'Test Project',
        'How does X affect Y?'
      );
    });
  });
});
```

---

## Troubleshooting

### Common Issues

**1. CORS Errors**
```
Access to fetch at 'http://localhost:8000/api/projects' from origin 'http://localhost:3000'
has been blocked by CORS policy
```
**Solution:** Ensure CORS middleware is configured on backend with correct origins.

**2. Network Timeout**
```
AxiosError: timeout of 30000ms exceeded
```
**Solution:** Increase timeout or optimize backend processing:
```javascript
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // Increase to 60 seconds
});
```

**3. 401 Unauthorized**
**Solution:** Check if auth token is being sent correctly in request headers.

**4. Connection Refused**
```
Error: connect ECONNREFUSED 127.0.0.1:8000
```
**Solution:** Verify backend server is running: `curl http://localhost:8000/health`

---

## Additional Resources

- **FastAPI CORS**: https://fastapi.tiangolo.com/tutorial/cors/
- **Axios Documentation**: https://axios-http.com/docs/intro
- **React Query**: https://tanstack.com/query/latest
- **SWR (React Hooks)**: https://swr.vercel.app/
- **Vue Composables**: https://vuejs.org/guide/reusability/composables.html

---

## Summary

This guide covered:

✅ API client setup and configuration  
✅ React and Vue integration examples  
✅ Custom hooks and composables  
✅ State management patterns  
✅ Error handling  
✅ WebSocket support for real-time updates  
✅ Deployment considerations  
✅ Testing strategies  

You now have everything needed to integrate your frontend with the Research Copilot backend API!
