from langchain_core.runnables import RunnableConfig
from typing_extensions import Annotated, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

def reducer(a: list, b: int | None) -> list:
    if b is not None:
        return a + [b]
    return a

class State(TypedDict):
    x: Annotated[list, reducer]

class ConfigSchema(TypedDict):
    r: float

graph = StateGraph(State, config_schema=ConfigSchema)

def node(state: State, config: RunnableConfig) -> dict:
    r = config["configurable"].get("r", 1.0)
    x = state["x"][-1]
    next_value = x * r * (1 - x)
    print(next_value)
    return {"x": next_value}

graph.add_node("A", node)
graph.set_entry_point("A")
graph.set_finish_point("A")
compiled = graph.compile()

print(compiled.config_specs)
# [ConfigurableFieldSpec(id='r', annotation=<class 'float'>, name=None, description=None, default=None, is_shared=False, dependencies=None)]

step1 = compiled.invoke({"x": 0.5}, {"configurable": {"r": 3.0}})
# {'x': [0.5, 0.75]}
print(step1)
step2 = compiled.invoke({"x": 0.5}, {"configurable": {"r": 3.0}})
print(step2)
step3 = compiled.invoke({"x": 0.5}, {"configurable": {"r": 3.0}})
print(step3)