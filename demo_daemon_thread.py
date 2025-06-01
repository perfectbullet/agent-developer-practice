import threading
import time

def non_daemon_task():
    print("Non-daemon thread starts")
    time.sleep(5)
    print("Non-daemon thread ends")  # 主线程结束后，非守护线程仍会执行完

def daemon_task():
    print("Daemon thread starts")
    time.sleep(8)
    print("Daemon thread ends")  # 主线程结束后，此语句不会执行

# 非守护线程
t1 = threading.Thread(target=non_daemon_task)
t1.start()

# 守护线程
t2 = threading.Thread(target=daemon_task, daemon=True)
t2.start()

# 主线程休眠2秒后退出
time.sleep(2)
print("Main thread exits")