from langgraph.prebuilt import create_react_agent

from ds_llm import llm
from tools import *

tools = [fetch_real_time_info, get_weather, insert_weather_to_db, query_weather_from_db]
graph = create_react_agent(llm, tools=tools)

if __name__ == '__main__':

    # 可以自动处理成 HumanMessage 的消息格式
    final_response = graph.invoke({"messages":["你好，请你介绍一下你自己"]})
    print(final_response)

    finan_response = graph.invoke({"messages": ["北京今天的天气怎么样？"]})

    finan_response
    finan_response = graph.invoke({"messages": ["你知道 cloud 3.5 发布的 computer use 吗？请用中文回复我"]})

    finan_response
    finan_response = graph.invoke({"messages": [
        "帮我查一下北京、上海，哈尔滨三个城市的天气，告诉我哪个城市最适合出游。同时，把查询到的数据存储到数据库中"]})

    finan_response
    finan_response = graph.invoke(
        {"messages": ["帮我分析一下数据库中北京和哈尔滨城市天气的信息，做一个详细的对比，并生成出行建议"]})

    finan_response