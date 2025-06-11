from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv
import getpass
import os

load_dotenv()
if not os.getenv("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass()
else:
    print('get deepseek api key ', os.environ["DEEPSEEK_API_KEY"])


llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # api_key="",
    # other params...
)

if __name__ == '__main__':

    # messages = [
    #     (
    #         "system",
    #         "You are a helpful assistant that translates English to Chinese. Translate the user sentence.",
    #     ),
    #     ("human", "I love programming."),
    # ]
    # ai_msg = llm.invoke(messages)
    # print(ai_msg.content)
    print(llm.invoke("帮我写一个使用Python实现的贪吃蛇的游戏代码").content)
