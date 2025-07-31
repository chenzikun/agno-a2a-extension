import base64
from io import BytesIO
from typing import Optional, List

from fastapi import UploadFile

from agno.media import Audio, Image, Video, File as FileMedia


async def process_image(file: UploadFile) -> Image:
    """
    处理上传的图像文件，转换为Base64编码
    
    Args:
        file: 上传的文件对象
        
    Returns:
        Image: Base64编码的图像对象
    """
    contents = await file.read()
    base64_image = base64.b64encode(contents).decode("utf-8")
    return Image(
        data=base64_image,
        mime_type=file.content_type or "image/png"
    )


async def process_audio(file: UploadFile) -> Audio:
    """
    处理上传的音频文件，转换为Base64编码
    
    Args:
        file: 上传的文件对象
        
    Returns:
        Audio: Base64编码的音频对象
    """
    contents = await file.read()
    base64_audio = base64.b64encode(contents).decode("utf-8")
    return Audio(
        data=base64_audio,
        mime_type=file.content_type or "audio/mpeg"
    )


async def process_video(file: UploadFile) -> Video:
    """
    处理上传的视频文件，转换为Base64编码
    
    Args:
        file: 上传的文件对象
        
    Returns:
        Video: Base64编码的视频对象
    """
    contents = await file.read()
    base64_video = base64.b64encode(contents).decode("utf-8")
    return Video(
        data=base64_video,
        mime_type=file.content_type or "video/mp4"
    )


async def process_document(file: UploadFile) -> Optional[FileMedia]:
    """
    处理上传的文档文件，转换为FileMedia对象
    
    Args:
        file: 上传的文件对象
        
    Returns:
        FileMedia: 文档对象，如果处理失败则返回None
    """
    try:
        contents = await file.read()
        document_file = BytesIO(contents)
        document_file.name = file.filename or "document"
        
        return FileMedia(
            data=document_file,
            mime_type=file.content_type or "application/octet-stream",
            filename=file.filename or "document"
        )
    except Exception as e:
        print(f"处理文档时出错: {e}")
        return None


def format_tools(tools: List) -> List[dict]:
    """
    格式化工具列表为API响应格式
    
    Args:
        tools: 原始工具列表
        
    Returns:
        List[dict]: 格式化后的工具列表
    """
    formatted_tools = []
    for tool in tools:
        tool_dict = {}
        
        # 获取工具名称
        if hasattr(tool, "name"):
            tool_dict["name"] = tool.name
        elif hasattr(tool, "__name__"):
            tool_dict["name"] = tool.__name__
        else:
            tool_dict["name"] = str(tool)
            
        # 获取工具描述
        if hasattr(tool, "description"):
            tool_dict["description"] = tool.description
        elif hasattr(tool, "__doc__") and tool.__doc__:
            tool_dict["description"] = tool.__doc__.strip()
        else:
            tool_dict["description"] = f"Tool: {tool_dict['name']}"
            
        # 获取工具参数
        if hasattr(tool, "args_schema"):
            schema_dict = {}
            if hasattr(tool.args_schema, "schema"):
                schema_dict = tool.args_schema.schema()
            elif hasattr(tool.args_schema, "__dict__"):
                schema_dict = tool.args_schema.__dict__
                
            if "properties" in schema_dict:
                tool_dict["parameters"] = schema_dict["properties"]
                
        formatted_tools.append(tool_dict)
        
    return formatted_tools


def get_session_title(session):
    """
    获取会话标题
    
    Args:
        session: 会话对象
        
    Returns:
        str: 会话标题
    """
    # 优先使用自定义会话名称
    if hasattr(session, "session_data") and session.session_data:
        session_name = session.session_data.get("session_name")
        if session_name:
            return session_name
    
    # 尝试从记忆中获取第一个用户消息
    if hasattr(session, "memory") and session.memory:
        messages = session.memory.get("messages", [])
        for message in messages:
            if message.get("role") == "user":
                content = message.get("content")
                if content and isinstance(content, str):
                    # 截取前30个字符作为标题
                    title = content[:30]
                    if len(content) > 30:
                        title += "..."
                    return title
    
    # 默认标题
    return f"会话 {session.session_id[:8]}"


def get_session_title_from_team_session(session):
    """获取团队会话标题"""
    return get_session_title(session)


def get_session_title_from_workflow_session(session):
    """获取工作流会话标题"""
    return get_session_title(session) 