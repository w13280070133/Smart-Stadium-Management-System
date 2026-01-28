"""
AI Agent Core Service

This module implements the core logic for handling natural language conversations
with C-end users. It uses OpenAI-compatible API (DeepSeek) with function calling
to automatically invoke tools defined in tools.py.
"""
import os
import json
import time
import logging
from datetime import datetime
from threading import Lock
from typing import Dict, List, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI

from .tools import AVAILABLE_TOOLS, execute_tool, get_tool_schemas
from ..config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Session Management (In-Memory with Auto-Cleanup)
# ============================================================================

# 全局对话历史存储：{session_id: {"messages": [...], "last_access": timestamp}}
_conversation_history: Dict[str, Dict[str, Any]] = {}
_history_lock = Lock()

# 会话过期时间（秒）：1小时未活跃则清理
SESSION_EXPIRE_SECONDS = 3600
# 最大会话数量限制，防止内存溢出
MAX_SESSIONS = 1000


def _cleanup_expired_sessions() -> None:
    """清理过期的会话（内部函数，需在锁内调用）"""
    now = time.time()
    expired_keys = [
        k for k, v in _conversation_history.items()
        if now - v.get("last_access", 0) > SESSION_EXPIRE_SECONDS
    ]
    for k in expired_keys:
        del _conversation_history[k]
    if expired_keys:
        logger.info(f"[AgentService] 清理了 {len(expired_keys)} 个过期会话")


def get_conversation_history(session_id: str) -> List[Dict[str, Any]]:
    """获取会话历史（带自动清理和容量限制）"""
    with _history_lock:
        now = time.time()
        
        # 定期清理过期会话
        _cleanup_expired_sessions()
        
        # 检查会话数量限制
        if session_id not in _conversation_history and len(_conversation_history) >= MAX_SESSIONS:
            # 删除最旧的会话
            oldest_key = min(_conversation_history.keys(), 
                           key=lambda k: _conversation_history[k].get("last_access", 0))
            del _conversation_history[oldest_key]
            logger.warning(f"[AgentService] 达到最大会话数限制，删除最旧会话: {oldest_key}")
        
        if session_id not in _conversation_history:
            _conversation_history[session_id] = {"messages": [], "last_access": now}
        
        _conversation_history[session_id]["last_access"] = now
        return _conversation_history[session_id]["messages"]


def add_message(session_id: str, message: Dict[str, Any]) -> None:
    """添加消息到会话历史"""
    history = get_conversation_history(session_id)
    history.append(message)


def clear_conversation_history(session_id: str) -> None:
    """清空会话历史"""
    with _history_lock:
        if session_id in _conversation_history:
            _conversation_history[session_id] = {"messages": [], "last_access": time.time()}


# ============================================================================
# Agent Service
# ============================================================================

