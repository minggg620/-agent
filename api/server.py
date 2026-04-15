"""
FastAPI 服务器 - 为 Zero Realm Social Agent 提供 Web API 接口
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.social_arena_agent import get_social_arena_agent

app = FastAPI(
    title="Zero Realm Social Agent API",
    description="高性能社交策略 Agent 的 Web API 接口",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    """Agent 请求模型"""
    mode: str = "passive"  # passive, active, competitive, defensive
    challenge: str = "monitor"  # injection, credibility, influence, monitor
    message: str = ""
    objectives: Optional[List[str]] = None
    session_context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Agent 响应模型"""
    success: bool
    session_id: str
    agent_id: str
    current_mode: str
    active_challenge: str
    messages: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
    error: Optional[str] = None
    timestamp: str


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Zero Realm Social Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "run_agent": "/api/v1/run",
            "health": "/api/v1/health",
            "modes": "/api/v1/modes",
            "challenges": "/api/v1/challenges"
        }
    }


@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_ready": True
    }


@app.get("/api/v1/modes")
async def get_modes():
    """获取可用的 Agent 模式"""
    return {
        "modes": [
            {"value": "passive", "description": "监控和观察模式"},
            {"value": "active", "description": "主动互动模式"},
            {"value": "competitive", "description": "完全竞争模式"},
            {"value": "defensive", "description": "防御和保护模式"}
        ]
    }


@app.get("/api/v1/challenges")
async def get_challenges():
    """获取可用的挑战类型"""
    return {
        "challenges": [
            {"value": "injection", "description": "对话注入挑战"},
            {"value": "credibility", "description": "信誉建立挑战"},
            {"value": "influence", "description": "影响力扩展挑战"},
            {"value": "monitor", "description": "信息监控挑战"}
        ]
    }


@app.post("/api/v1/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    """运行 Agent"""
    try:
        # 获取 agent 实例
        agent = get_social_arena_agent()
        
        # 准备输入数据
        input_data = {
            "mode": request.mode,
            "challenge": request.challenge,
            "session_context": {
                "objectives": request.objectives or ["gather_intelligence", "build_reputation"],
                "message": request.message
            }
        }
        
        if request.session_context:
            input_data["session_context"].update(request.session_context)
        
        # 运行 agent
        result = await agent.run(input_data)
        
        # 构建响应
        response = AgentResponse(
            success=True,
            session_id=result.get("session_id", ""),
            agent_id=result.get("agent_id", ""),
            current_mode=str(result.get("current_mode", "")),
            active_challenge=str(result.get("active_challenge", "")),
            messages=result.get("messages", []),
            performance_metrics=result.get("performance_metrics", {}),
            timestamp=datetime.now().isoformat()
        )
        
        return response
        
    except Exception as e:
        # 错误处理
        return AgentResponse(
            success=False,
            session_id="",
            agent_id="",
            current_mode="",
            active_challenge="",
            messages=[],
            performance_metrics={},
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
