import json

import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Integer, Float
from sqlalchemy.orm import sessionmaker, declarative_base

# 创建基类
Base = declarative_base()


# 定义 WeatherInfo 模型
class Weather(Base):
    __tablename__ = 'weather'
    city_id = Column(Integer, primary_key=True)  # 城市ID
    city_name = Column(String(50))  # 城市名称
    main_weather = Column(String(50))  # 主要天气状况
    description = Column(String(100))  # 描述
    temperature = Column(Float)  # 温度
    feels_like = Column(Float)  # 体感温度
    temp_min = Column(Float)  # 最低温度
    temp_max = Column(Float)  # 最高温度


# 数据库连接 URI
DATABASE_URI = 'mysql+pymysql://root:123456@127.0.0.1/langgraph_agent?charset=utf8mb4'  # 这里要替换成自己的数据库连接串
# 创建会话
engine = create_engine(DATABASE_URI)
# 如果表不存在，则创建表
Base.metadata.create_all(engine)
# 创建会话
Session = sessionmaker(bind=engine)


class WeatherLoc(BaseModel):
    location: str = Field(description="The location name of the city")


class WeatherInfo(BaseModel):
    """Extracted weather information for a specific city."""
    city_id: int = Field(..., description="The unique identifier for the city")
    city_name: str = Field(..., description="The name of the city")
    main_weather: str = Field(..., description="The main weather condition")
    description: str = Field(..., description="A detailed description of the weather")
    temperature: float = Field(..., description="Current temperature in Celsius")
    feels_like: float = Field(..., description="Feels-like temperature in Celsius")
    temp_min: float = Field(..., description="Minimum temperature in Celsius")
    temp_max: float = Field(..., description="Maximum temperature in Celsius")


class QueryWeatherSchema(BaseModel):
    """Schema for querying weather information by city name."""
    city_name: str = Field(..., description="The name of the city to query weather information")


class DeleteWeatherSchema(BaseModel):
    """Schema for deleting weather information by city name."""
    city_name: str = Field(..., description="The name of the city to delete weather information")


@tool(args_schema=WeatherLoc)
def get_weather(location):
    """
    查询当前天气的函数。
    :param location: 必需参数，字符串类型，表示要查询天气的具体城市名称。
        注意，对于中国的城市，应使用相应的英文城市名称。例如，要查询北京的天气，
        则loc参数应输入为'Beijing'。
    :return: OpenWeather API查询当前天气的结果，具体URL请求地址为：https://api.openweathermap.org/data/2.5/weather。
        返回类型是解析后的JSON格式对象，表示为字符串，包含所有重要的天气信息。
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


@tool(args_schema=WeatherInfo)
def insert_weather_to_db(city_id, city_name, main_weather, description, temperature, feels_like, temp_min, temp_max):
    """将天气信息插入数据库。"""
    session = Session()  # 确保为每次操作创建新的会话
    try:
        # 创建天气实例
        weather = Weather(
            city_id=city_id,
            city_name=city_name,
            main_weather=main_weather,
            description=description,
            temperature=temperature,
            feels_like=feels_like,
            temp_min=temp_min,
            temp_max=temp_max
        )
        # 添加到会话
        session.add(weather)
        # 提交事务
        session.commit()
        return {"messages": [f"天气数据已成功存储至Mysql数据库。"]}
    except Exception as e:
        session.rollback()  # 出错时回滚
        return {"messages": [f"数据存储失败，错误原因：{e}"]}
    finally:
        session.close()  # 关闭会话


@tool(args_schema=QueryWeatherSchema)
def query_weather_from_db(city_name: str):
    """Query weather information from the database by city name."""
    session = Session()
    try:
        # 查询天气数据
        weather_data = session.query(Weather).filter(Weather.city_name == city_name).first()
        print(weather_data)
        if weather_data:
            return {
                "city_id": weather_data.city_id,
                "city_name": weather_data.city_name,
                "main_weather": weather_data.main_weather,
                "description": weather_data.description,
                "temperature": weather_data.temperature,
                "feels_like": weather_data.feels_like,
                "temp_min": weather_data.temp_min,
                "temp_max": weather_data.temp_max
            }
        else:
            return {"messages": [f"未找到城市 '{city_name}' 的天气信息。"]}
    except Exception as e:
        return {"messages": [f"查询失败，错误原因：{e}"]}
    finally:
        session.close()  # 关闭会话


@tool(args_schema=DeleteWeatherSchema)
def delete_weather_from_db(city_name: str):
    """Delete weather information from the database by city name."""
    session = Session()
    try:
        # 查询要删除的天气数据
        weather_data = session.query(Weather).filter(Weather.city_name == city_name).first()

        if weather_data:
            # 删除记录
            session.delete(weather_data)
            session.commit()
            return {"messages": [f"城市 '{city_name}' 的天气信息已成功删除。"]}
        else:
            return {"messages": [f"未找到城市 '{city_name}' 的天气信息。"]}
    except Exception as e:
        session.rollback()  # 出错时回滚
        return {"messages": [f"删除失败，错误原因：{e}"]}
    finally:
        session.close()  # 关闭会话

