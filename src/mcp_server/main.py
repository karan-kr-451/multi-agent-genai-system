import json
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
import importlib.util
import os
import logging
from typing import List, Dict, Optional
from src.utils.logging_config import setup_logging
from src.utils.config import get_settings
from src.tools.tools import ALL_TOOLS
from .middleware import auth_middleware, error_handling_middleware, request_logging_middleware

# Set up logging
setup_logging()
logger = logging.getLogger("mcp_server")

# Load settings
settings = get_settings()

# Import SystemModifier
from src.system_modifier import SystemModifier

app = FastAPI(
    title="Multi-Agent GenAI Development System",
    description="A sophisticated multi-agent system for automated software development",
    version="1.0.0",
    openapi_tags=[
        {"name": "Projects", "description": "Project generation and management endpoints"},
        {"name": "Job Control", "description": "Endpoints for controlling job workflow"},
        {"name": "Status", "description": "Job status monitoring endpoints"}
    ]
)

# Add middleware in correct order
app.middleware("http")(request_logging_middleware)
app.middleware("http")(error_handling_middleware)
app.middleware("http")(auth_middleware)

# Add CORS middleware with settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis with configuration
try:
    redis_client = Redis.from_url(
        settings.get_redis_url(),
        decode_responses=True,
        socket_timeout=5
    )
    redis_client.ping()  # Test connection
    logger.info("Successfully connected to Redis at %s", settings.REDIS_HOST)
except Exception as e:
    logger.error("Failed to connect to Redis: %s", str(e))
    raise

# Dynamic Agent Loading
AGENT_MAPPING = {}

def load_dynamic_agents():
    agents_dir = os.path.join(os.path.dirname(__file__), "..", "agents")
    for filename in os.listdir(agents_dir):
        if filename.endswith(".py") and filename not in ["__init__.py", "base_agent.py"]:
            module_name = filename[:-3]
            file_path = os.path.join(agents_dir, filename)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Assuming agent class name is CamelCase version of module name
            class_name = ''.join(word.capitalize() for word in module_name.split('_'))
            agent_class = getattr(module, class_name)
            AGENT_MAPPING[module_name.replace("_agent", "")] = agent_class
            logger.info("Loaded agent: %s", class_name)

# Load dynamic agents when the server starts
load_dynamic_agents()

async def run_agent(agent_name: str, job_context: dict) -> dict:
    """Dynamically runs an agent and returns its result."""
    try:
        logger.info("Running agent: %s", agent_name)
        agent_class = AGENT_MAPPING[agent_name]
        agent = agent_class()
        result_str = await asyncio.to_thread(agent.run, json.dumps(job_context))
        try:
            return json.loads(result_str)
        except json.JSONDecodeError:
            return {"output": result_str}
    except Exception as e:
        logger.error("Error running agent %s: %s", agent_name, str(e), exc_info=True)
        raise

