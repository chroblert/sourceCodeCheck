# @Author: JC
import requests
import json
from lxml import etree
from tool import read_json_file_to_object
from tool import get_html
from tool import save_object_to_json_file
from tool import save_html_response_to_html_file
from tool import read_txt_file_to_list
from tool import Logger
from login import get_cookie_from_github
from copy import deepcopy
import re
import os
import sys
import time
import hashlib
import shutil


def get_html_with_keyword(keyword,cookie,pageNum = 1):
    '''
    抓取包含关键词的某一页的user/project
    '''
    url = 'https://github.com/search?o=desc&q="'+ keyword + '"&s=indexed&type=Code&p='+ str(pageNum)
    html = get_html(url,cookie = cookie)
    if html != 'Fail':
        dom_tree = etree.HTML(html)
        # xpath匹配
        userProjects = dom_tree.xpath('//*[@id="code_search_results"]/div[1]/div/div[1]/div/a[1]/text()')
        for userProject in userProjects:
            print(userProject)
        bottomTab = dom_tree.xpath('//*[@id="code_search_results"]/div[2]/div/a/text()')
        isEnd = True
        for tab in bottomTab:
            # print(tab)
            if tab == "Next":
                isEnd = False
        if not isEnd:
            print("第%d页结束，继续下一页"%pageNum)
        else:
            print("整体结束")
    else:
        isEnd = False
        userProjects = []
    return isEnd,userProjects

def get_all_user_project_with_keyword(keyword = 'chroblert',cookie={}):
    '''
    抓取包含关键词的所有页的user/project
    '''
    print("抓取所有包含%s关键词的user和project"%keyword)
    pageNum = 0
    #isEnd,allUserProjectList = get_html_with_keyword(keyword = keyword,cookie = cookie,pageNum = pageNum)
    isEnd = False
    allUserProjectList = []
    while(not isEnd):
        pageNum = pageNum + 1
        isEnd,userProjectList = get_html_with_keyword(keyword = keyword,cookie = cookie,pageNum = pageNum)
        if len(userProjectList) == 0:
            #pageNum = pageNum -1
            print('没有获取到%d页的内容，继续抓取第%d页'%(pageNum-1,pageNum))
        else:
            allUserProjectList.extend(userProjectList)
            print(userProjectList)
    return allUserProjectList
    
def save_List_to_file(dataList,fileName = 'allUserProjectList.txt'):
    with open(fileName,'w') as f:
        for i in dataList:
            f.write(i)
            f.write('\n')
    # print("保存成功")


def file_data_process(uri):
    '''
    该函数用于处理初始的格式为user/project的字符串，整理成一个字典，并存储为json文件
    :uri 包含字符串的文件
    '''
    userProjectDict = {}
    with open(uri,'r') as f:
        lineList = f.readlines()
    print(len(lineList))
    for i in lineList:
        user,project = i.split('/')
        project = project.replace('\n','')
        print(user)
        if user not in userProjectDict.keys():
            userProjectDict[user] = []
        if project not in userProjectDict[user]:
            userProjectDict[user].append(project)
    #print(userProjectDict)
    return userProjectDict

def get_all_fileLink_one_user_one_project(userName,projectName,cookie = {}):
    url = 'https://github.com/' + userName + '/' + projectName
    return deepcopy(get_fileLink_use_recursive(url = url,cookie = cookie)) 
