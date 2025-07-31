from typing import Any, Dict, Generator, List, Optional, cast

from agno.agent.agent import Agent, RunResponse
from agno.media import Audio, Image, Video
from agno.media import File as FileMedia

from agno.run.response import RunEvent
from agno.run.team import TeamRunResponse
from agno.team.team import Team


def chat_response_streamer(
        agent: Agent,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        images: Optional[List[Image]] = None,
        audio: Optional[List[Audio]] = None,
        videos: Optional[List[Video]] = None,
) -> Generator:
    try:
        run_response = agent.run(
            message,
            session_id=session_id,
            user_id=user_id,
            images=images,
            audio=audio,
            videos=videos,
            stream=True,
            stream_intermediate_steps=True,
        )
        for run_response_chunk in run_response:
            run_response_chunk = cast(RunResponse, run_response_chunk)
            yield run_response_chunk.to_json()
    except Exception as e:
        error_response = RunResponse(
            content=str(e),
            event=RunEvent.run_error,
        )
        yield error_response.to_json()
        return


def team_chat_response_streamer(
        team: Team,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        images: Optional[List[Image]] = None,
        audio: Optional[List[Audio]] = None,
        videos: Optional[List[Video]] = None,
        files: Optional[List[FileMedia]] = None,
) -> Generator:
    try:
        run_response = team.run(
            message,
            session_id=session_id,
            user_id=user_id,
            images=images,
            audio=audio,
            videos=videos,
            files=files,
            stream=True,
            stream_intermediate_steps=True,
        )
        for run_response_chunk in run_response:
            run_response_chunk = cast(TeamRunResponse, run_response_chunk)
            yield run_response_chunk.to_json()
    except Exception as e:
        error_response = TeamRunResponse(
            content=str(e),
            event=RunEvent.run_error,
        )
        yield error_response.to_json()
        return
