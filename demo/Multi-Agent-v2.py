from os.path import basename

from ds_llm import llm

from typing import TypedDict
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage

from langgraph.graph import START, StateGraph
from utils import save_graph_image

from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage
from typing import TypedDict


# 定义父图中的状态
class ParentState(TypedDict):
    user_input: str  # 用来接收用户的输入
    final_answer: str  # 用来存储大模型针对用户输入的响应


def parent_node_1(state: ParentState):
    response = llm.invoke(state["user_input"])
    response.pretty_print()
    return {"final_answer": response.content}


# ################################ 子图中专注于处理自己内部的逻辑，无需关心父图中的状态中都定义了哪些键
# 定义子图中的状态
class SubgraphState(TypedDict):
    # 以下三个 key 都是 子图 (subgraph) 中独享的
    response_answer: str
    summary_answer: str
    score: str


# 定义第一个节点，用于接收父图中的响应并且做文本摘要
def subgraph_node_1(state: SubgraphState):
    system_prompt = """
    Please summary the content you receive to 50 words or less
    """
    messages = state['response_answer']  # 这里接收父图传递过来的响应
    messages = [SystemMessage(content=system_prompt)] + [HumanMessage(content=messages)]
    response = llm.invoke(messages)
    response.pretty_print()
    return {"summary_answer": response.content}


# 定义第二个节点：
def subgraph_node_2(state: SubgraphState):
    messages = f"""
    This is the full content of what you received：{state["response_answer"]} \n
    This information is summarized for the full content:{state["summary_answer"]} 
    Please rate the text and summary information, returning a scale of 1 to 10. Note: Only the score value needs to be returned.
    """

    response = llm.invoke([HumanMessage(content=messages)])

    # 发送共享状态密钥（'user_input'）的更新
    return {"score": response.content}


# 正常定义子图并编译。
subgraph_builder = StateGraph(SubgraphState)
subgraph_builder.add_node(subgraph_node_1)
subgraph_builder.add_node(subgraph_node_2)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph_builder.add_edge("subgraph_node_1", "subgraph_node_2")
subgraph = subgraph_builder.compile()
# ################################ 子图中专注于处理自己内部的逻辑，无需关心父图中的状态中都定义了哪些键

# ################################ parent_node_2用来连接父图与子图之间的网络通信，它通过将父节点与子节点的状态做转化来达到此目的
def parent_node_2(state: ParentState):
    # 将父图中的状态转换为子图状态 final_answer -----> response_answer
    response = subgraph.invoke({'response_answer': state["final_answer"]})
    # 将子图状态再转换回父状态  score ----->
    return {'final_answer': response['score']}


# 构建父图
builder = StateGraph(ParentState)
builder.add_node('parent_node_1', parent_node_1)
# 注意，我们使用的不是编译后的子图，而是调用子图的‘ node_2 ’函数
builder.add_node('subgraph_node', parent_node_2)

builder.add_edge(START, "parent_node_1")
builder.add_edge('parent_node_1', 'subgraph_node')
graph = builder.compile()
save_graph_image(graph, basename(__file__).split('.')[0])

for chunk in graph.stream({"user_input": "我现在想学习大模型，应该关注哪些技术？"}, stream_mode='values'):
    print(chunk)
