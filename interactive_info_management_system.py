from langgraph.prebuilt import ToolNode

from langraph_tools import *

tools = [get_weather, insert_weather_to_db, query_weather_from_db, delete_weather_from_db]
tool_node = ToolNode(tools)

