from os.path import basename

from ds_llm import llm

from typing import TypedDict
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage

from langgraph.graph import START, StateGraph
from utils import save_graph_image

print(llm.invoke('帮我查询北京今天的天气').content)


