import json

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from typing import Union, Optional, TypedDict, Annotated
from pydantic import BaseModel, Field
import requests
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from IPython.display import Image, display

from langgraph.graph import StateGraph, END, START, add_messages
from ds_llm import llm


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

class WeatherLoc(BaseModel):
    location: str = Field(description="The location name of the city")

class SearchQuery(BaseModel):
    query: str = Field(description="Questions for networking queries")

@tool(args_schema=SearchQuery)
def fetch_real_time_info(query):
    """Get real-time Internet information"""
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "num": 1,
    })
    headers = {
        'X-API-KEY': 'b3510ac695bac1d69c47f8d56b6d69c5f1d5f3bf',
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=payload)
    data = json.loads(response.text)  # 将返回的JSON字符串转换为字典
    if 'organic' in data:
        return json.dumps(data['organic'], ensure_ascii=False)  # 返回'organic'部分的JSON字符串
    else:
        return json.dumps({"error": "No organic results found"}, ensure_ascii=False)  # 如果没有'organic'键，返回错误信息


@tool(args_schema=WeatherLoc)
def get_weather(location):
    """
    Function to query current weather.
    :param loc: Required parameter, of type string, representing the specific city name for the weather query. \
    Note that for cities in China, the corresponding English city name should be used. For example, to query the weather for Beijing, \
    the loc parameter should be input as 'Beijing'.
    :return: The result of the OpenWeather API query for current weather, with the specific URL request address being: https://api.openweathermap.org/data/2.5/weather. \
    The return type is a JSON-formatted object after parsing, represented as a string, containing all important weather information.
    """
    # Step 1.构建请求
    url = "https://api.openweathermap.org/data/2.5/weather"

    # Step 2.设置查询参数
    params = {
        "q": location,
        "appid": "01f0a372b3810c5c30d746565343f92d",  # 输入API key
        "units": "metric",  # 使用摄氏度而不是华氏度
        "lang": "zh_cn"  # 输出语言为简体中文
    }

    # Step 3.发送GET请求
    response = requests.get(url, params=params)

    # Step 4.解析响应
    data = response.json()
    return json.dumps(data)

tools = [get_weather, fetch_real_time_info]
tool_node = ToolNode(tools)

# 定义大模型实例，这里使用deepseek 模型进行演示。
llm = llm.bind_tools(tools)

def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]

    if not last_message.tool_calls:
        # 如果没有 工具调用，则输出至最终节点
        return "end"
    else:
        # 如果还有子任务需要继续执行工具调用的话，则继续等待执行
        return "continue"

def call_model(state):
    messages = state["messages"]
    responses = llm.invoke(messages)
    return {"messages": [responses]}

workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

# 添加边
workflow.add_edge(START, "agent")
# 添加条件边
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": END,
    }
)
# 添加边
workflow.add_edge('action', "agent")

# 添加断点
memory = MemorySaver()
graph = workflow.compile(memory, interrupt_before=["action"])
# 生成可视化图像结构
img_data = graph.get_graph().draw_mermaid_png()

# 保存图像到文件
with open("workflow_graph.png", "wb") as f:
    f.write(img_data)

if __name__ == '__main__':

    config = {"configurable": {"thread_id": "4"}}

    for chunk in graph.stream({"messages": "请帮我查一下北京的天气"}, config, stream_mode="values"):
        chunk["messages"][-1].pretty_print()
    print('=' * 100)
    print('=' * 100)
    for chunk in graph.stream(None, config, stream_mode="values"):
        chunk["messages"][-1].pretty_print()

    # config = {"configurable": {"thread_id": "4"}}
    #
    # for chunk in graph.stream({"messages": "最近 OpenAI 有哪些大动作？"}, config, stream_mode="values"):
    #     chunk["messages"][-1].pretty_print()
    #
    # for chunk in graph.stream(None, config, stream_mode="values"):
    #     chunk["messages"][-1].pretty_print()