async def workflow_manager(job_id: str):
    """Manages the state-driven workflow for a job."""
    logger.info("Starting workflow for job: %s", job_id)
    
    while True:
        try:
            job_data_str = redis_client.get(job_id)
            if not job_data_str:
                logger.warning("Job %s not found. Exiting workflow.", job_id)
                return
            
            job_data = json.loads(job_data_str)
            state = job_data.get("state")
            logger.info("Processing job %s in state: %s", job_id, state)

            next_state = None
            if state == "INGESTION":
                ingestion_tool = ALL_TOOLS["ingestion"]
                ingested_files = []

                # Ingest files from the dedicated localFiles input
                for file_info in job_data["context"].get("files_to_ingest", []):
                    source_path = file_info["source_path"]
                    destination_filename = file_info["destination_filename"]
                    ingestion_result = await asyncio.to_thread(
                        ingestion_tool._run, 
                        json.dumps({"source_path": source_path, "destination_filename": destination_filename})
                    )
                    ingested_files.append({
                        "source": source_path, 
                        "destination": destination_filename, 
                        "result": ingestion_result
                    })
                
                # Ingest PDF if provided via dedicated input
                if job_data["context"].get("pdf_path"):
                    pdf_source_path = job_data["context"]["pdf_path"]
                    pdf_filename = os.path.basename(pdf_source_path)
                    pdf_ingestion_result = await asyncio.to_thread(
                        ingestion_tool._run, 
                        json.dumps({"source_path": pdf_source_path, "destination_filename": pdf_filename})
                    )
                    ingested_files.append({
                        "source": pdf_source_path, 
                        "destination": pdf_filename, 
                        "result": pdf_ingestion_result
                    })

                job_data["context"]["ingested_files"] = ingested_files
                next_state = "IDEA_GENERATION"

            elif state == "IDEA_GENERATION":
                result = await run_agent("idea_generation", job_data["context"])
                job_data["context"]["generated_ideas"] = result
                next_state = "IDEA_SELECTION"

            elif state == "ARCHITECT_ANALYSIS":
                architect = AGENT_MAPPING["architect"]()
                architect_result_str = await asyncio.to_thread(architect.run, json.dumps(job_data["context"]))
                architect_result = json.loads(architect_result_str)
                job_data["context"]["architect_result"] = architect_result

                if architect_result.get("modifications_required"):
                    system_modifier = SystemModifier(base_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
                    modification_report = system_modifier.apply_modifications(architect_result["plan"])
                    job_data["context"]["modification_report"] = modification_report
                    load_dynamic_agents()  # Reload agents after modifications
                    next_state = "ANALYZING"
                else:
                    next_state = "ANALYZING"

            elif state == "ANALYZING":
                result = await run_agent("analyzer", job_data["context"])
                job_data["context"]["analyzer_result"] = result
                next_state = "DESIGNING"
            
            elif state == "DESIGNING":
                designer_results = await run_agent("designer", job_data["context"])
                job_data["context"]["designer_results"] = designer_results
                next_state = "DESIGN_EVALUATION"

            elif state == "DESIGN_EVALUATION":
                evaluator = AGENT_MAPPING["evaluator"]()
                evaluated_designs_str = await asyncio.to_thread(
                    evaluator.run, 
                    json.dumps(job_data["context"]["designer_results"])
                )
                evaluated_designs = json.loads(evaluated_designs_str)
                job_data["context"]["evaluated_designs"] = evaluated_designs
                next_state = "DESIGN_SELECTION"

            elif state == "BUILDING":
                result = await run_agent("builder", job_data["context"])
                job_data["context"]["builder_result"] = result
                next_state = "STATIC_ANALYSIS"

            elif state == "STATIC_ANALYSIS":
                sentinel = AGENT_MAPPING["sentinel"]()
                sentinel_report = await asyncio.to_thread(sentinel.run, json.dumps(job_data["context"]))
                job_data["context"]["sentinel_report"] = json.loads(sentinel_report)
                if job_data["context"]["sentinel_report"].get("issues_found"):
                    next_state = "REFACTORING"
                else:
                    next_state = "INTEGRATING"

            elif state == "REFACTORING":
                refactoring_agent = AGENT_MAPPING["refactoring"]()
                refactoring_result = await asyncio.to_thread(
                    refactoring_agent.run, 
                    json.dumps(job_data["context"]["sentinel_report"]["summary"])
                )
                job_data["context"]["refactoring_result"] = json.loads(refactoring_result)
                if job_data["context"]["refactoring_result"].get("status") == "success":
                    next_state = "STATIC_ANALYSIS"
                else:
                    job_data["state"] = "ERROR"
                    job_data["error_message"] = "Refactoring failed to resolve issues."
                    next_state = "RETROSPECTION"

            elif state == "INTEGRATING":
                result = await run_agent("integrator", job_data["context"])
                job_data["context"]["integrator_result"] = result
                next_state = "DOC_WRITING"

            elif state == "DOC_WRITING":
                result = await run_agent("doc_writer", job_data["context"])
                job_data["context"]["doc_writer_result"] = result
                next_state = "INFRASTRUCTURE_GENERATION"

            elif state == "INFRASTRUCTURE_GENERATION":
                infra_agent = AGENT_MAPPING["infrastructure"]()
                infra_result = await asyncio.to_thread(
                    infra_agent.run, 
                    json.dumps(job_data["context"]["selected_design"])
                )
                job_data["context"]["infrastructure_result"] = json.loads(infra_result)
                next_state = "DEPLOYING"

            elif state == "DEPLOYING":
                deployment_agent = AGENT_MAPPING["deployment"]()
                deployment_result = await asyncio.to_thread(
                    deployment_agent.run, 
                    json.dumps(job_data["context"])
                )
                job_data["context"]["deployment_result"] = json.loads(deployment_result)
                if job_data["context"]["deployment_result"].get("status") == "success":
                    next_state = "MONITORING"
                else:
                    job_data["state"] = "ERROR"
                    job_data["error_message"] = "Deployment failed."
                    next_state = "RETROSPECTION"

            elif state == "MONITORING":
                runtime_monitor = ALL_TOOLS["runtime_monitor"]
                monitor_report = await asyncio.to_thread(
                    runtime_monitor._run, 
                    json.dumps({"application_id": job_id, "duration_minutes": 5})
                )
                monitor_report_json = json.loads(monitor_report)
                job_data["context"]["monitor_report"] = monitor_report_json

                if monitor_report_json.get("overall_health") == "unhealthy":
                    job_data["context"]["sentinel_report"] = {
                        "issues_found": True, 
                        "summary": "Runtime issues detected by monitor.", 
                        "report": monitor_report
                    }
                    next_state = "REFACTORING"
                else:
                    next_state = "COMPLETED"

            elif state == "PENDING_REFINEMENT":
                refinement_agent = AGENT_MAPPING["refinement"]()
                refinement_result = await asyncio.to_thread(
                    refinement_agent.run, 
                    json.dumps({
                        "input_feedback": job_data["context"]["human_feedback"], 
                        "input_context": job_data["context"]
                    })
                )
                job_data["context"]["refinement_result"] = json.loads(refinement_result)
                
                result = job_data["context"]["refinement_result"]
                if result.get("action_type") == "modify_context":
                    for key, value in result.get("modifications", {}).items():
                        job_data["context"][key] = value
                elif result.get("action_type") == "update_initial_prompt":
                    job_data["context"]["initial_prompt"] = result.get("modifications", {}).get(
                        "new_prompt", 
                        job_data["context"]["initial_prompt"]
                    )
                    # Reset context for re-evaluation
                    for key in ["generated_ideas", "selected_idea", "architect_result", 
                              "analyzer_result", "designer_results", "evaluated_designs", 
                              "selected_design"]:
                        job_data["context"].pop(key, None)

                next_state = result.get("next_state_suggestion", "ERROR")
                if next_state == "ERROR":
                    job_data["error_message"] = "Refinement agent could not determine next step."

            if next_state:
                logger.info("Job %s transitioning from %s to %s", job_id, state, next_state)
                job_data["state"] = next_state
                redis_client.set(job_id, json.dumps(job_data))
            
            if state in ["IDEA_SELECTION", "DESIGN_SELECTION", "PENDING_APPROVAL", "COMPLETED", "ERROR"]:
                if state in ["COMPLETED", "ERROR"]:
                    # Run retrospection
                    retrospection_agent = AGENT_MAPPING["retrospection"]()
                    retrospection_result = await asyncio.to_thread(
                        retrospection_agent.run, 
                        json.dumps(job_data["context"])
                    )
                    job_data["context"]["retrospection_result"] = json.loads(retrospection_result)
                    
                    # Run prompt optimization
                    prompt_optimizer_agent = AGENT_MAPPING["prompt_optimizer"]()
                    optimized_prompts_result = await asyncio.to_thread(
                        prompt_optimizer_agent.run, 
                        json.dumps(job_data["context"]["retrospection_result"])
                    )
                    job_data["context"]["optimized_prompts_result"] = json.loads(optimized_prompts_result)
                    
                    # Save final state
                    redis_client.set(job_id, json.dumps(job_data))
                    logger.info("Job %s completed with state: %s", job_id, state)
                break

        except Exception as e:
            logger.error("Error in workflow manager for job %s: %s", job_id, str(e), exc_info=True)
            try:
                job_data["state"] = "ERROR"
                job_data["error_message"] = f"Workflow error: {str(e)}"
                redis_client.set(job_id, json.dumps(job_data))
            except:
                logger.error("Failed to update job state after error", exc_info=True)
            break

@app.post("/start_project", tags=["Projects"])
async def start_project(
    prompt: str, 
    github_url: Optional[str] = None, 
    pdf_path: Optional[str] = None, 
    files_to_ingest: List[Dict[str, str]] = [], 
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Start a new project generation workflow."""
    try:
        job_id = f"job_{redis_client.dbsize() + 1}"
        logger.info("Starting new project with job_id: %s", job_id)
        logger.debug("Project details - prompt: %s, github_url: %s, pdf_path: %s, files: %s", 
                    prompt, github_url, pdf_path, files_to_ingest)
        
        initial_context = {
            "initial_prompt": prompt,
            "github_url": github_url,
            "pdf_path": pdf_path,
            "files_to_ingest": files_to_ingest
        }
        job_data = {"job_id": job_id, "state": "INGESTION", "context": initial_context}
        redis_client.set(job_id, json.dumps(job_data))
        background_tasks.add_task(workflow_manager, job_id)
        
        return {"message": "Project generation started.", "job_id": job_id}
    except Exception as e:
        logger.error("Failed to start project: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jobs/{job_id}/select_idea", tags=["Job Control"])
async def select_idea(job_id: str, idea_index: int, background_tasks: BackgroundTasks):
    """Select a generated project idea for further development."""
    try:
        logger.info("Selecting idea %d for job %s", idea_index, job_id)
        job_data_str = redis_client.get(job_id)
        if not job_data_str:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = json.loads(job_data_str)
        if job_data["state"] != "IDEA_SELECTION":
            raise HTTPException(status_code=400, detail=f"Job is not in IDEA_SELECTION state.")

        generated_ideas = job_data["context"].get("generated_ideas", [])
        if not (0 <= idea_index < len(generated_ideas)):
            raise HTTPException(status_code=400, detail="Invalid idea index.")

        selected_idea = generated_ideas[idea_index]
        job_data["context"]["selected_idea"] = selected_idea
        job_data["state"] = "ARCHITECT_ANALYSIS"
        redis_client.set(job_id, json.dumps(job_data))
        background_tasks.add_task(workflow_manager, job_id)
        
        return {"message": "Idea selected. Architect analysis initiated."}
    except Exception as e:
        logger.error("Error selecting idea for job %s: %s", job_id, str(e), exc_info=True)
        raise

@app.post("/jobs/{job_id}/select_design", tags=["Job Control"])
async def select_design(job_id: str, design_index: int, background_tasks: BackgroundTasks):
    """Select a design for the project from multiple generated designs."""
    try:
        logger.info("Selecting design %d for job %s", design_index, job_id)
        job_data_str = redis_client.get(job_id)
        if not job_data_str:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = json.loads(job_data_str)
        if job_data["state"] != "DESIGN_SELECTION":
            raise HTTPException(status_code=400, detail=f"Job is not in DESIGN_SELECTION state.")

        evaluated_designs = job_data["context"].get("evaluated_designs", [])
        if not (0 <= design_index < len(evaluated_designs)):
            raise HTTPException(status_code=400, detail="Invalid design index.")

        selected_design = evaluated_designs[design_index]
        job_data["context"]["selected_design"] = selected_design
        job_data["state"] = "PENDING_APPROVAL"
        redis_client.set(job_id, json.dumps(job_data))
        background_tasks.add_task(workflow_manager, job_id)
        
        return {"message": "Design selected. Awaiting final approval."}
    except Exception as e:
        logger.error("Error selecting design for job %s: %s", job_id, str(e), exc_info=True)
        raise

@app.post("/jobs/{job_id}/approve", tags=["Job Control"])
async def approve_job(job_id: str, background_tasks: BackgroundTasks):
    """Approve the project and start the build process."""
    try:
        logger.info("Approving job %s", job_id)
        job_data_str = redis_client.get(job_id)
        if not job_data_str:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = json.loads(job_data_str)
        if job_data["state"] != "PENDING_APPROVAL":
            raise HTTPException(status_code=400, detail=f"Job is not in PENDING_APPROVAL state.")

        job_data["state"] = "BUILDING"
        redis_client.set(job_id, json.dumps(job_data))
        background_tasks.add_task(workflow_manager, job_id)
        
        return {"message": "Job approved. Build process initiated."}
    except Exception as e:
        logger.error("Error approving job %s: %s", job_id, str(e), exc_info=True)
        raise

@app.post("/jobs/{job_id}/feedback", tags=["Job Control"])
async def provide_feedback(job_id: str, feedback: str, background_tasks: BackgroundTasks):
    """Provide feedback on the project, leading to refinement or error correction."""
    try:
        logger.info("Receiving feedback for job %s", job_id)
        job_data_str = redis_client.get(job_id)
        if not job_data_str:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = json.loads(job_data_str)
        if job_data["state"] not in ["PENDING_APPROVAL", "ERROR"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Feedback can only be provided in PENDING_APPROVAL or ERROR states."
            )

        job_data["context"]["human_feedback"] = feedback
        job_data["state"] = "PENDING_REFINEMENT"
        redis_client.set(job_id, json.dumps(job_data))
        background_tasks.add_task(workflow_manager, job_id)
        
        return {"message": "Feedback received. Initiating refinement process."}
    except Exception as e:
        logger.error("Error providing feedback for job %s: %s", job_id, str(e), exc_info=True)
        raise

@app.get("/status/{job_id}", tags=["Status"])
async def get_status(job_id: str):
    """Get the current status of the job."""
    try:
        logger.debug("Fetching status for job %s", job_id)
        job_data_str = redis_client.get(job_id)
        if not job_data_str:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return json.loads(job_data_str)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting status for job %s: %s", job_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))