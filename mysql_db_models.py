
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base

# 创建基类
Base = declarative_base()

# 定义 WeatherInfo 模型
class Weather(Base):
    __tablename__ = 'weather'
    city_id = Column(Integer, primary_key=True)  # 城市ID
    city_name = Column(String(50))                # 城市名称
    main_weather = Column(String(50))             # 主要天气状况
    description = Column(String(100))              # 描述
    temperature = Column(Float)                    # 温度
    feels_like = Column(Float)                    # 体感温度
    temp_min = Column(Float)                      # 最低温度
    temp_max = Column(Float)                      # 最高温度


# 数据库连接 URI，这里要替换成自己的Mysql 连接信息，以下是各个字段的对应解释：
# root：MySQL 数据库的用户名。
# snowball950123：MySQL 数据库的密码。
# 192.168.110.131：MySQL 服务器的 IP 地址。
# langgraph_agent：要连接的数据库的名称。
# charset=utf8mb4：设置数据库的字符集为 utf8mb4，支持更广泛的 Unicode 字符
DATABASE_URI = 'mysql+pymysql://root:snowball950123@192.168.110.131/langgraph_agent?charset=utf8mb4'
engine = create_engine(DATABASE_URI)

# 如果表不存在，则创建表
Base.metadata.create_all(engine)

# 创建会话
Session = sessionmaker(bind=engine)
