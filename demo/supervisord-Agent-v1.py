import getpass
import os
from langchain_openai import ChatOpenAI
from ds_llm import llm

from langgraph.graph import StateGraph, MessagesState, START, END

class AgentState(MessagesState):
    next: str

members = ["chat", "coder", "sqler"]
options = members + ["FINISH"]

from typing import Literal
from typing_extensions import TypedDict
class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH"""

    next: Literal["chat", "coder", "sqler", 'FINISH']


from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage


def supervisor(state: AgentState):
    system_prompt = (
        "你是一名监督者，负责管理以下工作人员之间的对话："
        f" {members}.\n\n"
        "每位工作人员都有特定的角色：\n"
        "- chat: 使用自然语言直接回应用户输入.\n"
        "- coder: 在需要数学计算或具体编程任务时被激活。\n"
        "- sqler: 在需要数据库查询或生成明确的 SQL 语句时使用。\n\n"
        "根据下列用户请求，请判断下一步应由哪位工作人员执行任务。"
        " 每位工作人员会完成一项任务，并返回他们的结果与状态。"
        " 当所有任务完成后，请返回 FINISH。"
    )

    messages = [{"role": "system", "content": system_prompt}, ] + state["messages"]
    print('-' * 100)
    response = llm.with_structured_output(Router).invoke(messages)

    next_ = response["next"]

    if next_ == "FINISH":
        next_ = END
    print('next_ is ', next_)
    print('=' * 100)
    return {"next": next_}

def chat(state: AgentState):
    messages = state["messages"][-1]
    model_response = llm.invoke(messages.content)
    final_response = [HumanMessage(content=model_response.content, name="chat")]   # 这里要添加名称
    return {"messages": final_response}

def coder(state: AgentState):
    messages = state["messages"][-1]
    model_response = llm.invoke(messages.content)
    final_response = [HumanMessage(content=model_response.content, name="coder")]   # 这里要添加名称
    return {"messages": final_response}

def sqler(state: AgentState):
    messages = state["messages"][-1]
    model_response = llm.invoke(messages.content)
    final_response = [HumanMessage(content=model_response.content, name="sqler")]  # 这里要添加名称
    return {"messages": final_response}


builder = StateGraph(AgentState)

# builder.add_edge(START, "supervisor")
builder = builder.add_node("supervisor", supervisor)
builder = builder.add_node("chat", chat)
builder = builder.add_node("coder", coder)
builder = builder.add_node("sqler", sqler)


for member in members:
    # 我们希望我们的工人在完成工作后总是向主管“汇报”
    builder.add_edge(member, "supervisor")


# 任何一个代理都可以决定结束
def router(state):
    return state["next"]

builder.add_conditional_edges("supervisor", router, {'chat': 'chat', 'coder': 'coder', 'sqler': 'sqler', '__end__': END})

# 添加开始和节点
builder.add_edge(START, "supervisor")

# 编译图
graph = builder.compile()

for chunk in graph.stream({"messages": "你好，请你介绍一下你自己"}, stream_mode="values"):
    print(chunk)