def get_fileLink_use_recursive(url,cookie = {}):
    '''
    递归实现抓取文件链接
    '''
    # 1. 结束条件：当访问目录url获得的内容里只有文件名，没有目录名(理想情况)；特殊情况（无法访问目标url），同样结束
    html = get_html(url = url ,cookie = cookie)
    fileLinkList = []
    # 第一个递归结束条件
    print("递归查找 %s 目录下的文件"%url)
    if html == 'Fail' :
        # print('html = Fail,结束递归: ' + url)
        return []
    else:
        dom_tree = etree.HTML(html)
        fileAndDirLinkList = dom_tree.xpath('//tr[@class="js-navigation-item" or @class="js-navigation-item navigation-focus"]//td[@class="content"]//a/@href')
        fileLinkCount = 0
        for fileOrDirLink in fileAndDirLinkList:
            # 为链接前加上https://github.com
            fileOrDirLink = 'https://github.com' + fileOrDirLink
            # if fileOrDirLink.split('/')[3] == 'blob':
            if fileOrDirLink.split('/')[5] == 'blob': # 代表是文件
                # fileLink的个数。
                fileLinkCount = fileLinkCount + 1
                # add：只有在文件后缀格式不为可读文件的情况下，才添加进fileLinkList中
                if fileOrDirLink.split('.')[len(fileOrDirLink.split('.')) - 1] in ['jpg','png','gif','ico','svg','zip','rar','exe','bin','jar','mp3','mp4','class','pdf']:
                    print('不记录不可读文件链接')
                    pass
                else:
                    fileLinkList.append(fileOrDirLink)
            else: # 说明是目录
                searchResult = get_fileLink_use_recursive(fileOrDirLink)
                # print("查找结束，返回查找到的fileLinkList")
                # print(searchResult)
                fileLinkList.extend(searchResult)
        # 第二个递归结束条件:若fileLink的个数为fileOrDirLink列表中元素的个数，则结束递归
        if fileLinkCount == len(fileAndDirLinkList):
            # print('该目录下全部为文件链接，结束递归：' + url)
            # 返回查找得到的fileLinkList
            return fileLinkList
        # 递归返回结果
        return fileLinkList

class userItem:
    '''
    一个用于存储用户、权重、项目列表、文件链接列表的结构
    '''
    def __init__(self):
        self.userName = '' # 名称
        self.weight = 0 # 权重
        self.projectList = [] # 包含关键词的项目的list
        self.fileLinkDict = {} # 包含关键词的文件链接的dict 格式为 {"project1":["fileLink1","fileLink2","fileLink3"],"project2":["fileLink1","fileLink2","fileLink3"]}

def get_all_fileLink(dataDict,cookie = {}):
    '''
    根据dataDict得到所有的文件链接

    :dataDict 是上面定义的结构
    '''
    userItemList = []
    for user in dataDict.keys():
        print("user:" + user)
        uItem = userItem()
        uItem.userName = user
        uItem.projectList.extend(dataDict[user])
        fileLinkDict = {}
        for project in dataDict[user]:
            #print(project)
            allFileLinkList = get_all_fileLink_one_user_one_project(userName = user,projectName = project,cookie = cookie)
            fileLinkDict[project] = []
            fileLinkDict[project].extend(allFileLinkList)
            print("%s 用户 %s 项目内包含敏感信息的文件链接：=======================")
            print(allFileLinkList)
        uItem.fileLinkDict.update(fileLinkDict)
        userItemList.append(uItem)
    #print(userItemList)
    return userItemList

def read_json_file_to_userItemList(fileName):
    '''
    从json格式的文件中读取数据并返回一饿userItemList

    :fileName 存储json数据的文件名
    '''
    allUserItemList = read_json_file_to_object(fileName)
    # print(allUserItemList)
    allUItemList = []
    for uItem in allUserItemList:
        usItem = userItem()
        usItem.userName = uItem['userName']
        usItem.weight = uItem['weight']
        usItem.projectList.extend(deepcopy(uItem['projectList']))
        usItem.fileLinkDict= deepcopy(uItem['fileLinkDict'])
        allUItemList.append(usItem)
    return allUItemList


def save_userItemList_to_json_file(userItemList,fileName = 'userItemList.json'):
    '''
    该函数将从json文件中读取数据并将其转换为userItem类型，存储在一个list中
    '''
    tempList = []
    tempDict = {}
    for userItem in userItemList:
        tempDict['userName'] = userItem.userName
        tempDict['weight'] = userItem.weight
        tempDict['projectList'] = userItem.projectList
        tempDict['fileLinkDict'] = userItem.fileLinkDict
        tempList.append(deepcopy(tempDict))
    save_object_to_json_file(tempList,fileName)

