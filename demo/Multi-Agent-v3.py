from os.path import basename

from typing import TypedDict
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage

import operator
from typing import Annotated, Sequence
from typing_extensions import TypedDict

import functools
from langchain_core.messages import AIMessage
from langgraph.graph import START, StateGraph, END
from utils import save_graph_image
from langchain_core.tools import tool
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage
from typing import TypedDict
from ds_llm import llm
from pydantic import BaseModel, Field
from typing import List, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import ToolNode
from mysql_db_models import Session, SalesData


# 定义工具
class AddSaleSchema(BaseModel):
    product_id: int
    employee_id: int
    customer_id: int
    sale_date: str
    quantity: int
    amount: float
    discount: float


class DeleteSaleSchema(BaseModel):
    sales_id: int


class UpdateSaleSchema(BaseModel):
    sales_id: int
    quantity: int
    amount: float


class QuerySalesSchema(BaseModel):
    sales_id: int


# 1. 添加销售数据：
@tool(args_schema=AddSaleSchema)
def add_sale(product_id, employee_id, customer_id, sale_date, quantity, amount, discount):
    """Add sale record to the database."""
    session = Session()
    try:
        new_sale = SalesData(
            product_id=product_id,
            employee_id=employee_id,
            customer_id=customer_id,
            sale_date=sale_date,
            quantity=quantity,
            amount=amount,
            discount=discount
        )
        session.add(new_sale)
        session.commit()
        return {"messages": ["销售记录添加成功。"]}
    except Exception as e:
        return {"messages": [f"添加失败，错误原因：{e}"]}
    finally:
        session.close()


# 2. 删除销售数据
@tool(args_schema=DeleteSaleSchema)
def delete_sale(sales_id):
    """Delete sale record from the database."""
    session = Session()
    try:
        sale_to_delete = session.query(SalesData).filter(SalesData.sales_id == sales_id).first()
        if sale_to_delete:
            session.delete(sale_to_delete)
            session.commit()
            return {"messages": ["销售记录删除成功。"]}
        else:
            return {"messages": [f"未找到销售记录ID：{sales_id}"]}
    except Exception as e:
        return {"messages": [f"删除失败，错误原因：{e}"]}
    finally:
        session.close()


# 3. 修改销售数据
@tool(args_schema=UpdateSaleSchema)
def update_sale(sales_id, quantity, amount):
    """Update sale record in the database."""
    session = Session()
    try:
        sale_to_update = session.query(SalesData).filter(SalesData.sales_id == sales_id).first()
        if sale_to_update:
            sale_to_update.quantity = quantity
            sale_to_update.amount = amount
            session.commit()
            return {"messages": ["销售记录更新成功。"]}
        else:
            return {"messages": [f"未找到销售记录ID：{sales_id}"]}
    except Exception as e:
        return {"messages": [f"更新失败，错误原因：{e}"]}
    finally:
        session.close()


# 4. 查询销售数据
@tool(args_schema=QuerySalesSchema)
def query_sales(sales_id):
    """Query sale record from the database."""
    session = Session()
    try:
        sale_data = session.query(SalesData).filter(SalesData.sales_id == sales_id).first()
        if sale_data:
            return {
                "sales_id": sale_data.sales_id,
                "product_id": sale_data.product_id,
                "employee_id": sale_data.employee_id,
                "customer_id": sale_data.customer_id,
                "sale_date": sale_data.sale_date,
                "quantity": sale_data.quantity,
                "amount": sale_data.amount,
                "discount": sale_data.discount
            }
        else:
            return {"messages": [f"未找到销售记录ID：{sales_id}。"]}
    except Exception as e:
        return {"messages": [f"查询失败，错误原因：{e}"]}
    finally:
        session.close()


# 数据分析师（code_agent）第二个数据分析师（code_agent）在需要的时候，
# 接收db_agent的数据，生成可视化的图表，这里我们给他配置一个本地的Python代码解释器。
# 这里我们使用Python REPL 工具，它是LangChian封装的一个工具，作用是先让大模型生成代码，
# 然后再运行该代码来获取答案，且仅返回打印的内容。
from langchain_experimental.utilities import PythonREPL

repl = PythonREPL()


@tool
def python_repl(
        code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed:\n\`\`\`python\n{code}\n\`\`\`\nStdout: {result}"
    return (
            result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."
    )


# 定义工具列表
tools = [add_sale, delete_sale, update_sale, query_sales, python_repl]
tool_executor = ToolNode(tools)


# Stage 3. 创建代理
def create_agent(llm, tools, system_message: str):
    """Create an agent."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " If you or any of the other assistants have the final answer or deliverable,"
                " prefix your response with FINAL ANSWER so the team knows to stop."
                " You have access to the following tools: {tool_names}.\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    return prompt | llm.bind_tools(tools)


# 数据库管理员
db_agent = create_agent(
    llm,
    [add_sale, delete_sale, update_sale, query_sales],
    system_message="You should provide accurate data for the code_generator to use.  and source code shouldn't be the final answer",
)

# 数据分析
code_agent = create_agent(
    llm,
    [python_repl],
    system_message="Run python code to display diagrams or output execution results",
)


def agent_node(state, agent, name):
    result = agent.invoke(state)
    # 将代理输出转换为适合附加到全局状态的格式
    if isinstance(result, ToolMessage):
        pass
    else:
        # 创建一个 AIMessage 类的新实例，其中包含 result 对象的所有数据（除了 type 和 name），并且设置新实例的 name 属性为特定的值 name。
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        # 跟踪发件人，这样我们就知道下一个要传给谁。
        "sender": name,
    }


db_node = functools.partial(agent_node, agent=db_agent, name="db_manager")
code_node = functools.partial(agent_node, agent=code_agent, name="code_generator")


# 任何一个代理都可以决定结束
def router(state):
    # 这是一个路由
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        # 前一个代理正在调用一个工具
        return "call_tool"
    if "FINAL ANSWER" in last_message.content:
        # 任何Agent都决定工作完成
        return END
    return "continue"


# 定义状态和图
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str


# Stage 5. 构建图结构
# 初始化一个状态图
workflow = StateGraph(AgentState)
# 将Agent作为节点进行添加
workflow.add_node('db_manager', db_node)
workflow.add_node('code_generator', code_node)
workflow.add_node('call_tool', tool_executor)
# 通过条件边 构建 子代理之间的通信
workflow.add_conditional_edges(
    "db_manager",
    router,
    {"continue": "code_generator", 'call_tool': 'call_tool', END: END}
)
workflow.add_conditional_edges(
    "code_generator",
    router,
    {"continue": "db_manager", 'call_tool': 'call_tool', END: END}
)

workflow.add_conditional_edges(
    'call_tool',
    lambda x: x['sender'],
    {
        "db_manager": "db_manager",
        "code_generator": "code_generator",
    },
)

# 设置 db_manager 为初始节点
workflow.set_entry_point('db_manager')
# 编译图
graph = workflow.compile()
save_graph_image(graph, basename(__file__).split('.')[0])

if __name__ == '__main__':

    # Stage 6. 调用测试
    for chunk in graph.stream(
            {"messages": [HumanMessage(content="根据sales_id使用折线图显示前5名销售的销售总额")]},
            {"recursion_limit": 50},
            stream_mode='values'
    ):
        print(chunk)
