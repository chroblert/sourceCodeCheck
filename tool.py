import json
import requests
from tenacity import retry, stop_after_attempt, wait_random
from copy import deepcopy

def read_json_file_to_object(uri):
    '''
    该函数用于读取json文件，并返回字典
    :uri json文件的路径
    :return 返回一个字典 
    '''
    print("读取%s文件中的数据："%uri)
    with open(uri,'r') as f:
        temp = json.loads(f.read())
    return temp

class MyException(Exception):
    pass
@retry(reraise = True,stop = stop_after_attempt(5),wait = wait_random(min=1,max=2))
def get_html_retry(url,cookie = {}):
    '''
    若返回值为'Fail',则说明响应失败
    '''
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'Referer': 'https://www.google.com/'}
    proxies = {'http':'114.67.229.212:8080'}
    try:
        response = requests.get(url,cookies = cookie,headers = headers,timeout = 5)#,proxies = proxies)
        html = response.content.decode('utf-8')
        return html
    except TimeoutError:
        print("TimeOutError")
        raise MyException("Fail")
    except Exception as e:
        print("OtherError")
        print(e)
        raise MyException("Fail")

def get_html(url,cookie = {}):
    '''
    若返回值为'Fail',则说明响应失败
    '''
    try:
        html = get_html_retry(url,cookie=cookie)
    except MyException:
        html = 'Fail'
        print("Fail")
    return html

def save_object_to_json_file(objectData , jsonFileName = 'test.json'):
    with open(jsonFileName,'w') as outfile:
        json.dump(objectData,outfile,ensure_ascii=False)
        outfile.write('\n')

def save_html_response_to_html_file(responseData,htmlFileName = "test.html"):
    with open(htmlFileName,'w',encoding = 'utf-8') as f:
        f.write(responseData)

def read_txt_file_to_list(uri):
    lineList = []
    with open(uri,'r',encoding = 'utf-8') as f:
        tempLineList = f.readlines()
        for line in tempLineList:
            lineList.append(line.strip('\n'))
    return deepcopy(lineList)