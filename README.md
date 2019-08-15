# 文件说明

> - `gaiaIP.txt` : 公司服务器的IP。每行一个IP地址
> - `gaiaDomain.txt`: 公司一些服务的域名。每行一个域名。本版程序暂时未用到
> - `gaiaKeywords.txt`:能够识别为本公司的一些标志性关键字
> - `sensitiveKeywords.txt`:一些比较敏感的关键词，如用户名、密码之类的

# 使用说明

- `pip install -r requirements.txt`
- 按照**文件说明**填写一些内容
- 填写自己github上的用户名和密码
  - 注：在新机器上第一次登录时需要有验证码
  - 因而第一次需要先实际在浏览器中登录，并填写验证码
  - 之后，方可继续正常执行
- 如果需要更新存储的Cookie值，则需要在gitHubSpider.py文件中的`get_cookie_from_github(refreshCookie=False)`False改为True
- 之后运行即可

# 版本说明

- v1.0.0
  - 缺少多线程支持
  - 缺少随机代理IP支持
  - 缺少随机UA支持
  - 现只支持在GitHub上进行源码扫描