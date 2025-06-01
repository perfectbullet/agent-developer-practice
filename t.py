import json

from openai import OpenAI
client = OpenAI(
    api_key="sk-kWNCLmUaSjsr2iUq7LZ2fEgCxSFyr4YWKUjjjoIW5HsNzhGo", # 在这里将 MOONSHOT_API_KEY 替换为你从 Kimi 开放平台申请的 API Key
    base_url="https://api.moonshot.cn/v1",
)

messages = []


tools = [
    {
        "type": "function",
        "function": {
            "name": "query_by_product_name",
            "description": "Query the database to retrieve a list of products that match or contain the specified product name. This function can be used to assist customers in finding products by name via an online platform or customer support interface.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "The name of the product to search for. The search is case-insensitive and allows partial matches."
                    }
                },
                "required": ["product_name"]
            }
        }

    },
    {
        "type": "function",
        "function": {
            "name": "read_store_promotions",
            "description": "Read the store's promotion document to find specific promotions related to the provided product name. This function scans a text document for any promotional entries that include the product name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "The name of the product to search for in the promotion document. The function returns the promotional details if found."
                    }
                },
                "required": ["product_name"]
            }
        }
    }
]


def read_store_promotions(product_name):
    # 指定优惠政策文档的文件路径
    file_path = 'store_promotions.txt'

    try:
        # 打开文件并按行读取内容
        with open(file_path, 'r', encoding='utf-8') as file:
            promotions_content = file.readlines()

        # 搜索包含产品名称的行
        filtered_content = [line for line in promotions_content if product_name in line]

        # 返回匹配的行，如果没有找到，返回一个默认消息
        if filtered_content:
            return ''.join(filtered_content)
        else:
            return "没有找到关于该产品的优惠政策。"
    except FileNotFoundError:
        # 文件不存在的错误处理
        return "优惠政策文档未找到，请检查文件路径是否正确。"
    except Exception as e:
        # 其他潜在错误的处理
        return f"读取优惠政策文档时发生错误: {str(e)}"

import sqlite3

def query_by_product_name(product_name):
    # 连接 SQLite 数据库
    conn = sqlite3.connect('SportsEquipment.db')
    cursor = conn.cursor()

    # 使用SQL查询按名称查找产品。'%'符号允许部分匹配。
    cursor.execute("SELECT * FROM products WHERE product_name LIKE ?", ('%' + product_name + '%',))

    # 获取所有查询到的数据
    rows = cursor.fetchall()

    # 关闭连接
    conn.close()

    return rows

available_functions = {"query_by_product_name": query_by_product_name, "read_store_promotions":read_store_promotions}


prompt = '你家卖健身手套吗？现在有什么优惠？'

# 添加用户的提问到消息列表
messages.append({'role': 'user', 'content': prompt})

# 检查是否需要调用外部函数
completion = client.chat.completions.create(
    model="moonshot-v1-8k",
    messages=messages,
    tools=tools,
    parallel_tool_calls=True  # 这里需要格外注意
)

# 提取回答内容
response = completion.choices[0].message
tool_calls = completion.choices[0].message.tool_calls

# 处理外部函数调用
if tool_calls:
    function_name = tool_calls[0].function.name
    function_args = json.loads(tool_calls[0].function.arguments)

    function_response = available_functions[function_name](**function_args)

    messages.append(response)

    for tool_call in tool_calls:
        messages.append(
                {
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                    "tool_call_id": tool_call.id,
                }
            )

    second_response = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=messages,
    )
    # 获取最终结果

    final_response = second_response.choices[0].message.content
    messages.append({'role': 'assistant', 'content': final_response})
    print(final_response)
else:
    # 打印响应并添加到消息列表
    print(response.content)
    messages.append({'role': 'assistant', 'content': response.content})