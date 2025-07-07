# System Design: Multi-Agent GenAI Development System

This document provides a detailed system design for the Multi-Agent GenAI Development System, elaborating on its architecture, component interactions, data flows, and key interfaces.

## 1. Overall System Architecture Diagram

```mermaid
graph TD
    User[User] --> Frontend[React Frontend]
    Frontend -->|HTTP/REST| MCP_Server[FastAPI MCP Server]

    subgraph Backend Services
        MCP_Server -->|Redis Client| Redis[Redis (Pub/Sub & KV Store)]
        MCP_Server -->|HTTP/REST| Ollama[Ollama LLM Service]
        MCP_Server -->|Dynamic Load| Agents[Python Agents]
        Agents -->|Tool Calls| Tools[Python Tools]
        Tools -->|File Ops| Workspace[Project Workspace (Filesystem)]
        Tools -->|External APIs| External_Services[External Services (e.g., GitHub, ArXiv, Web Search)]
    end

    Redis -->|Pub/Sub| Agents
    Agents -->|Redis Client| Redis

    Workspace -->|Git Ops| Git_Repo[Local Git Repository]
```

## 2. Component Breakdown & Interactions

### 2.1. FastAPI MCP Server (`src/mcp_server/main.py`)

*   **Role**: The central orchestrator and API gateway. It manages the overall workflow, job states, and dispatches tasks to agents. It's responsible for human-in-the-loop interactions (idea selection, design approval, feedback).
*   **Technology**: FastAPI (Python)
*   **Interactions**:
    *   **Receives HTTP Requests**: From the React Frontend (e.g., `start_project`, `select_idea`, `select_design`, `approve`, `feedback`, `status`).
    *   **Manages Job State**: Stores and retrieves job context and state transitions in Redis.
    *   **Dispatches Agent Tasks**: Calls `run_agent` which dynamically loads and executes agent logic.
    *   **Communicates with LLM**: Sends prompts to Ollama for agent reasoning.
    *   **Handles System Modifications**: Triggers `SystemModifier` based on `ArchitectAgent`'s plan.

### 2.2. Redis (`docker-compose.yml`)

*   **Role**: High-performance in-memory data store used for:
    *   **Job State Persistence**: Stores the entire job context (including agent outputs) as JSON strings, keyed by `job_id`.
    *   **Agent-to-Agent (A2A) Communication**: Acts as a message broker using Pub/Sub for asynchronous task dispatch and result reporting (though in the current linear workflow, direct function calls are used, Redis still holds the state).
*   **Technology**: Redis
*   **Interactions**:
    *   **MCP Server**: Reads and writes job data.
    *   **Agents**: (Conceptual for A2A) Agents would subscribe to specific channels for tasks and publish results to a common channel.

### 2.3. Ollama LLM Service (`docker-compose.yml`)

