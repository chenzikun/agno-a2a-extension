from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from agents.apis.factory import ai_factory
from agno.media import Audio, Image, Video
from agno.media import File as FileMedia
from agno.memory.v2 import Memory
from agents.apis.playground.operator import (
    get_session_title_from_team_session,
)
from agents.apis.playground.schemas import (
    MemoryResponse,
    TeamGetResponse,
    TeamRenameRequest,
    TeamSessionResponse,
)
from agents.apis.playground.utils import process_audio, process_document, process_image, process_video
from agno.storage.session.team import TeamSession
from agno.utils.log import logger

from agents.apis.routers._async.chat_response import team_chat_response_streamer


teams_router = APIRouter(prefix="", tags=["teams"])


@teams_router.get("/teams")
async def get_teams():
    teams = ai_factory.get_all_teams()
    return [TeamGetResponse.from_team(team) for team in teams]


@teams_router.get("/teams/{team_id}")
async def get_team(team_id: str):
    team = ai_factory.get_team_by_id(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    return TeamGetResponse.from_team(team)


@teams_router.post("/teams/{team_id}/runs")
async def create_team_run(
        team_id: str,
        message: str = Form(...),
        stream: bool = Form(True),
        monitor: bool = Form(True),
        session_id: Optional[str] = Form(None),
        user_id: Optional[str] = Form(None),
        files: Optional[List[UploadFile]] = File(None),
):
    logger.debug(f"Creating team run: {message} {session_id} {monitor} {user_id} {team_id} {files}")

    team = ai_factory.get_team_by_id(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    if session_id is not None and session_id != "":
        logger.debug(f"Continuing session: {session_id}")
    else:
        logger.debug("Creating new session")
        session_id = str(uuid4())

    if monitor:
        team.monitoring = True
    else:
        team.monitoring = False

    base64_images: List[Image] = []
    base64_audios: List[Audio] = []
    base64_videos: List[Video] = []
    document_files: List[FileMedia] = []

    if files:
        for file in files:
            if file.content_type in ["image/png", "image/jpeg", "image/jpg", "image/webp"]:
                try:
                    base64_image = process_image(file)
                    base64_images.append(base64_image)
                except Exception as e:
                    logger.error(f"Error processing image {file.filename}: {e}")
                    continue
            elif file.content_type in ["audio/wav", "audio/mp3", "audio/mpeg"]:
                try:
                    base64_audio = process_audio(file)
                    base64_audios.append(base64_audio)
                except Exception as e:
                    logger.error(f"Error processing audio {file.filename}: {e}")
                    continue
            elif file.content_type in [
                "video/x-flv",
                "video/quicktime",
                "video/mpeg",
                "video/mpegs",
                "video/mpgs",
                "video/mpg",
                "video/mpg",
                "video/mp4",
                "video/webm",
                "video/wmv",
                "video/3gpp",
            ]:
                try:
                    base64_video = process_video(file)
                    base64_videos.append(base64_video)
                except Exception as e:
                    logger.error(f"Error processing video {file.filename}: {e}")
                    continue
            elif file.content_type in [
                "application/pdf",
                "text/csv",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain",
                "application/json",
            ]:
                document_file = process_document(file)
                if document_file is not None:
                    document_files.append(document_file)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")

    if stream and team.is_streamable:
        return StreamingResponse(
            team_chat_response_streamer(
                team,
                message,
                session_id=session_id,
                user_id=user_id,
                images=base64_images if base64_images else None,
                audio=base64_audios if base64_audios else None,
                videos=base64_videos if base64_videos else None,
                files=document_files if document_files else None,
            ),
            media_type="text/event-stream",
        )
    else:
        run_response = await team.arun(
            message=message,
            session_id=session_id,
            user_id=user_id,
            images=base64_images if base64_images else None,
            audio=base64_audios if base64_audios else None,
            videos=base64_videos if base64_videos else None,
            files=document_files if document_files else None,
            stream=False,
        )
        return run_response.to_dict()


@teams_router.get("/teams/{team_id}/sessions", response_model=List[TeamSessionResponse])
async def get_all_team_sessions(team_id: str, user_id: Optional[str] = Query(None, min_length=1)):
    team = ai_factory.get_team_by_id(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.storage is None:
        raise HTTPException(status_code=404, detail="Team does not have storage enabled")

    try:
        all_team_sessions: List[TeamSession] = team.storage.get_all_sessions(user_id=user_id,
                                                                             entity_id=team_id)  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sessions: {str(e)}")

    team_sessions: List[TeamSessionResponse] = []
    for session in all_team_sessions:
        title = get_session_title_from_team_session(session)
        team_sessions.append(
            TeamSessionResponse(
                title=title,
                session_id=session.session_id,
                session_name=session.session_data.get("session_name") if session.session_data else None,
                created_at=session.created_at,
            )
        )
    return team_sessions


@teams_router.get("/teams/{team_id}/sessions/{session_id}")
async def get_team_session(team_id: str, session_id: str, user_id: Optional[str] = Query(None, min_length=1)):
    team = ai_factory.get_team_by_id(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.storage is None:
        raise HTTPException(status_code=404, detail="Team does not have storage enabled")

    try:
        team_session: Optional[TeamSession] = team.storage.read(session_id, user_id)  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")

    if not team_session:
        raise HTTPException(status_code=404, detail="Session not found")

    team_session_dict = team_session.to_dict()
    if team_session.memory is not None:
        runs = team_session.memory.get("runs")
        if runs is not None:
            first_run = runs[0]
            # This is how we know it is a RunResponse
            if "content" in first_run:
                team_session_dict["runs"] = []
                for run in runs:
                    first_user_message = None
                    for msg in run.get("messages", []):
                        if msg.get("role") == "user" and msg.get("from_history", False) is False:
                            first_user_message = msg
                            break
                    # Remove the memory from the response
                    team_session_dict.pop("memory", None)
                    team_session_dict["runs"].append(
                        {
                            "message": first_user_message,
                            "response": run,
                        }
                    )

    return team_session_dict


@teams_router.post("/teams/{team_id}/sessions/{session_id}/rename")
async def rename_team_session(team_id: str, session_id: str, body: TeamRenameRequest):
    team = ai_factory.get_team_by_id(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.storage is None:
        raise HTTPException(status_code=404, detail="Team does not have storage enabled")

    all_team_sessions: List[TeamSession] = team.storage.get_all_sessions(user_id=body.user_id,
                                                                         entity_id=team_id)  # type: ignore
    for session in all_team_sessions:
        if session.session_id == session_id:
            team.rename_session(body.name, session_id=session_id)
            return JSONResponse(content={"message": f"successfully renamed team session {body.name}"})

    raise HTTPException(status_code=404, detail="Session not found")


@teams_router.delete("/teams/{team_id}/sessions/{session_id}")
async def delete_team_session(team_id: str, session_id: str, user_id: Optional[str] = Query(None, min_length=1)):
    team = ai_factory.get_team_by_id(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.storage is None:
        raise HTTPException(status_code=404, detail="Team does not have storage enabled")

    all_team_sessions: List[TeamSession] = team.storage.get_all_sessions(user_id=user_id,
                                                                         entity_id=team_id)  # type: ignore
    for session in all_team_sessions:
        if session.session_id == session_id:
            team.delete_session(session_id)
            return JSONResponse(content={"message": f"successfully deleted team session {session_id}"})

    raise HTTPException(status_code=404, detail="Session not found")


@teams_router.get("/team/{team_id}/memories")
async def get_team_memories(team_id: str, user_id: str = Query(..., min_length=1)):
    team = ai_factory.get_team_by_id(team_id)
    if team is None:
        return JSONResponse(status_code=404, content="Teem not found.")

    if team.memory is None:
        return JSONResponse(status_code=404, content="Team does not have memory enabled.")

    if isinstance(team.memory, Memory):
        memories = team.memory.get_user_memories(user_id=user_id)
        return [
            MemoryResponse(memory=memory.memory, topics=memory.topics, last_updated=memory.last_updated)
            for memory in memories
        ]
    else:
        return []