def search_all_sensitive_data_in_one_file(fileLink,cookie = {}):
    '''
    从给定的fileLink中去查找一些关键信息，并进行匹配返回
    
    :fileLink 文件链接
    :cookie 维持登录状态的cookie值
    :return fileWeight,fileHtml,list(set(retIPList)),list(set(retDomainList)),list(set(havedSensitiveKeywordList))
    '''

    companyIPList = read_txt_file_to_list(uri = companyIPListUri)
    companyDomainList = read_txt_file_to_list(companyDomainListUri)
    sensitiveKeywordList = read_txt_file_to_list(sensitiveKeywordListUri)
    fileWeight = 0 # 用来表示该文件包含敏感信息源码的程度，若为0，则表明为正常文件
    # 1. 获取到该文件中的内容
    html = get_html(url = fileLink,cookie=cookie)
    htmlFileName = str(fileLink.split('/')[len(fileLink.split('/'))-1]) + ".html"
    if html != "Fail":
        dom_tree = etree.HTML(html)
        # print(html)
        dom_tree_xpath_result_list = dom_tree.xpath('/html/body/div[4]/div/main//div[@itemprop="text" or@ id="readme"]')
        fileHtml = ''
        if len(dom_tree_xpath_result_list) != 0:
            fileHtml = (etree.tostring(dom_tree_xpath_result_list[0])).decode('utf-8')
        else:
            save_html_response_to_html_file(html,'ttttt.html')
            print("没有匹配到文本中的内容")
        # 2. 提取出响应内容中的所有IP
        allIPList = list(set(re.findall(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',fileHtml)))
        # print("该文件内包含的IP如下：")
        # print(allIPList)
        save_List_to_file(allIPList,'allIPList.txt')
        # 求出companyIPList与allIPList的交集
        # retIPList = list(set(allIPList).intersection(set(companyIPList)))
        retIPList = [i for i in allIPList if i in list(set(companyIPList)) ]
        # 通过交集IPlist的len() 来判断该文件内容中是否有公司的服务器IP
        isHaveCompanyIP = True
        if len(retIPList) == 0:
            isHaveCompanyIP = False
            print("该文件内不包含公司服务器的IP地址")
        else:
            fileWeight = fileWeight + len(retIPList)
            print("包含的公司IP如下：")
            print(list(set(retIPList)))
        # print(allIP)
        # 3. 提取出响应内容的所有域名url
        # allDomainUrlList = list(set(re.findall(r'\b(https?:\/\/.*\.?com|cn|org|edu)\b',fileHtml)))
        # allDomainUrlList = list(set(re.findall(r'(http|https)://(\w+\.){1,3}\w+',fileHtml)))
        allDomainUrlList = re.findall(r'\b((?:http|https)://(?:[\w|-]+\.){1,}\w+)\b',fileHtml)
        # print("该文件内包含的域名如下：")
        # print(allDomainUrlList)
        save_List_to_file(list(set(allDomainUrlList)),'allDomainUrlList.txt')
        # 求出allDomainUrlList中的url包含company关键字的url的list
        retDomainList = [i for i in allDomainUrlList if company in i]
        # 通过交集domainList的len()来判断该文件内容中是否有公司的domain
        isHaveCompanyDomain = True
        if len(retDomainList) == 0:
            isHaveCompanyDomain = False
            print("该文件内不包含公司服务器的域名")
        else:
            fileWeight = fileWeight + len(retDomainList)
            print("包含的公司域名如下：")
            print(list(set(retDomainList)))
        # 4. 检索该文件内是否有一些敏感信息词汇
        isHaveSensitiveKeyword = True
        havedSensitiveKeywordList = []
        for sensitiveKeyword in sensitiveKeywordList:
            regPattern = re.compile(r'' + sensitiveKeyword + '')
            result = regPattern.findall(fileHtml)
            havedSensitiveKeywordList.extend(result)
        if len(havedSensitiveKeywordList) == 0:
            isHaveSensitiveKeyword = False
            print("不包含一些敏感信息词汇")
        else:
            fileWeight = fileWeight + len(havedSensitiveKeywordList)
            print("包含的敏感词汇如下：")
            print(list(set(havedSensitiveKeywordList)))
        
    else:
        print("在GitHub上读取 %s 文件失败"%fileLink)
        fileWeight = 0
        fileHtml = ''
        retIPList = []
        retDomainList = []
        havedSensitiveKeywordList = []
    return fileWeight,fileHtml,list(set(retIPList)),list(set(retDomainList)),list(set(havedSensitiveKeywordList))
    # 4. 响应内容中是否包含普通敏感关键词

def get_sensitive_info_for_one_file(fullDir,fileLink,cookie = {}):
    '''
    对于给定的文件链接，调用search_all_sensitive_data_in_one_file()函数，去得到一些关键信息。

    若文件内包含敏感信息，则fileWeight为相应的权重，returnInfo包含文件存储名，文件权重，文件敏感词list，domainlist，IPList
    :fullDir是为某用户某项目创建的目录 
    :fileLink是某用户某项目内的一个文件的链接
    :cookie是去访问链接时需要用到的cookie
    :return fileWeight,returnInfo
    '''
    fileWeight,fileHtml,retIPList,retDomainList,havedSensitiveKeywordList = search_all_sensitive_data_in_one_file(fileLink = fileLink,cookie = cookie)
    if fileWeight != 0:
        toStoreFileNameB = str(fileLink.split('/')[len(fileLink.split('/'))-1])
        # 此处对要保存的文件名做处理，因为字符个数限制，否则可能会报错
        # 格式为 ：url编码后的源文件名-MD5(除了用户和项目名之外的url编码后的文件名).html
        fileNameUsedToComputeMD5Hash = '-'.join(fileLink.split('/')[5:]) + ".html"
        fileNameMD5Hash = str(hashlib.md5(fileNameUsedToComputeMD5Hash.encode('utf-8')).hexdigest())
        toStoreFileNameA = toStoreFileNameB + '-' + fileNameMD5Hash + '.html'
        toStoreFileName = fullDir + '/' + toStoreFileNameA
        # 将包含敏感信息的文件的具体内容下载到本地
        print("将包含敏感信息的文件的具体内容下载到本地")
        save_html_response_to_html_file(responseData = fileHtml,htmlFileName=toStoreFileName)
        # toStoreInfo = userName + '|#|' + projectName + '|#|'  + toStoreFileNameA + '|#|' + str(fileWeight) + '|#|' + ' , '.join(havedSensitiveKeywordList) + '|#|' + ' , '.join(retDomainList)  + '|#|' + ' , '.join(retIPList)
        returnInfo = toStoreFileNameA + '|#|' + str(fileWeight) + '|#|' + ' , '.join(havedSensitiveKeywordList) + '|#|' + ' , '.join(retDomainList)  + '|#|' + ' , '.join(retIPList)
    else:
        returnInfo = ''
    return fileWeight,returnInfo

def get_sensitive_info_for_one_userProject(scanResultDir,userName,projectName,userItemDict,cookie = {}):
    '''
    获取用户某个项目带有敏感信息的情况
    '''
    # fullUserProjectDir是针对于某个用户的某个项目的目录
    fullUserProjectDir = scanResultDir + '/' + userName + '/' + projectName 
    if not os.path.exists(fullUserProjectDir):
        os.makedirs(fullUserProjectDir)
    userProjectWeight = 0
    with open(fullUserProjectDir + '/result.txt','w',encoding = 'utf-8') as f:
        f.write('userName|#|projectName|#|fileLinkUrl|#|toStoreFileName|#|fileWeight|#|havedSensitiveKeywordList|#|retDomainList|#|retIPList')
        f.write('\n')

    fileLinkUrlList = userItemDict.fileLinkDict[projectName]
    for fileLinkUrl in fileLinkUrlList:
        print("|||||======%s--->%s--->%s ======|||||"%(userName,projectName,fileLinkUrl))
        fileWeight,fileInfo = get_sensitive_info_for_one_file(fullDir = fullUserProjectDir,fileLink = fileLinkUrl,cookie = cookie)
        if fileWeight != 0:
            toStoreFileInfoWithUserProjectName = userName + '|#|' + projectName + '|#|' + fileLinkUrl + '|#|' + fileInfo
            with open( fullUserProjectDir + '/result.txt','a',encoding = 'utf-8') as f:
                f.write(toStoreFileInfoWithUserProjectName)
                f.write('\n')
            userProjectWeight = userProjectWeight + fileWeight
        else:
            pass
    return userProjectWeight

def get_sensitive_info_for_one_user(scanResultDir,userName,userItemDict,cookie = {}):
    '''
    获取一个用户带有敏感信息的情况
    '''
    projectNameList = userItemDict.projectList
    userWeight = 0
    os.makedirs(scanResultDir + '/' + userName)
    with open(scanResultDir + '/' + userName + '/result.txt','w',encoding = 'utf-8') as f:
        f.write('userName|#|projectName|#|userProjectWeight')
        f.write('\n')
    for projectName in projectNameList:
        print("|||||======%s--->%s ======|||||"%(userName,projectName))
        userProjectWeight = get_sensitive_info_for_one_userProject(scanResultDir = scanResultDir,userName = userName,projectName = projectName,userItemDict = userItemDict,cookie = cookie)
        if userProjectWeight != 0 :
            toStoreUserProjectInfo = userName + '|#|' + projectName + '|#|' + str(userProjectWeight)
            with open(scanResultDir + '/' + userName + '/result.txt','a',encoding = 'utf-8') as f:
                f.write(toStoreUserProjectInfo)
                f.write('\n')
            userWeight = userWeight + userProjectWeight
        else:
            pass
    return userWeight

def get_sensitive_info_for_github(scanResultDir,userItemList,cookie = {}):
    '''
    获取GitHub上关于敏感信息的情况
    '''
    # userNameList = ['qiumingzhao']
    with open(scanResultDir + '/result.txt','w',encoding = 'utf-8') as f:
        f.write('userName|#|userWeight')
        f.write('\n')
    for userItemDict in userItemList:
        # print(type(userItemDict))
        userName = userItemDict.userName
        print("|||||======%s======|||||"%userName)
        userWeight = get_sensitive_info_for_one_user(scanResultDir = scanResultDir,userName = userName,userItemDict = userItemDict,cookie = cookie)
        if userWeight != 0:
            toStoreUserInfo = userName + '|#|' + str(userWeight)
            with open(scanResultDir + '/result.txt','a',encoding = 'utf-8') as f:
                f.write(toStoreUserInfo)
                f.write('\n')
        else:
            # 删除为该用户创建的目录
            pathToBeDelete = scanResultDir + '/' + userName
            try:
                shutil.rmtree(pathToBeDelete)
            except OSError as e:
                print(e)
            else:
                print("The directory is deleted successfully")
    print('在Github上的源码扫描结束')
            
def get_all_user_project_with_all_keyword(uri = 'companyKeywords.txt',cookie = {}):
    '''
    获取所有带有关键词的所有的用户名和项目名
    '''
    allUserProjectList = []
    companyKeywordList = read_txt_file_to_list(uri = uri)
    for companyKeyword in companyKeywordList:
        # 将list转为set再转为list是为了去掉初始list中的重复数据
        allUserProjectList.extend(list(set(get_all_user_project_with_keyword(keyword = companyKeyword,cookie = cookie))))
    return deepcopy(list(set(allUserProjectList)))

def show_search_result(scanResultDirUri):
    '''
    将最后所有的结果收集起来，并存储进show-result.txt文件中
    '''
    userResultTxtUri = scanResultDirUri + '/result.txt'
    userList = read_txt_file_to_list(userResultTxtUri)
    userList = deepcopy(userList[1:])
    allUserProjectFileList = []
    for user in userList:
        userProjectResultTxtUri = scanResultDirUri + '/' + user.split('|#|')[0] + '/result.txt'
        userProjectList = read_txt_file_to_list(userProjectResultTxtUri)
        userProjectList = deepcopy(userProjectList[1:])
        for userProject in userProjectList:
            userProjectFileResultTxtUri = scanResultDirUri + '/' + user.split('|#|')[0] + '/' + userProject.split('|#|')[1] + '/result.txt'
            userProjectFileList = read_txt_file_to_list(userProjectFileResultTxtUri)
            allUserProjectFileList.extend(deepcopy(userProjectFileList[1:]))
    save_List_to_file(allUserProjectFileList,scanResultDirUri + '/show-result.txt')



if __name__ == '__main__':
    scanTimeAsDir = time.strftime('%Y%m%d%H%M',time.localtime(time.time()))
    scanResultDir = 'scanResult/' + scanTimeAsDir
    if not os.path.exists(scanResultDir):
        os.makedirs(scanResultDir)
    overallScanResultUri = scanResultDir + '/' + 'scanResult.txt'
    logPath = scanResultDir + '/Logs'
    if not os.path.exists(logPath):
        os.makedirs(logPath)
    sys.stdout = Logger(logPath + '/info.log',sys.stdout)
    sys.stderr = Logger(logPath + '/error.log',sys.stderr)
    sys.stderr = Logger(logPath + '/error.log',sys.stderr)
    # 一些重要文件
    company='chroblert' #公司的一个标志信息
    companyKeywordListUri = './config/companyKeywords.txt'
    companyIPListUri = './config/companyIP.txt'
    companyDomainListUri = './config/companyDomain.txt'
    sensitiveKeywordListUri = './config/sensitiveKeywords.txt'
    # 1. 拿到用于保持登录状态的cookie
    cookie = get_cookie_from_github(refreshCookie=False)
    print(cookie)
    # 2. 拿到包含所有关键词的所有用户名/项目名
    allUserProjectList = get_all_user_project_with_all_keyword(uri = companyKeywordListUri,cookie = cookie)
    save_List_to_file(allUserProjectList,fileName = 'allUserProjectList.txt')
    # print(allUserProjectList)
    # 3. 将格式为用户名/项目名的字符串进行处理，存储为字典格式,并保存到json文件中
    allUserProjectListUri = "allUserProjectList.txt"
    userProjectDict = file_data_process(allUserProjectListUri)
    save_object_to_json_file(userProjectDict,'allUserProjectDict.json')
    # # 4. 在某用户的某个仓库中搜索关键词，得到仓库中所有包含该关键词的文件链接，并将结果保存到json文件中
    allUserProjectDictUri = 'allUserProjectDict.json'
    allUserProjectDict = read_json_file_to_object(allUserProjectDictUri)
    allUserItemList = get_all_fileLink(allUserProjectDict,cookie = cookie)
    # print("保存成文件")
    save_userItemList_to_json_file(allUserItemList,fileName = 'allUserItemList.json')
    allUserItemListUri = 'allUserItemList.json'
    # 5. 读取文件中的数据
    allUserItemList = read_json_file_to_userItemList(allUserItemListUri)
    # print(allUserItemList)
    get_sensitive_info_for_github(scanResultDir = scanResultDir,userItemList = allUserItemList,cookie=cookie)
    # 6. 搜集所有的数据并存放进一个文件中
    show_search_result(scanResultDir)
    