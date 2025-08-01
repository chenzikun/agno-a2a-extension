import json
from dataclasses import asdict
from typing import AsyncGenerator, List, Optional
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from agno_a2a_ext.apis.factory import ai_factory
from agno.media import File as FileMedia
from agno_a2a_ext.apis.playground.operator import (
    get_session_title,
    get_session_title_from_workflow_session,
)
from agno_a2a_ext.apis.playground.schemas import (
    AgentModel,
    MemoryResponse,
    TeamGetResponse,
    WorkflowGetResponse,
    WorkflowRenameRequest,
    WorkflowRunRequest,
    WorkflowSessionResponse,
    WorkflowsGetResponse,
)
from agno.run.team import TeamRunResponse
from agno.storage.session.agent import AgentSession
from agno.storage.session.workflow import WorkflowSession
from agno.team.team import Team
from agno.utils.log import logger

workflows_router = APIRouter(prefix="", tags=["workflows"])


@workflows_router.get("/workflows", response_model=List[WorkflowsGetResponse])
async def get_workflows():
    current_workflows = ai_factory.get_all_workflows()
    if current_workflows is None:
        return []

    return [
        WorkflowsGetResponse(
            workflow_id=str(workflow.workflow_id),
            name=workflow.name,
            description=workflow.description,
        )
        for workflow in current_workflows
    ]


@workflows_router.get("/workflows/{workflow_id}", response_model=WorkflowGetResponse)
async def get_workflow(workflow_id: str):

    workflow = ai_factory.get_workflow_by_id(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return WorkflowGetResponse(
        workflow_id=workflow.workflow_id,
        name=workflow.name,
        description=workflow.description,
        parameters=workflow._run_parameters or {},
        storage=workflow.storage.__class__.__name__ if workflow.storage else None,
    )


@workflows_router.post("/workflows/{workflow_id}/runs")
async def create_workflow_run(workflow_id: str, body: WorkflowRunRequest):
    # Retrieve the workflow by ID
    workflow = ai_factory.get_workflow_by_id(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if body.session_id is not None:
        logger.debug(f"Continuing session: {body.session_id}")
    else:
        logger.debug("Creating new session")

    # Create a new instance of this workflow
    new_workflow_instance = workflow.deep_copy(update={"workflow_id": workflow_id, "session_id": body.session_id})
    new_workflow_instance.user_id = body.user_id
    new_workflow_instance.session_name = None

    # Return based on the response type
    try:
        if new_workflow_instance._run_return_type == "RunResponse":
            # Return as a normal response
            return new_workflow_instance.run(**body.input)
        else:
            # Return as a streaming response
            return StreamingResponse(
                (json.dumps(asdict(result)) for result in new_workflow_instance.run(**body.input)),
                media_type="text/event-stream",
            )
    except Exception as e:
        # Handle unexpected runtime errors
        raise HTTPException(status_code=500, detail=f"Error running workflow: {str(e)}")


@workflows_router.get("/workflows/{workflow_id}/sessions", response_model=List[WorkflowSessionResponse])
async def get_all_workflow_sessions(workflow_id: str, user_id: Optional[str] = Query(None, min_length=1)):
    # Retrieve the workflow by ID
    workflow = ai_factory.get_workflow_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Ensure storage is enabled for the workflow
    if not workflow.storage:
        raise HTTPException(status_code=404, detail="Workflow does not have storage enabled")

    # Retrieve all sessions for the given workflow and user
    try:
        all_workflow_sessions: List[WorkflowSession] = workflow.storage.get_all_sessions(
            user_id=user_id, entity_id=workflow_id
        )  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sessions: {str(e)}")

    # Return the sessions
    return [
        WorkflowSessionResponse(
            title=get_session_title_from_workflow_session(session),
            session_id=session.session_id,
            session_name=session.session_data.get("session_name") if session.session_data else None,
            created_at=session.created_at,
        )
        for session in all_workflow_sessions
    ]


@workflows_router.get("/workflows/{workflow_id}/sessions/{session_id}")
async def get_workflow_session(
        workflow_id: str, session_id: str, user_id: Optional[str] = Query(None, min_length=1)
):
    workflow = ai_factory.get_workflow_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Ensure storage is enabled for the workflow
    if not workflow.storage:
        raise HTTPException(status_code=404, detail="Workflow does not have storage enabled")

    # Retrieve the specific session
    try:
        workflow_session: Optional[WorkflowSession] = workflow.storage.read(session_id, user_id)  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")

    if not workflow_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Return the session
    return workflow_session


@workflows_router.post("/workflows/{workflow_id}/sessions/{session_id}/rename")
async def rename_workflow_session(workflow_id: str, session_id: str, body: WorkflowRenameRequest):
    workflow = ai_factory.get_workflow_by_id(workflow_id)

    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow.session_id = session_id
    workflow.rename_session(body.name)
    return JSONResponse(content={"message": f"successfully renamed workflow {workflow.name}"})


@workflows_router.delete("/workflows/{workflow_id}/sessions/{session_id}")
async def delete_workflow_session(workflow_id: str, session_id: str):
    workflow = ai_factory.get_workflow_by_id(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow.delete_session(session_id)
    return JSONResponse(content={"message": f"successfully deleted workflow {workflow.name}"})