import requests
import json
from lxml import etree
# from lxml import html as lxmlhtml
from tool import read_json_file_to_object
from tool import get_html
from tool import save_object_to_json_file
from tool import save_html_response_to_html_file
from tool import read_txt_file_to_list
from login import get_cookie_from_github
from copy import deepcopy
import re
import os
import time
import hashlib

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

def get_all_user_project_with_keyword(keyword = 'gaiaworks',cookie={}):
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
    


def get_fileLink_one_page(user,project,keyword = 'gaiaworks',cookie = {} ,pageNum = 1):
    '''
    根据user和project，搜索在项目中包含关键词的具体文件链接
    '''
    url = 'https://github.com/' + user + '/' + project + '/search?o=desc&p=' + str(pageNum) + '&q=%22' + keyword + '%22&s=indexed'
    html = get_html(url,cookie = cookie)
    if html != 'Fail':
        dom_tree = etree.HTML(html)
        # xpath匹配
        fileLinks = dom_tree.xpath('//*[@id="code_search_results"]/div/div/div[1]/div/a/@href')
        bottomTab = dom_tree.xpath('//*[@id="code_search_results"]/div[2]/div/a/text()')
        isEnd = True
        for tab in bottomTab:
            #print(tab)
            if tab == "Next":
                isEnd = False
        if not isEnd:
            print("第%d页结束，继续下一页"%pageNum)
        else:
            print("整体结束")
    else:
        isEnd = False
        fileLinks = []
    fileLinkList = []
    if len(fileLinks) != 0:
        for fileLink in fileLinks:
            fileLinkList.append('https://github.com' + str(fileLink))
    return isEnd,fileLinkList
    #with open('result.html','w',encoding='utf-8') as f:
    #    f.write(html)

def get_all_fileLink_one_user_one_project(user,project,keyword = 'gaiaworks',cookie = {}):
    '''
    抓取包含关键词的所有页的fileLink
    '''
    print("抓取%s用户的%s仓库中所有包含%s关键词的fileLink"%(user,project,keyword))
    pageNum = 0
    #isEnd,allUserProjectList = get_html_with_keyword(keyword = keyword,cookie = cookie,pageNum = pageNum)
    isEnd = False
    allFileLinkList = []
    while(not isEnd):
        pageNum = pageNum + 1
        isEnd,fileLinkList = get_fileLink_one_page(user = user,project = project,keyword = keyword,cookie = cookie,pageNum = pageNum)
        if len(fileLinkList) == 0:
            #pageNum = pageNum -1
            print('没有获取到%d页的内容，继续抓取第%d页'%(pageNum-1,pageNum))
        else:
            allFileLinkList.extend(fileLinkList)
            # print(fileLinkList)
    return allFileLinkList

class userItem:
    def __init__(self):
        self.userName = '' # 名称
        self.weight = 0 # 权重
        self.projectList = [] # 包含关键词的项目的list
        self.fileLinkDict = {} # 包含关键词的文件链接的dict 格式为 {"project1":["fileLink1","fileLink2","fileLink3"],"project2":["fileLink1","fileLink2","fileLink3"]}

def get_all_fileLink(dataDict,keyword = 'gaiaworks',cookie = {}):
    userItemList = []
    for user in dataDict.keys():
        print("user:" + user)
        uItem = userItem()
        uItem.userName = user
        uItem.projectList.extend(dataDict[user])
        fileLinkDict = {}
        for project in dataDict[user]:
            #print(project)
            allFileLinkList = get_all_fileLink_one_user_one_project(user = user,project = project,keyword = keyword,cookie = cookie)
            fileLinkDict[project] = []
            fileLinkDict[project].extend(allFileLinkList)
            print("zong=======================")
            print(allFileLinkList)
        uItem.fileLinkDict.update(fileLinkDict)
        userItemList.append(uItem)
    #print(userItemList)
    return userItemList