class AgentService:
    """
    AI Agent 服务类
    
    负责处理用户的自然语言对话，自动调用工具查询数据库，
    并生成友好的回复。
    
    核心流程：
    1. 接收用户输入
    2. 调用 LLM（带工具定义）
    3. 如果 LLM 返回工具调用，执行工具并获取结果
    4. 将工具结果返回给 LLM，生成最终回复
    5. 返回回复给用户
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
    ):
        """
        初始化 Agent 服务
        
        Args:
            api_key: DeepSeek API Key，如果不提供则从环境变量或配置读取
            base_url: API 基础 URL
            model: 使用的模型名称
        """
        # 从参数、配置或环境变量获取 API Key
        self.api_key = api_key or settings.DEEPSEEK_API_KEY or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DeepSeek API Key 未配置。请在 .env 文件中设置 DEEPSEEK_API_KEY "
                "或在初始化时传入 api_key 参数"
            )
        
        self.base_url = base_url
        self.model = model
        
        # 初始化 OpenAI 异步客户端
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
        # 获取工具定义（转换为 OpenAI Function Calling 格式）
        self.tools = self._convert_tools_to_openai_format()
        
        print(f"[AgentService] 初始化完成")
        print(f"[AgentService] Base URL: {self.base_url}")
        print(f"[AgentService] Model: {self.model}")
        print(f"[AgentService] 可用工具数量: {len(self.tools)}")
    
    def _convert_tools_to_openai_format(self) -> List[Dict[str, Any]]:
        """
        将工具定义转换为 OpenAI Function Calling 格式
        
        Returns:
            OpenAI 格式的工具定义列表
        """
        tools = []
        for tool_name, tool_info in AVAILABLE_TOOLS.items():
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_info["description"],
                    "parameters": tool_info["args_model"].model_json_schema(),
                }
            }
            tools.append(tool_def)
        return tools
    
    def _get_system_prompt(self) -> str:
        """
        生成系统提示词
        
        Returns:
            系统提示词字符串
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 获取星期几
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]
        
        return f"""你是一个专业的体育馆智能助手。

当前时间: {current_time} ({weekday})

【核心职责】
1. 协助用户查询场地状态。
2. 协助用户完成场地预订（必须调用工具）。
3. 解答场馆规则问题。

【思考与回复规则】
1. **上下文敏感**：用户如果说 "订这个"、"就要它了"，你必须回顾【对话历史】，找到上一步用户查询的场地 ID、时间段。如果上一步信息不全，必须追问，不要猜测。
2. **工具调用优先**：涉及数据查询（如"有没有场"、"价格多少"）或操作（"预订"），必须调用工具，禁止编造数据。
3. **参数补全**：
   - 如果用户只说了 "下午"，默认指 14:00-18:00。
   - 如果用户只说了 "晚上"，默认指 18:00-22:00。
   - 如果用户未指定日期，默认为【今天】。
4. **简洁回复**：不要啰嗦，直接给出结果。预订成功后，告诉用户订单号和扣款金额。

【异常处理】
- 如果工具报错（如余额不足），请用委婉的语气告诉用户原因，并建议充值。
- 如果用户问了非体育馆相关的问题，礼貌拒绝。
"""
    
    async def chat_stream(
        self,
        user_input: str,
        session_id: str = "default",
        member_id: Optional[int] = None,
        max_iterations: int = 5,
    ) -> AsyncGenerator[str, None]:
        """
        处理用户对话（流式响应）
        
        Args:
            user_input: 用户输入的自然语言
            session_id: 会话 ID，用于区分不同用户
            member_id: 会员 ID，用于关联订单到具体用户
            max_iterations: 最大工具调用迭代次数，防止死循环
        
        Yields:
            str: AI 助手的回复片段（流式输出）
        """
        print(f"\n{'='*80}")
        print(f"[AgentService] 新对话（流式）")
        print(f"[AgentService] Session ID: {session_id}")
        print(f"[AgentService] Member ID: {member_id}")
        print(f"[AgentService] User Input: {user_input}")
        print(f"{'='*80}\n")
        
        # 获取会话历史
        history = get_conversation_history(session_id)
        
        # 如果是新会话，添加系统提示词
        if not history:
            system_message = {
                "role": "system",
                "content": self._get_system_prompt()
            }
            add_message(session_id, system_message)
            history = get_conversation_history(session_id)
        
        # 添加用户消息
        user_message = {
            "role": "user",
            "content": user_input
        }
        add_message(session_id, user_message)
        
        # 【优化】历史记录截断策略：保留 System Prompt + 最近 10 轮对话（20 条消息）
        # history[0] 是 System Prompt，保留它，然后取最后 20 条消息
        if len(history) > 21:
            pruned_history = [history[0]] + history[-20:]
            print(f"[AgentService] 历史记录截断: {len(history)} -> {len(pruned_history)} 条消息")
        else:
            pruned_history = history
        
        # Function Calling Loop
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\n[AgentService] --- Iteration {iteration} (Stream) ---")
            
            try:
                # 调用 LLM（流式）
                print(f"[AgentService] 调用 LLM (stream=True)...")
                print(f"[AgentService] 消息数量: {len(pruned_history)}")
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=pruned_history,
                    tools=self.tools,
                    tool_choice="auto",
                    stream=True,  # 启用流式响应
                )
                
                # 用于累积工具调用信息
                accumulated_content = ""
                tool_calls_accumulator = {}  # {index: {id, name, arguments}}
                finish_reason = None
                
                # 流式读取响应
                async for chunk in response:
                    if not chunk.choices:
                        continue
                    
                    choice = chunk.choices[0]
                    delta = choice.delta
                    finish_reason = choice.finish_reason
                    
                    # 处理普通文本内容
                    if delta.content:
                        accumulated_content += delta.content
                        # 实时 yield 给前端
                        yield delta.content
                    
                    # 处理工具调用（累积，不 yield）
                    if delta.tool_calls:
                        for tool_call_delta in delta.tool_calls:
                            index = tool_call_delta.index
                            
                            if index not in tool_calls_accumulator:
                                tool_calls_accumulator[index] = {
                                    "id": "",
                                    "name": "",
                                    "arguments": ""
                                }
                            
                            # 累积 ID
                            if tool_call_delta.id:
                                tool_calls_accumulator[index]["id"] += tool_call_delta.id
                            
                            # 累积函数名
                            if tool_call_delta.function and tool_call_delta.function.name:
                                tool_calls_accumulator[index]["name"] += tool_call_delta.function.name
                            
                            # 累积参数
                            if tool_call_delta.function and tool_call_delta.function.arguments:
                                tool_calls_accumulator[index]["arguments"] += tool_call_delta.function.arguments
                
                print(f"[AgentService] 流式响应完成")
                print(f"[AgentService] Finish Reason: {finish_reason}")
                print(f"[AgentService] Accumulated Content Length: {len(accumulated_content)}")
                print(f"[AgentService] Tool Calls Count: {len(tool_calls_accumulator)}")
                
                # 检查是否有工具调用
                if tool_calls_accumulator:
                    print(f"[AgentService] 检测到工具调用: {len(tool_calls_accumulator)} 个")
                    
                    # 构建 assistant 消息（包含工具调用）
                    assistant_message_dict = {
                        "role": "assistant",
                        "content": accumulated_content or None,
                        "tool_calls": []
                    }
                    
                    # 转换累积的工具调用为标准格式
                    for idx in sorted(tool_calls_accumulator.keys()):
                        tc = tool_calls_accumulator[idx]
                        assistant_message_dict["tool_calls"].append({
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": tc["arguments"]
                            }
                        })
                    
                    add_message(session_id, assistant_message_dict)
                    
                    # 执行所有工具调用
                    for tc in assistant_message_dict["tool_calls"]:
                        tool_name = tc["function"]["name"]
                        tool_args_str = tc["function"]["arguments"]
                        tool_call_id = tc["id"]
                        
                        print(f"\n[AgentService] 执行工具: {tool_name}")
                        print(f"[AgentService] 工具参数: {tool_args_str}")
                        
                        try:
                            # 解析参数
                            tool_args = json.loads(tool_args_str)
                            
                            # 执行工具
                            tool_result = execute_tool(tool_name, member_id=member_id, **tool_args)
                            
                            print(f"[AgentService] 工具执行成功")
                            print(f"[AgentService] 工具结果: {tool_result}")
                            
                            # 将工具结果添加到历史
                            tool_message = {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": tool_name,
                                "content": json.dumps(tool_result, ensure_ascii=False),
                            }
                            add_message(session_id, tool_message)
                            
                        except Exception as e:
                            print(f"[AgentService] 工具执行失败: {e}")
                            
                            # 将错误信息添加到历史
                            error_message = {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": tool_name,
                                "content": json.dumps({
                                    "error": str(e),
                                    "message": "工具执行失败"
                                }, ensure_ascii=False),
                            }
                            add_message(session_id, error_message)
                    
                    # 递归调用，让 LLM 根据工具结果生成最终回复（流式输出）
                    print(f"[AgentService] 递归调用 chat_stream 以生成最终回复...")
                    async for token in self.chat_stream(
                        user_input="",  # 空输入，因为我们只是让 LLM 根据工具结果回复
                        session_id=session_id,
                        member_id=member_id,
                        max_iterations=max_iterations - iteration
                    ):
                        yield token
                    
                    # 递归调用完成，退出循环
                    return
                
                else:
                    # 没有工具调用，说明 LLM 已经生成了最终回复
                    print(f"[AgentService] 无工具调用，流式输出完成")
                    
                    # 将 assistant 消息添加到历史
                    assistant_message_dict = {
                        "role": "assistant",
                        "content": accumulated_content or "抱歉，我没有理解您的问题。",
                    }
                    add_message(session_id, assistant_message_dict)
                    
                    print(f"\n[AgentService] 流式响应完成")
                    print(f"{'='*80}\n")
                    
                    return
            
            except Exception as e:
                print(f"[AgentService] 错误: {e}")
                error_msg = f"抱歉，处理您的请求时出现了错误：{str(e)}"
                yield error_msg
                return
        
        # 达到最大迭代次数
        print(f"[AgentService] 达到最大迭代次数 ({max_iterations})")
        yield "抱歉，处理您的请求时遇到了问题，请稍后再试。"
    
    async def reset_conversation(self, session_id: str) -> None:
        """
        重置会话历史
        
        Args:
            session_id: 会话 ID
        """
        clear_conversation_history(session_id)
        print(f"[AgentService] 会话 {session_id} 已重置")


# ============================================================================
# Convenience Functions
# ============================================================================

# 全局 Agent 实例（单例模式）
_agent_instance: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """
    获取全局 Agent 服务实例（单例）
    
    Returns:
        AgentService 实例
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AgentService()
    return _agent_instance


async def chat_with_agent(
    user_input: str,
    session_id: str = "default",
    member_id: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """
    便捷函数：与 Agent 对话（流式）
    
    注意：这是一个异步生成器，必须使用 async for 迭代
    
    Args:
        user_input: 用户输入
        session_id: 会话 ID
        member_id: 会员 ID
    
    Yields:
        str: AI 助手的回复片段（流式输出）
    """
    agent = get_agent_service()
    # 必须使用 async for 显式透传 yield，不能直接 return
    async for token in agent.chat_stream(user_input, session_id, member_id):
        yield token
