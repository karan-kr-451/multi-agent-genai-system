# Multi-Agent GenAI Development System

This project is an advanced, fully agentic, multi-agent Generative AI system designed for end-to-end project development. It leverages the Model Context Protocol (MCP) server pattern and Agent-to-Agent (A2A) communication to orchestrate a complex workflow, aiming to surpass human capabilities in project creation through automation, self-correction, continuous learning, and advanced human-AI collaboration.

## Table of Contents
1.  [Project Overview](#1-project-overview)
2.  [High-Level Architecture](#2-high-level-architecture)
3.  [Agent Definitions & Responsibilities](#3-agent-definitions--responsibilities)
    *   [Idea Generation Agent](#idea-generation-agent)
    *   [Architect Agent](#architect-agent)
    *   [Analyzer Agent](#analyzer-agent)
    *   [Designer Agent](#designer-agent)
    *   [Evaluator Agent](#evaluator-agent)
    *   [Builder Agent](#builder-agent)
    *   [Sentinel Agent](#sentinel-agent)
    *   [Refactoring Agent](#refactoring-agent)
    *   [Integrator Agent](#integrator-agent)
    *   [Doc Writer Agent](#doc-writer-agent)
    *   [Deployment Agent](#deployment-agent)
    *   [Retrospection Agent](#retrospection-agent)
    *   [Refinement Agent](#refinement-agent)
4.  [Key Features & Workflows](#4-key-features--workflows)
    *   [Idea Generation & Selection](#idea-generation--selection)
    *   [Self-Modification (Architect Agent)](#self-modification-architect-agent)
    *   [Generative Design & Evaluation](#generative-design--evaluation)
    *   [Human-in-the-Loop (HITL) Approvals](#human-in-the-loop-hitl-approvals)
    *   [Proactive Self-Healing & Predictive Maintenance](#proactive-self-healing--predictive-maintenance)
    *   [Deep Domain Expertise & XAI](#deep-domain-expertise--xai)
    *   [Continuous Learning & Self-Improvement](#continuous-learning--self-improvement)
    *   [Advanced Human-AI Collaboration (Refinement)](#advanced-human-ai-collaboration-refinement)
    *   [Deployment & Monitoring (Conceptual)](#deployment--monitoring-conceptual)
5.  [Setup & Installation](#5-setup--installation)
6.  [Usage](#6-usage)
7.  [Future Enhancements (Conceptual)](#7-future-enhancements-conceptual)

---

## 1. Project Overview

This system automates the software development lifecycle from a high-level concept to a deployed and monitored application. It's built with a Python backend (FastAPI, LangChain) and a React frontend, utilizing open-source tools and a modular agent-based architecture. The goal is to create a highly autonomous system that can adapt, learn, and self-correct, pushing the boundaries of AI-driven project creation.

## 2. High-Level Architecture

The system is designed around a central **Model Context Protocol (MCP) Server**, which acts as the orchestrator and communication hub.

*   **MCP Server (FastAPI)**: The central brain. Manages job states, dispatches tasks to agents, handles human interactions (approvals, feedback), and persists job context in Redis.
*   **Agents (LangChain)**: Specialized AI entities, each with a defined role, system prompt, and toolset.
*   **Tools**: Functions or APIs that agents can use to interact with the environment (filesystem, Git, web search, external knowledge bases, etc.).
*   **Redis**: Used for inter-agent messaging (Pub/Sub) and persistent storage of job contexts and states.
*   **Ollama**: Provides local, open-source Large Language Models (LLMs) for agent reasoning.
*   **Frontend (React/Vite)**: A user interface for initiating projects, monitoring progress, and providing human-in-the-loop approvals and feedback.
*   **Docker/Docker Compose**: For containerization and easy local setup of all services.
*   **GitHub Actions**: For CI/CD automation (conceptual for the generated projects).

```yaml
version: 1.0
system:
  name: Multi-Agent GenAI Development System
  description: An autonomous system for end-to-end project development using FOSS.
  components:
    - name: mcp_server
      type: backend
      framework: FastAPI
      language: Python
      description: Manages agent state, context, and tool connections.
    - name: messaging_layer
      type: broker
      service: Redis (Pub/Sub)
      description: Facilitates asynchronous A2A communication.
    - name: agent_framework
      type: library
      name: LangChain
      description: Core framework for building individual agents.
    - name: llm_service
      type: local_api
      name: Ollama
      models: [llama3, mistral, codellama]
      description: Provides local, open-source LLM inference.
    - name: vector_store
      type: database
      name: ChromaDB # (Conceptual, not fully implemented in this version)
      description: Stores and retrieves embeddings for context retrieval.
    - name: frontend
      type: ui
      framework: React (Vite)
      description: User interface for managing and monitoring the system.
    - name: ci_cd
      type: automation
      service: GitHub Actions
      description: Automates build, test, and deployment pipelines.
    - name: deployment
      targets:
        backend: Railway # (Conceptual)
        frontend: Vercel # (Conceptual)
```

## 3. Agent Definitions & Responsibilities

Each agent is a specialized Python class built with LangChain, equipped with a specific set of tools and a system prompt defining its role.

### Idea Generation Agent
*   **Role**: Takes a high-level concept and generates multiple distinct, concrete project ideas.
*   **Inputs**: High-level project concept (text).
*   **Outputs**: JSON array of project ideas (title, description, features, technologies).
*   **Key Tools**: `SearchTool`.

### Architect Agent
*   **Role**: The system's "meta-brain." Analyzes project requirements against current system capabilities and generates a "System Modification Plan" if new tools or agents are needed.
*   **Inputs**: Initial project prompt, current system context (including agent/tool code).
*   **Outputs**: JSON indicating `modifications_required` and a `plan` (new tool/agent code, MCP modifications).
*   **Key Tools**: `FileSystemTool` (read-only access to `src/`).

### Analyzer Agent
*   **Role**: Conducts in-depth analysis of the selected project idea, performs research, and proposes innovative extensions.
*   **Inputs**: Selected project idea (JSON).
*   **Outputs**: Detailed JSON report (summary, analysis, research findings, domain insights, innovative suggestions, reasoning explanation).
*   **Key Tools**: `GitTool`, `FileSystemTool`, `SearchTool`, `ArxivTool`, `DomainExpertTool`.

### Designer Agent
*   **Role**: Creates multiple distinct system architectures and project plans based on the Analyzer's report.
*   **Inputs**: Analyzer Agent's report (JSON).
*   **Outputs**: JSON array of design proposals (architecture, API spec, PlantUML diagram URL, project plan).
*   **Key Tools**: `FileSystemTool`, `PlantUMLTool`.

### Evaluator Agent
*   **Role**: Assesses multiple architectural design proposals and provides a simulated evaluation (cost, complexity, scalability, pros/cons).
*   **Inputs**: JSON array of design proposals.
*   **Outputs**: JSON array of evaluated designs (original design + evaluation metrics).
*   **Key Tools**: None (primarily LLM reasoning).

### Builder Agent
*   **Role**: Writes the code for the project based on the selected design. Includes an advanced self-correction loop for debugging.
*   **Inputs**: Selected design (JSON).
*   **Outputs**: Confirmation of build completion or error report.
*   **Key Tools**: `FileSystemTool`, `ShellTool`, `ASTAnalysisTool`.

### Sentinel Agent
*   **Role**: Performs static analysis on the generated code to identify issues, code smells, and vulnerabilities.
*   **Inputs**: Project in `workspace` directory.
*   **Outputs**: JSON report (issues found, raw report, summary).
*   **Key Tools**: `ShellTool`, `FileSystemTool`.

### Refactoring Agent
*   **Role**: Fixes code quality issues, bugs, or vulnerabilities identified by the Sentinel Agent or during the build process. Iteratively applies fixes.
*   **Inputs**: Issue description (from Sentinel or Builder).
*   **Outputs**: JSON (status, message, changes made).
*   **Key Tools**: `FileSystemTool`, `ShellTool`, `ASTAnalysisTool`.

### Integrator Agent
*   **Role**: Manages version control (Git) and prepares the project for deployment, including generating CI/CD pipelines.
*   **Inputs**: Latest code commits.
*   **Outputs**: Confirmation of integration and CI/CD readiness.
*   **Key Tools**: `GitTool`, `FileSystemTool`.

### Doc Writer Agent
*   **Role**: Creates comprehensive documentation for the project, including `README.md` and API documentation.
*   **Inputs**: Completed codebase and design documents.
*   **Outputs**: Confirmation of documentation generation.
*   **Key Tools**: `FileSystemTool`.

### Deployment Agent
*   **Role**: (Conceptual) Simulates deploying the application to a production-like environment.
*   **Inputs**: Ready-to-deploy project.
*   **Outputs**: JSON (status, message, deployment URL).
*   **Key Tools**: `ShellTool` (conceptual interaction with cloud APIs).

### Retrospection Agent
*   **Role**: Analyzes the complete context of a finished job (success or failure) to extract actionable insights for system improvement.
*   **Inputs**: Full job context (JSON).
*   **Outputs**: JSON (job outcome, failure reason, insights, agent-specific feedback).
*   **Key Tools**: None (primarily LLM reasoning).

### Refinement Agent
*   **Role**: Interprets natural language feedback from the human user and translates it into actionable instructions or modifications for other agents or the project plan.
*   **Inputs**: Human feedback (text), current job context (JSON).
*   **Outputs**: JSON (action type, details, next state suggestion, explanation).
*   **Key Tools**: `FileSystemTool`.

## 4. Key Features & Workflows

The system operates through a sophisticated state-driven workflow managed by the MCP server.

### Idea Generation & Selection
*   The process starts with a high-level user prompt.
*   The `Idea Generation Agent` proposes multiple distinct project ideas.
*   The user reviews and selects the most suitable idea via the frontend.

### Self-Modification (Architect Agent)
*   After idea selection, the `Architect Agent` analyzes the project requirements against the system's current capabilities (existing agents and tools).
*   If new capabilities are needed (e.g., a specific API integration tool), the Architect generates a "System Modification Plan" (Python code for new tools/agents).
*   A `SystemModifier` module dynamically creates these new files, and the MCP server reloads the agents/tools, making the system self-extensible.

### Generative Design & Evaluation
*   The `Designer Agent` generates **multiple, distinct architectural designs** for the selected project idea.
*   The `Evaluator Agent` then assesses each design, providing simulated scores for cost, complexity, and scalability, along with pros and cons.
*   The user reviews these evaluated designs and selects the preferred one.

### Human-in-the-Loop (HITL) Approvals
*   The system pauses at critical junctures (e.g., after design selection) for human review and approval.
*   This ensures human oversight and control over key decisions.

### Proactive Self-Healing & Predictive Maintenance
*   After the `Builder Agent` completes its work, the `Sentinel Agent` performs static analysis (linting, basic checks).
*   If issues are found, the `Refactoring Agent` automatically attempts to fix them, iteratively applying changes and re-running checks until the code is clean or a maximum number of attempts is reached.
*   (Conceptual) After deployment, the `RuntimeMonitorTool` continuously checks the application's health, and if issues arise, it can trigger the `Refactoring Agent` for automated runtime fixes.

### Deep Domain Expertise & XAI
*   The `Analyzer Agent` utilizes a `DomainExpertTool` to query a simulated knowledge base for specialized insights relevant to the project's domain.
*   Agents are prompted to provide `reasoning_explanation` for their decisions, enhancing transparency and explainability (XAI).

### Continuous Learning & Self-Improvement
*   Upon job completion (success or failure), the `Retrospection Agent` analyzes the entire job context.
*   It identifies agent performance, tool effectiveness, workflow bottlenecks, and suggests improvements to agent prompts or system configurations.
*   (Conceptual) These insights would feed into a meta-learning loop to continuously refine the system's performance over time.

### Advanced Human-AI Collaboration (Refinement)
*   At `PENDING_APPROVAL` and `ERROR` states, the user can provide natural language feedback.
*   The `Refinement Agent` interprets this feedback and translates it into actionable instructions, potentially guiding the system to re-execute previous stages with modified parameters or adjust the project plan.

### Deployment & Monitoring (Conceptual)
*   The `Deployment Agent` simulates deploying the completed project.
*   The `RuntimeMonitorTool` (conceptual) simulates continuous monitoring of the deployed application for performance, errors, and security.

---

## 5. Setup & Installation

To get the Multi-Agent GenAI Development System up and running locally, follow these steps:

1.  **Prerequisites**:
    *   **Docker & Docker Compose**: Ensure you have Docker and Docker Compose installed on your system.
    *   **Python 3.11+**: Make sure you have a compatible Python version.
    *   **Poetry**: Install Poetry for Python dependency management: `pip install poetry`
    *   **Node.js & npm**: Ensure you have Node.js and npm installed for the React frontend.

2.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/multi-agent-genai-system.git
    cd multi-agent-genai-system
    ```
    *(Replace `https://github.com/your-username/multi-agent-genai-system.git` with your actual repository URL)*

3.  **Start Backend Services (Redis & Ollama)**:
    ```bash
    docker-compose up -d
    ```
    This will start Redis (for state management) and Ollama (for local LLM inference).

4.  **Download Ollama Model**:
    Once Ollama is running, download the `llama3` model (or your preferred model, ensure it's configured in `src/agents/base_agent.py`):
    ```bash
    docker exec -it multi-agent-genai-system-ollama-1 ollama pull llama3
    ```
    *(Note: The container name `multi-agent-genai-system-ollama-1` might vary. You can find it using `docker ps`)*

5.  **Install Backend Dependencies**:
    Navigate to the root of the project and install Python dependencies using Poetry:
    ```bash
    poetry install
    ```

6.  **Install Frontend Dependencies**:
    Navigate into the `ui` directory and install Node.js dependencies:
    ```bash
    cd ui
    npm install
    cd .. # Go back to the project root
    ```

7.  **Start the FastAPI Backend**:
    From the project root, start the FastAPI server. Use `--reload` for development convenience.
    ```bash
    uvicorn src.mcp_server.main:app --reload --host 0.0.0.0 --port 8000
    ```

8.  **Start the React Frontend**:
    In a *new terminal window*, navigate to the `ui` directory and start the React development server:
    ```bash
    cd ui
    npm run dev
    ```

## 6. Usage

1.  **Access the Frontend**: Open your web browser and navigate to `http://localhost:5173`.

2.  **Initiate a Project**:
    *   In the text area, enter a high-level project concept (e.g., "Build a secure online banking application" or "Create a mobile game with a leaderboard").
    *   Click the "Start Project" button.

3.  **Follow the Workflow**:
    *   **Idea Selection**: The system will generate several project ideas. Review them and click "Select This Idea" for your preferred option.
    *   **Architect's Analysis**: The Architect Agent will analyze the request and potentially suggest system modifications.
    *   **Design Selection**: The Designer Agent will propose multiple architectural designs, evaluated by the Evaluator Agent. Review the designs, their scores, pros, and cons, and click "Select This Design".
    *   **Human-in-the-Loop Approval**: After design selection, the system pauses in a `PENDING_APPROVAL` state. Review the selected design and click "Approve Plan" to proceed.
    *   **Providing Feedback**: If you are *not* satisfied, or if you want to request a modification, you can type your feedback into the "Provide Feedback" text area (e.g., "Make the UI more minimalist," "Ensure the database schema includes a 'last_login' field for users.") and click **"Submit Feedback"**. This will send your request to the `Refinement Agent`.
    *   **Building, Static Analysis, Refactoring**: Observe the system building the project, running static analysis, and potentially self-correcting through refactoring.
    *   **Deployment & Monitoring**: The system will conceptually deploy and monitor the application.
    *   **Retrospection**: Upon completion (or error), a retrospection report will be generated, providing insights into the job's performance.

4.  **Error Handling**: If the system encounters an unrecoverable error, the job will transition to an `ERROR` state. You can review the error message and the `Retrospection Report`. You can also provide feedback to guide the system on how to recover or what to change for a retry.

## 7. What the User Gets

Upon successful completion of a project, you will receive:

*   **A Fully Generated Codebase**: The primary output is a complete, runnable software project (frontend, backend, database schema, etc.) located in the `./workspace/` directory of your `multi-agent-genai-system` project.
*   **Design Documents**: Architecture diagrams (PlantUML URLs) and conceptual API specifications (OpenAPI format).
*   **Comprehensive Documentation**: A `README.md` file within the generated project (conceptual, generated by `DocWriterAgent`) and potentially API documentation.
*   **Insights & Learning**: Detailed reports from the Analyzer, Evaluator, Sentinel, and Retrospection Agents, providing transparency into the AI's reasoning and insights into the development process.
*   **A Deployed Application (Conceptual)**: A simulated URL for the deployed application, demonstrating the end-to-end automation.

## 8. Future Enhancements (Conceptual)

This project lays a robust foundation for a truly autonomous development system. Here are some conceptual future enhancements:

*   **Advanced Simulation & Evaluation**: Integrate more sophisticated simulation tools (e.g., for performance, cost, security) to provide more accurate design evaluations.
*   **Automated Prompt Engineering**: Implement an agent that automatically fine-tunes prompts for other agents based on retrospection insights to improve their performance.
*   **Reinforcement Learning for Orchestration**: Use RL to dynamically adjust the workflow and agent interactions based on past project successes and failures.
*   **Real-world Deployment Integration**: Connect the `Deployment Agent` to actual cloud provider APIs (AWS, GCP, Azure, Railway, Vercel) for automated provisioning and deployment.
*   **Continuous Monitoring & Self-Healing in Production**: Integrate with real APM tools and logging systems to enable the system to detect and fix issues in live production environments.
*   **Knowledge Graph for Domain Expertise**: Replace the simulated `DomainExpertTool` with a connection to a real knowledge graph or vector database for deep, queryable domain expertise.
*   **Parallel Task Execution**: Enhance the MCP server to dispatch independent tasks to multiple agent instances concurrently for faster execution.
*   **Version Control Integration**: Fully integrate Git operations for branching, merging, and pull requests, managed autonomously by the `Integrator Agent`.
*   **Automated Test Generation**: Implement an agent that can generate comprehensive unit, integration, and end-to-end tests for the generated code.
*   **User Authentication & Multi-tenancy**: Add user management to the MCP server for a multi-user environment.
*   **Visualizations**: Develop richer visualizations for the workflow, agent interactions, and project progress.