def read_json_file_to_userItemList(fileName):
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
    一个IP list
    一个域名 list
    普通的敏感字符串 list

    return:
    
    '''
    # gaiaIPListUri = 'gaiaIP.txt'
    # gaiaDomainListUri = 'gaiaDomain.txt'
    # sensitiveKeywordListUri = 'sensitiveKeywords.txt'
    gaiaIPList = read_txt_file_to_list(uri = gaiaIPListUri)
    gaiaDomainList = read_txt_file_to_list(gaiaDomainListUri)
    sensitiveKeywordList = read_txt_file_to_list(sensitiveKeywordListUri)
    fileWeight = 0 # 用来表示该文件包含敏感信息源码的程度，若为0，则表明为正常文件
    # 1. 获取到该文件中的内容
    html = get_html(url = fileLink,cookie=cookie)
    htmlFileName = str(fileLink.split('/')[len(fileLink.split('/'))-1]) + ".html"
    if html != "Fail":
        dom_tree = etree.HTML(html)
        # print(html)
        # dom_tree_xpath_result_list = dom_tree.xpath('/html/body/div[4]/div/main/div[3]/div[1]/div[3]/div[2]/table')
        # dom_tree_xpath_result_list = dom_tree.xpath('/html/body/div[4]/div/main//div[@itemprop="text"]/table')
        # dom_tree_xpath_result_list = dom_tree.xpath('/html/body/div[4]/div/main//div[@itemprop="text"]')
        dom_tree_xpath_result_list = dom_tree.xpath('/html/body/div[4]/div/main//div[@itemprop="text" or@ id="readme"]')
        fileHtml = ''
        if len(dom_tree_xpath_result_list) != 0:
            fileHtml = (etree.tostring(dom_tree_xpath_result_list[0])).decode('utf-8')
        else:
            save_html_response_to_html_file(html,'ttttt.html')
            print("没有匹配到文本中的内容")

        # fileHtml = (etree.tostring(dom_tree.xpath('/html/body/div[4]/div/main/div[3]/div[1]/div[3]/div[2]/table')[0])).decode('utf-8')
        # fileHtml = ''.join(dom_tree.xpath('/html/body/div[4]/div/main/div[3]/div[1]/div[3]/div[2]/table'))
        # test = dom_tree.xpath('/html/body/div[4]/div/main/div[3]/div[1]/div[3]/div[2]/table')
        # print(test)
        # print(len(test))
        # testList = []
        # for i in test:
        #     print(etree.tostring(i).decode('utf-8'))
        #     testList.append(etree.tostring(i).decode('utf-8'))
        # fileHtml = ''.join(testList)
        # print(type(test))
        # input("暂停")
        # save_html_response_to_html_file(responseData = fileHtml,htmlFileName= htmlFileName)
        # print("html response保存到%s文件"%htmlFileName)
        # 2. 提取出响应内容中的所有IP
        allIPList = list(set(re.findall(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',fileHtml)))
        # print("该文件内包含的IP如下：")
        # print(allIPList)
        save_List_to_file(allIPList,'allIPList.txt')
        # 求出gaiaIPList与allIPList的交集
        retIPList = list(set(allIPList).intersection(set(gaiaIPList)))
        # 通过交集IPlist的len() 来判断该文件内容中是否有公司的服务器IP
        isHaveGaiaIP = True
        if len(retIPList) == 0:
            isHaveGaiaIP = False
            print("该文件内不包含公司服务器的IP地址")
        else:
            fileWeight = fileWeight + len(retIPList)
            print("包含的公司IP如下：")
            print(retIPList)
        # print(allIP)
        # 3. 提取出响应内容的所有域名url
        # allDomainUrlList = list(set(re.findall(r'\b(https?:\/\/.*\.?com|cn|org|edu)\b',fileHtml)))
        # allDomainUrlList = list(set(re.findall(r'(http|https)://(\w+\.){1,3}\w+',fileHtml)))
        allDomainUrlList = list(set(re.findall(r'\b((?:http|https)://(?:\w+\.){1,}\w+)\b',fileHtml)))
        # print("该文件内包含的域名如下：")
        # print(allDomainUrlList)
        save_List_to_file(allDomainUrlList,'allDomainUrlList.txt')
        # 求出allDomainUrlList中的url包含gaia关键字的url的list
        retDomainList = [i for i in allDomainUrlList if 'gaia' in i]
        # 通过交集domainList的len()来判断该文件内容中是否有公司的domain
        isHaveGaiaDomain = True
        if len(retDomainList) == 0:
            isHaveGaiaDomain = False
            print("该文件内不包含公司服务器的域名")
        else:
            fileWeight = fileWeight + len(retDomainList)
            print("包含的公司域名如下：")
            print(retDomainList)
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
        print("在GitHub上读取%s文件失败"%fileLink)
        fileWeight = 0
        fileHtml = ''
        retIPList = []
        retDomainList = []
        havedSensitiveKeywordList = []
    return fileWeight,fileHtml,retIPList,retDomainList,list(set(havedSensitiveKeywordList))
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
    # fullUserProjectDir是针对于某个用户的某个项目的目录
    fullUserProjectDir = scanResultDir + '/' + userName + '/' + projectName 
    if not os.path.exists(fullUserProjectDir):
        os.makedirs(fullUserProjectDir)
    userProjectWeight = 0
    with open(fullUserProjectDir + '/result.txt','w',encoding = 'utf-8') as f:
        f.write('userName|#|projectName|#|toStoreFileName|#|fileWeight|#|havedSensitiveKeywordList|#|retDomainList|#|retIPList')
        f.write('\n')
    # fileLinkUrlList = ['https://github.com/qiumingzhao/LearnJava/blob/01253ebc4d3fef53ee4ceb9e94796333f2010f22/asset/src/main/java/com/benlai/asset/task/Clock.java']
    # print(type(userItemDict.fileLinkDict))
    # print(userItemDict.projectList)
    # print(userItemDict.fileLinkDict.keys())
    fileLinkUrlList = userItemDict.fileLinkDict[projectName]
    for fileLinkUrl in fileLinkUrlList:
        print("|||||======%s--->%s--->%s ======|||||"%(userName,projectName,fileLinkUrl))
        fileWeight,fileInfo = get_sensitive_info_for_one_file(fullDir = fullUserProjectDir,fileLink = fileLinkUrl,cookie = cookie)
        if fileWeight != 0:
            toStoreFileInfoWithUserProjectName = userName + '|#|' + projectName + '|#|' +fileInfo
            with open( fullUserProjectDir + '/result.txt','a',encoding = 'utf-8') as f:
                f.write(toStoreFileInfoWithUserProjectName)
                f.write('\n')
            userProjectWeight = userProjectWeight + fileWeight
        else:
            pass
    return userProjectWeight

def get_sensitive_info_for_one_user(scanResultDir,userName,userItemDict,cookie = {}):
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
            pass
    print('在Github上的源码扫描结束')
            
def get_all_user_project_with_all_keyword(uri = 'gaiaKeywords.txt',cookie = {}):
    allUserProjectList = []
    gaiaKeywordList = read_txt_file_to_list(uri = uri)
    for gaiaKeyword in gaiaKeywordList:
        allUserProjectList.extend(get_all_user_project_with_keyword(keyword = gaiaKeyword,cookie = cookie))
    return deepcopy(allUserProjectList)

if __name__ == '__main__':
    scanTimeAsDir = time.strftime('%Y%m%d%H%M',time.localtime(time.time()))
    scanResultDir = 'scanResult/' + scanTimeAsDir
    if not os.path.exists(scanResultDir):
        os.makedirs(scanResultDir)
    overallScanResultUri = scanResultDir + '/' + 'scanResult.txt'
    # 一些重要文件
    gaiaKeywordListUri = 'gaiaKeywords.txt'
    gaiaIPListUri = 'gaiaIP.txt'
    gaiaDomainListUri = 'gaiaDomain.txt'
    sensitiveKeywordListUri = 'sensitiveKeywords.txt'
    # 1. 拿到用于保持登录状态的cookie
    cookie = get_cookie_from_github(refreshCookie=False)
    # print(cookie)
    # 2. 拿到包含所有关键词的所有用户名/项目名
    allUserProjectList = get_all_user_project_with_all_keyword(uri = gaiaKeywordListUri,cookie = cookie)
    # save_List_to_file(allUserProjectList,fileName = 'allUserProjectList.txt')
    #print(allUserProjectList)
    # 3. 将格式为用户名/项目名的字符串进行处理，存储为字典格式,并保存到json文件中
    # allUserProjectListUri = "allUserProjectList.txt"
    # userProjectDict = file_data_process(allUserProjectListUri)
    # save_object_to_json_file(userProjectDict,'allUserProjectDict.json')
    # 4. 在某用户的某个仓库中搜索关键词，得到仓库中所有包含该关键词的文件链接，并将结果保存到json文件中
    # allUserProjectDictUri = 'allUserProjectDict.json'
    # allUserProjectDict = read_json_file_to_object(allUserProjectDictUri)
    # allUserItemList = get_all_fileLink(allUserProjectDict,cookie = cookie)
    # print("保存成文件")
    # save_userItemList_to_json_file(allUserItemList,fileName = 'allUserItemList.json')
    allUserItemListUri = 'allUserItemList.json'
    # 5. 读取文件中的数据
    allUserItemList = read_json_file_to_userItemList(allUserItemListUri)
    # print(allUserItemList)
    get_sensitive_info_for_github(scanResultDir = scanResultDir,userItemList = allUserItemList,cookie=cookie)
    



