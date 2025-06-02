import getpass
import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import MessagesState, START
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langraph_tools import *

from ds_llm import llm

tools = [get_weather, insert_weather_to_db, query_weather_from_db, delete_weather_from_db]
# 绑定工具， 不绑定模型无法返回工具调用
llm = llm.bind_tools(tools)
tool_node = ToolNode(tools)


def call_model(state):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "end"
    elif last_message.tool_calls[0]["name"] == "delete_weather_from_db":
        return "run_tool"
    else:
        return "continue"


def run_tool(state):
    new_messages = []
    tool_calls = state["messages"][-1].tool_calls

    # tools =  [get_weather, insert_weather_to_db, query_weather_from_db, delete_weather_from_db]
    tools = [delete_weather_from_db]
    tools = {t.name: t for t in tools}

    for tool_call in tool_calls:
        tool = tools[tool_call["name"]]
        result = tool.invoke(tool_call["args"])
        new_messages.append(
            {
                "role": "tool",
                "name": tool_call["name"],
                "content": result,
                "tool_call_id": tool_call["id"],
            }
        )
    return {"messages": new_messages}


# 构建图
workflow = StateGraph(MessagesState)
# 添加节点
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)
workflow.add_node("run_tool", run_tool)
# 添加边
workflow.add_edge(START, "agent")
# 添加条件边
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "end": END,
        "continue": "action",
        "run_tool": "run_tool",
    }
)

workflow.add_edge("action", "agent")
workflow.add_edge("run_tool", "agent")

# 添加断点
memory = MemorySaver()
graph = workflow.compile(memory, interrupt_before=["run_tool"])

if __name__ == '__main__':
    # # 生成可视化图像结构
    # img_data = graph.get_graph().draw_mermaid_png()
    #
    # # 保存图像到文件
    # with open("interactive_info_management_system.png", "wb") as f:
    #     f.write(img_data)

    # config = {"configurable": {"thread_id": "9"}}
    #
    # for chunk in graph.stream({"messages": "查一下北京的天气,并缓存到本地"}, config, stream_mode="values"):
    #     chunk["messages"][-1].pretty_print()

    # config = {"configurable": {"thread_id": "9"}}
    #
    # for chunk in graph.stream(
    #         {"messages": "帮我同时查一下上海、杭州的天气，比较哪个城市更适合现在出游。并缓存天气信息到本地"}, config,
    #         stream_mode="values"):
    #     chunk["messages"][-1].pretty_print()

    config = {"configurable": {"thread_id": "9"}}

    for chunk in graph.stream({"messages": "帮我删除数据库中北京的天气数据"}, config, stream_mode="values"):
        chunk["messages"][-1].pretty_print()

    state = graph.get_state(config)
    print(state.next)
    print(state.tasks)
    print(state.values)

    # 首先还是同样，如果允许删除操作，仍然在input参数中填写None，将上述全部状态信息传递到图中使其恢复中断的执行，如下所示：
    for chunk in graph.stream(None, config, stream_mode="values"):
        chunk["messages"][-1].pretty_print()
