from datetime import datetime
now = datetime.now()
print(now)
print(type(now))
print(now.strftime("%Y年%m月%d日"))
print(now.strftime("%H:%M:%S"))
print(now.strftime("%Y-%m-%d"))