import requests 
from bs4 import BeautifulSoup
import os
import json

Base_URL = "https://github.com/login"
Login_URL = "https://github.com/session"

def get_github_html(url):
    '''
    这里用于获取登录页的html，以及cookie
    :param url: https://github.com/login
    :return: 登录页面的HTML,以及第一次的cooke
    '''
    response = requests.get(url)
    first_cookie = response.cookies.get_dict()
    print(first_cookie)
    return response.text,first_cookie



def get_token(html):
    '''
    处理登录后页面的html
    :param html:
    :return: 获取csrftoken
    '''
    soup = BeautifulSoup(html,'html.parser')
    res = soup.find("input",attrs={"name":"authenticity_token"})
    token = res["value"]
    print(token)
    return token


def gihub_login(url,token,cookie):
    '''
    这个是用于登录
    :param url: https://github.com/session
    :param token: csrftoken
    :param cookie: 第一次登录时候的cookie
    :return: 返回第一次和第二次合并后的cooke
    '''

    data= {
        "commit": "Sign in",
        "utf8":"✓",
        "authenticity_token":token,
        "login":"jeffrey-li-gaia",
        "password":"GaIa@1234p;/P:?"
    }
    header = {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'}
    response = requests.post(url,data=data,cookies=cookie,headers = header)
    print(response.status_code)
    cookie = response.cookies.get_dict()
    #这里注释的解释一下，是因为之前github是通过将两次的cookie进行合并的
    #现在不用了可以直接获取就行
    # cookie.update(second_cookie)
    return cookie

def get_cookie_from_github(refreshCookie = False):
    '''
    该函数用于登录GitHub，并返回用于保持登录的cookie值
    '''
    if (not os.path.exists("./login_cookie.json")) or refreshCookie:
        print("cookie未存在")
        html,cookie = get_github_html(Base_URL)
        token = get_token(html)
        cookie = gihub_login(Login_URL,token,cookie)
        login_cookie = [{'cookie':cookie},{'token':token}]
        with open("./login_cookie.json",'w') as f:
            f.write(json.dumps(login_cookie))
        print("设置cookie完毕")
    else:
        print("cookie 已存在")
        with open("./login_cookie.json",'r') as f:
            temp = json.loads(f.read())
            #print(temp)
            cookie = temp[0]["cookie"]
            token = temp[1]["token"]
        print("读取cookie完毕")
    return cookie 