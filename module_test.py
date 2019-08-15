import os
import time
import re
# import lxml
from lxml import etree
from tool import read_txt_file_to_list

with open('tttttt.html','r',encoding = 'utf-8') as f:
    fileHtml = f.read()

sensitiveKeywordListUri = 'sensitiveKeywords.txt'
sensitiveKeywordList = read_txt_file_to_list(sensitiveKeywordListUri)
print(sensitiveKeywordList)
isHaveSensitiveKeyword = True
fileWeight = 0
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
    print(havedSensitiveKeywordList)
