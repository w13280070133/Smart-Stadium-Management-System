"""
Agent Chat Router

Provides RESTful API endpoints for frontend to interact with AI Agent.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..agent.core import chat_with_agent


# ============================================================================
# Pydantic Models
# ============================================================================

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户输入的消息", min_length=1)
    session_id: Optional[str] = Field(None, description="会话 ID，用于区分不同用户或会话")
    member_id: Optional[int] = Field(None, description="会员 ID，用于关联订单到具体用户")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "明天下午有羽毛球场吗？",
                "session_id": "user-123",
                "member_id": 1
            }
        }


class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str = Field(..., description="AI 助手的回复")
    session_id: str = Field(..., description="会话 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reply": "让我帮您查询一下明天下午的羽毛球场...",
                "session_id": "user-123"
            }
        }


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/agent", tags=["AI Agent"])


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    与 AI 助手对话（流式响应）
    
    用户发送自然语言消息，AI 助手会自动理解意图并调用相应的工具
    （如查询场地、获取规则等），然后以流式方式返回友好的回复。
    
    Args:
        request: 聊天请求，包含用户消息和可选的会话 ID
    
    Returns:
        StreamingResponse: 流式文本响应
    
    Raises:
        HTTPException(400): 请求参数错误
        HTTPException(500): 服务器内部错误
    
    Example:
        Request:
        ```json
        {
            "message": "明天下午有羽毛球场吗？",
            "session_id": "user-123",
            "member_id": 1
        }
        ```
        
        Response: 流式文本输出
    """
    # 打印调试信息
    print(f"[AgentChatRouter] 收到请求（流式）")
    print(f"[AgentChatRouter] Message: {request.message}")
    print(f"[AgentChatRouter] Session ID: {request.session_id}")
    print(f"[AgentChatRouter] Member ID: {request.member_id}")
    
    # 验证消息不为空
    if not request.message or not request.message.strip():
        print(f"[AgentChatRouter] 错误：消息内容为空")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="消息内容不能为空"
        )
    
    # 生成或使用提供的 session_id
    session_id = request.session_id or f"session-{uuid.uuid4()}"
    
    try:
        # 定义流式生成器
        async def event_generator():
            try:
                # 调用 Agent 进行流式对话（chat_with_agent 现在总是流式的）
                async for token in chat_with_agent(
                    user_input=request.message.strip(),
                    session_id=session_id,
                    member_id=request.member_id
                ):
                    if token:  # 只发送非空内容
                        yield token
                        
            except Exception as e:
                print(f"[AgentChatRouter] 流式生成错误: {e}")
                yield f"\n\n抱歉，处理您的请求时出现错误。"
        
        # 返回流式响应（纯文本流）
        return StreamingResponse(
            event_generator(),
            media_type="text/plain; charset=utf-8"
        )
    
    except ValueError as e:
        # 参数验证错误
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"请求参数错误: {str(e)}"
        )
    
    except Exception as e:
        # 其他错误
        print(f"[AgentChatRouter] 错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理您的请求时出现错误，请稍后再试"
        )


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_session(session_id: str):
    """
    重置会话历史
    
    清空指定会话的对话历史，开始新的对话。
    
    Args:
        session_id: 要重置的会话 ID
    
    Returns:
        204 No Content
    
    Example:
        Request:
        ```
        POST /api/agent/reset?session_id=user-123
        ```
    """
    try:
        from ..agent.core import get_agent_service
        
        agent = get_agent_service()
        await agent.reset_conversation(session_id)
        
        return None
    
    except Exception as e:
        print(f"[AgentChatRouter] 重置会话错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置会话失败"
        )


@router.get("/health")
async def health_check():
    """
    健康检查
    
    检查 Agent 服务是否正常运行。
    
    Returns:
        健康状态信息
    """
    try:
        from ..agent.core import get_agent_service
        
        agent = get_agent_service()
        
        return {
            "status": "healthy",
            "service": "AI Agent",
            "model": agent.model,
            "base_url": agent.base_url,
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
