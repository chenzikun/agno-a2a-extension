from typing import Dict, List, Optional

from agno.agent.agent import Agent
from agno.team.team import Team
from agno.workflow.workflow import Workflow


def get_agent_by_id(agent_id: str, agents: Optional[Dict[str, Agent] or List[Agent]] = None) -> Optional[Agent]:
    """
    根据ID获取Agent实例
    
    Args:
        agent_id: 代理ID
        agents: 代理字典或列表
        
    Returns:
        Agent: 找到的代理实例，未找到则返回None
    """
    if not agents:
        return None
        
    # 如果是字典
    if isinstance(agents, dict):
        return agents.get(agent_id)
        
    # 如果是列表
    if isinstance(agents, list):
        for agent in agents:
            if getattr(agent, "agent_id", None) == agent_id:
                return agent
                
    return None


def get_team_by_id(team_id: str, teams: Optional[Dict[str, Team] or List[Team]] = None) -> Optional[Team]:
    """
    根据ID获取Team实例
    
    Args:
        team_id: 团队ID
        teams: 团队字典或列表
        
    Returns:
        Team: 找到的团队实例，未找到则返回None
    """
    if not teams:
        return None
        
    # 如果是字典
    if isinstance(teams, dict):
        return teams.get(team_id)
        
    # 如果是列表
    if isinstance(teams, list):
        for team in teams:
            if getattr(team, "team_id", None) == team_id:
                return team
                
    return None


def get_workflow_by_id(workflow_id: str, workflows: Optional[Dict[str, Workflow] or List[Workflow]] = None) -> Optional[Workflow]:
    """
    根据ID获取Workflow实例
    
    Args:
        workflow_id: 工作流ID
        workflows: 工作流字典或列表
        
    Returns:
        Workflow: 找到的工作流实例，未找到则返回None
    """
    if not workflows:
        return None
        
    # 如果是字典
    if isinstance(workflows, dict):
        return workflows.get(workflow_id)
        
    # 如果是列表
    if isinstance(workflows, list):
        for workflow in workflows:
            if getattr(workflow, "workflow_id", None) == workflow_id:
                return workflow
                
    return None 