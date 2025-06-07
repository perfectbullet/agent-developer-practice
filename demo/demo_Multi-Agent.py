from os.path import basename

from ds_llm import llm

from typing import TypedDict
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage

from langgraph.graph import START, StateGraph
from utils import save_graph_image


# 定义父图中的状态
class ParentState(TypedDict):
    user_input: str  # 用来接收用户的输入
    final_answer: str  # 用来存储大模型针对用户输入的响应


def parent_node(state: ParentState):
    messages = [("human", state["user_input"])]
    response = llm.invoke(messages)
    return {'final_answer': response.content}


# 定义子图中的状态
class SubgraphState(TypedDict):
    # 这个 key 是和 父图（ParentState）共享的，
    final_answer: str
    # 这个key 是 子图 (subgraph) 中独享的
    summary_answer: str


def subgraph_node_1(state: SubgraphState):
    system_prompt = """
    Please summary the content you receive to 50 words or less
    """
    messages = state['final_answer']  # 这里接收父图传递过来的响应
    messages = [SystemMessage(content=system_prompt)] + [HumanMessage(content=messages)]
    response = llm.invoke(messages)
    return {"summary_answer": response.content}


def subgraph_node_2(state: SubgraphState):
    # final_answer 仅能在 子图中使用
    messages = f"""
    This is the full content of what you received：{state["final_answer"]} \n
    This information is summarized for the full content:{state["summary_answer"]} 
    Please rate the text and summary information, returning a scale of 1 to 10. Note: Only the score value needs to be returned.
    """

    response = llm.invoke([HumanMessage(content=messages)])

    # 发送共享状态密钥（'user_input'）的更新
    return {"final_answer": response.content}


# 定义子图的图结构并且进行编译
subgraph_builder = StateGraph(SubgraphState)
subgraph_builder.add_node(subgraph_node_1)
subgraph_builder.add_node(subgraph_node_2)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph_builder.add_edge("subgraph_node_1", "subgraph_node_2")
subgraph = subgraph_builder.compile()

# 定义父图的图结构，并将子图作为节点添加至父图
builder = StateGraph(ParentState)
builder.add_node("node_1", parent_node)

# 将编译后的子图作为一个节点添加到父图中
builder.add_node("node_2", subgraph)
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
graph = builder.compile()

save_graph_image(graph, basename(__file__).split('.')[0])

if __name__ == '__main__':
    for chunk in graph.stream({"user_input": "我现在想学习大模型，应该关注哪些技术？"}, stream_mode='values'):
        print(chunk)

    # for chunk in graph.stream({"user_input": "如何理解RAG？"}, stream_mode='values', subgraphs=True):
    #     print(chunk)
