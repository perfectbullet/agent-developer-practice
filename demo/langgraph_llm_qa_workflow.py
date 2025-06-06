from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Optional

from ds_llm import llm


# 定义图中输入状态
class InputState(TypedDict):
    question: str
    llm_answer: Optional[str]  # 表示 answer 可以是 str 类型，也可以是 None


# 定义图中输出状态
class OutputState(TypedDict):
    answer: str


# 将 InputState 和 OutputState 这两个 TypedDict 类型合并成一个更全面的字典类型。
class AllState(InputState, OutputState):
    pass


def llm_node(state: InputState):
    messages = [("system", "你是一位乐于助人的智能助理",),
                ("human", state["question"])]
    response = llm.invoke(messages)
    return {"llm_answer": response.content}


def action_node(state: InputState):
    messages = [("system", "无论你接收到什么语言的文本，请翻译成日语",),
                ("human", state["llm_answer"])]
    response = llm.invoke(messages)
    return {"answer": response.content}


# 构建图
builder = StateGraph(AllState, input=InputState, output=OutputState)
builder.add_node('llm_node', llm_node)
builder.add_node('action_node', action_node)

builder.add_edge(START, 'llm_node')
builder.add_edge('llm_node', 'action_node')
builder.add_edge('action_node', END)

# 编译图
graph = builder.compile()

final_answer = graph.invoke({'question': '北京今天天气'})
print(final_answer)