*   **Role**: Provides local, open-source Large Language Model inference for all agents.
*   **Technology**: Ollama
*   **Interactions**:
    *   **Agents**: Agents (via `BaseAgent`'s `llm` attribute) send prompts to Ollama and receive generated text responses.

### 2.4. Python Agents (`src/agents/`)

*   **Role**: Specialized AI entities, each responsible for a specific phase or task in the project development lifecycle. They encapsulate domain-specific logic and tool usage.
*   **Technology**: Python, LangChain
*   **Interactions**:
    *   **MCP Server**: Executed by the MCP server (via dynamic loading). Receive job context as input.
    *   **Ollama**: Send prompts to Ollama for reasoning and task execution.
    *   **Tools**: Utilize various Python tools to perform actions (e.g., read/write files, run shell commands, search the web).
    *   **Redis**: (Conceptual for A2A) Would publish intermediate results or request tasks from other agents.

### 2.5. Python Tools (`src/tools/`)

*   **Role**: Provide agents with capabilities to interact with the external environment or perform specific computations.
*   **Technology**: Python
*   **Interactions**:
    *   **Agents**: Called by agents to perform actions.
    *   **Filesystem**: Read from and write to the `Project Workspace`.
    *   **Shell**: Execute system commands (e.g., `git`, `npm`, `pytest`).
    *   **External APIs**: Interact with services like ArXiv, web search engines, or conceptual domain knowledge bases.

### 2.6. Project Workspace (`./workspace/`)

*   **Role**: A dedicated directory where all project-related files are created, modified, and stored by the agents. This ensures isolation from the main system.
*   **Technology**: Local Filesystem
*   **Interactions**:
    *   **FileSystemTool**: Agents use this tool to read, write, and list files within the workspace.
    *   **GitTool**: Agents use this tool to perform Git operations within the workspace.

### 2.7. React Frontend (`ui/`)

*   **Role**: Provides the user interface for initiating projects, monitoring their progress, and facilitating human-in-the-loop interactions.
*   **Technology**: React, Vite
*   **Interactions**:
    *   **MCP Server**: Sends HTTP requests to the MCP server's API endpoints to start jobs, select options, approve plans, provide feedback, and fetch job status.

## 3. Data Flow Diagram (Simplified Workflow)

This diagram illustrates the primary data flow through the system's main workflow stages.

```mermaid
graph TD
    A[User Input (Prompt)] --> B{MCP Server: Start Project}
    B --> C[Redis: Store Job Context (State: IDEA_GENERATION)]
    C --> D[MCP Server: Run IdeaGenerationAgent]
    D --> E[Redis: Update Job Context (Generated Ideas)]
    E --> F{Frontend: Display Ideas & Await Selection}
    F --> G[User Selects Idea]
    G --> H{MCP Server: Select Idea}
    H --> I[Redis: Update Job Context (Selected Idea, State: ARCHITECT_ANALYSIS)]
    I --> J[MCP Server: Run ArchitectAgent]
    J --> K{Redis: Update Job Context (Architect Result, State: ANALYZING or SYSTEM_MODIFICATION)}
    K --> L[MCP Server: Run AnalyzerAgent]
    L --> M[Redis: Update Job Context (Analyzer Result, State: DESIGNING)]
    M --> N[MCP Server: Run DesignerAgent (Multiple Designs)]
    N --> O[Redis: Update Job Context (Designer Results, State: DESIGN_EVALUATION)]
    O --> P[MCP Server: Run EvaluatorAgent]
    P --> Q[Redis: Update Job Context (Evaluated Designs, State: DESIGN_SELECTION)]
    Q --> R{Frontend: Display Designs & Await Selection}
    R --> S[User Selects Design]
    S --> T{MCP Server: Select Design}
    T --> U[Redis: Update Job Context (Selected Design, State: PENDING_APPROVAL)]
    U --> V{Frontend: Display Plan & Await Approval/Feedback}
    V --> W[User Approves OR Provides Feedback]

    W -->|Approve| X{MCP Server: Approve Job}
    X --> Y[Redis: Update Job Context (State: BUILDING)]
    Y --> Z[MCP Server: Run BuilderAgent]
    Z --> AA[Redis: Update Job Context (Builder Result, State: STATIC_ANALYSIS)]
    AA --> BB[MCP Server: Run SentinelAgent]
    BB --> CC[Redis: Update Job Context (Sentinel Report)]
    CC --> DD{Issues Found?}
    DD -->|Yes| EE[MCP Server: Run RefactoringAgent]
    EE --> FF[Redis: Update Job Context (Refactoring Result)]
    FF --> GG[Loop to STATIC_ANALYSIS]
    DD -->|No| HH[Redis: Update Job Context (State: INTEGRATING)]
    HH --> II[MCP Server: Run IntegratorAgent]
    II --> JJ[Redis: Update Job Context (Integrator Result, State: DOC_WRITING)]
    JJ --> KK[MCP Server: Run DocWriterAgent]
    KK --> LL[Redis: Update Job Context (DocWriter Result, State: DEPLOYING)]
    LL --> MM[MCP Server: Run DeploymentAgent]
    MM --> NN[Redis: Update Job Context (Deployment Result, State: MONITORING)]
    NN --> OO[MCP Server: Run RuntimeMonitorTool]
    OO --> PP[Redis: Update Job Context (Monitor Report)]
    PP --> QQ{Issues Found?}
    QQ -->|Yes| RR[Loop to REFACTORING]
    QQ -->|No| SS[Redis: Update Job Context (State: COMPLETED)]
    SS --> TT[MCP Server: Run RetrospectionAgent]
    TT --> UU[Redis: Update Job Context (Retrospection Result)]
    UU --> VV[Frontend: Display Final Status & Retrospection]

    W -->|Feedback| WW{MCP Server: Provide Feedback}
    WW --> XX[Redis: Update Job Context (Human Feedback, State: PENDING_REFINEMENT)]
    XX --> YY[MCP Server: Run RefinementAgent]
    YY --> ZZ[Redis: Update Job Context (Refinement Action)]
    ZZ --> AAA[Loop to relevant state based on RefinementAgent's output]
```

## 4. Key API Endpoints (FastAPI MCP Server)

The MCP server exposes the following RESTful API endpoints for interaction with the frontend and internal orchestration.

*   **`POST /start_project`**
    *   **Description**: Initiates a new project workflow.
    *   **Request**: `prompt: str` (high-level project concept).
    *   **Response**: `{"message": "Project generation started.", "job_id": "..."}`
*   **`POST /jobs/{job_id}/select_idea`**
    *   **Description**: Allows the user to select a generated project idea.
    *   **Request**: `job_id: str`, `idea_index: int`
    *   **Response**: `{"message": "Idea selected. Architect analysis initiated."}`
*   **`POST /jobs/{job_id}/select_design`**
    *   **Description**: Allows the user to select an evaluated architectural design.
    *   **Request**: `job_id: str`, `design_index: int`
    *   **Response**: `{"message": "Design selected. Awaiting final approval."}`
*   **`POST /jobs/{job_id}/approve`**
    *   **Description**: Approves the current state (e.g., selected design) to proceed with the workflow.
    *   **Request**: `job_id: str`
    *   **Response**: `{"message": "Job approved. Build process initiated."}`
*   **`POST /jobs/{job_id}/feedback`**
    *   **Description**: Allows the user to provide natural language feedback at specific workflow points.
    *   **Request**: `job_id: str`, `feedback: str`
    *   **Response**: `{"message": "Feedback received. Initiating refinement process."}`
*   **`GET /status/{job_id}`**
    *   **Description**: Retrieves the current status and full context of a job.
    *   **Request**: `job_id: str`
    *   **Response**: `JSON` object containing the job's `state` and `context` data.

## 5. Agent-to-Agent (A2A) Communication & Data Persistence

While the current implementation uses the MCP server as a central orchestrator that directly calls agent functions, the underlying design supports true A2A communication via Redis Pub/Sub.

*   **Job Context in Redis**: The entire state of a job, including all intermediate outputs from agents, is stored as a single JSON object in Redis under its `job_id`. This allows any agent to access the full history and context of the project.
*   **Asynchronous Task Dispatch (Conceptual A2A)**:
    *   The MCP server (or an agent) would publish a message to a specific agent's Redis channel (e.g., `agent_dispatch_analyzer`).
    *   The target agent would be continuously listening on its channel.
    *   Upon receiving a message, the agent would process the task and publish its result to a common `agent_results` channel.
    *   The MCP server (or a dedicated "Result Listener" component) would subscribe to `agent_results` to update the main job context and trigger the next workflow state.

## 6. Data Structures (Simplified JSON Schemas)

### 6.1. Full Job Context (Stored in Redis)

```json
{
  "job_id": "string",
  "state": "string", // e.g., "IDEA_GENERATION", "DESIGN_SELECTION", "BUILDING", "COMPLETED", "ERROR"
  "context": {
    "initial_prompt": "string",
    "generated_ideas": [ // From IdeaGenerationAgent
      {
        "title": "string",
        "description": "string",
        "features": ["string"],
        "technologies": ["string"]
      }
    ],
    "selected_idea": { ... }, // Selected idea from generated_ideas
    "architect_result": { // From ArchitectAgent
      "modifications_required": "boolean",
      "plan": {
        "new_tools": { "filename.py": "code_string" },
        "new_agents": { "filename.py": "code_string" },
        "mcp_modifications": ["string"]
      }
    },
    "modification_report": "string", // From SystemModifier
    "analyzer_result": { // From AnalyzerAgent
      "summary": "string",
      "analysis": "string",
      "research_findings": ["string"],
      "domain_insights": "string",
      "innovative_suggestions": [
        { "suggestion": "string", "justification": "string" }
      ],
      "reasoning_explanation": "string"
    },
    "designer_results": [ // From DesignerAgent (multiple designs)
      {
        "architecture": {
          "frontend": { "framework": "string", "description": "string" },
          "backend": { "framework": "string", "description": "string" },
          "database_schema": { "table_name": { "columns": ["string"] } }
        },
        "api_spec": "string", // OpenAPI YAML
        "diagram_url": "string",
        "project_plan": ["string"]
      }
    ],
    "evaluated_designs": [ // From EvaluatorAgent (designer_results + evaluation)
      {
        // ... original design fields ...
        "evaluation": {
          "cost_score": "int",
          "complexity_score": "int",
          "scalability_score": "int",
          "pros": ["string"],
          "cons": ["string"]
        }
      }
    ],
    "selected_design": { ... }, // Selected design from evaluated_designs
    "builder_result": { // From BuilderAgent
      "status": "string",
      "message": "string",
      "final_error": "string" // if failed
    },
    "sentinel_report": { // From SentinelAgent
      "issues_found": "boolean",
      "report": "string",
      "summary": "string"
    },
    "refactoring_result": { // From RefactoringAgent
      "status": "string",
      "message": "string",
      "changes_made": ["string"]
    },
    "integrator_result": { ... }, // From IntegratorAgent
    "doc_writer_result": { ... }, // From DocWriterAgent
    "deployment_result": { // From DeploymentAgent
      "status": "string",
      "message": "string",
      "deployment_url": "string"
    },
    "monitor_report": { // From RuntimeMonitorTool
      "overall_health": "string",
      "performance_issues": ["string"],
      "errors_detected": ["string"],
      "security_alerts": ["string"]
    },
    "human_feedback": "string", // From Frontend
    "refinement_result": { // From RefinementAgent
      "action_type": "string",
      "details": { ... },
      "next_state_suggestion": "string",
      "explanation": "string"
    },
    "retrospection_result": { // From RetrospectionAgent
      "job_outcome": "string",
      "failure_reason": "string",
      "insights": "string",
      "agent_specific_feedback": { "agent_name": "feedback_string" }
    }
  },
  "error_message": "string" // If job ended in ERROR state
}
```

## 7. Deployment Strategy

The system is designed for containerized deployment, leveraging free-tier cloud services where possible.

*   **Containerization**: All components (MCP Server, Redis, Ollama) are containerized using Docker.
*   **Local Development**: `docker-compose.yml` orchestrates all services for easy local setup.
*   **Backend Deployment (Conceptual)**: The FastAPI MCP Server can be deployed to platforms like Railway, which support Docker image deployments. The Docker image would be built via GitHub Actions and pushed to Docker Hub.
*   **Frontend Deployment (Conceptual)**: The React frontend can be deployed to static site hosting services like Vercel or Netlify, which integrate directly with GitHub repositories for continuous deployment.
*   **Ollama Deployment**: For production, Ollama would ideally run on a dedicated GPU instance or a managed service that provides LLM inference.

This detailed system design provides a comprehensive understanding of the Multi-Agent GenAI Development System, its internal workings, and how its various components interact to achieve autonomous project creation.