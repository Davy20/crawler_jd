# jd_jiashiqi_data.py
# 0228新增info
# ['SKU','Brand','Name','Model','Shop','Info',Price','Commcount']

from bs4 import BeautifulSoup
import requests
import re,json
import pandas as pd
import time
import random
import datetime

#京东加湿器类目
#动态网页爬取

def isConnected():
    try:
        requests.get('http://www.baidu.com',timeout=(3,7))
    except:
        return False
    return True

def getHtml(url,kv): # 只输入URL的主体部分，后面的参数用下面的字典附加上
    
    try:
        r=requests.get(url,headers=kv,timeout=(3,7))
        r.raise_for_status()
        r.encoding='GBK'
        return r.text
    except :
        n = 0
        while isConnected == False:
            time.sleep(5)
            n += 1
            print("\n断网第{0}次重连".format(n), end="\r")

def getSku(url): # 这个函数里获取的每一页60个商品里的SKU，但是每个商品链接内还有多个SKU。
    sku = []
    try:
        html = getHtml(url,kv_sku)
        soup = BeautifulSoup(html,"html.parser")
    except:
        print('页面解析错误')
    
    try:
        next_page = 'https://list.jd.com' + soup.find_all('a',class_='pn-next')[0].attrs['href']
    except:
        next_page = None

    try:
        gl_items=soup.find_all('li',class_='gl-item')
        for gl_item in gl_items:
            data_sku_attrs = gl_item.div.attrs
            data_sku = data_sku_attrs['data-sku']
            sku.append(data_sku)
    except:
        print('sku爬取错误') 
    return sku, next_page

def get_npage_sku(start_url):
    print("开始爬取SKU")
    sku_all_page = [] # 所有页面的直接看到的sku
    
    next_page = start_url
    i=0
    while next_page:
        i += 1
        sku, next_page = getSku(next_page)
        sku_all_page += sku
        print("第{}页已爬完，共{}个SKU".format(i,len(sku)), end="\r")
    sku_all_page_set=list(set(sku_all_page))
    # file_sku = pd.DataFrame(columns=['sku'],data=sku_all_page_set)
    # file_sku.to_csv(save_path_part,encoding='GBK')
    return sku_all_page_set

def get_all_sku(sku): # 获取某个SKU下关联的多个SKU
    url = 'https://item.jd.com/'+sku+'.html'
    try:
        html = getHtml(url,kv_sku)
        soup = BeautifulSoup(html,"html.parser")
    except:
        print("页面解析错误")
    try:
        choose_html = soup.find_all('div', id="choose-attr-1")
        if choose_html == []:
            skus = [sku]
        else :
            pat = re.compile(r'data-sku=\"(\d+)\"')
            skus = pat.findall(str(choose_html))
    except:
        skus = [sku]
        print("get_all_sku解析错误，已设为空值")

    return skus

def get_all_sku_file(sku_list): # 获取一个sku列表里所有的关联SKU并输出文档。
    time_start = time.time()
    print("\n开始获取所有SKU")
    N = len(sku_list)
    n = 0
    sku_all = []
    sku_map = map(get_all_sku, sku_list)
    for i in sku_map:
        sku_all.extend(i)
        n += 1
        print("进度:{0}%".format(round(n * 100 / N)), end="\r")
    sku_all_set=list(set(sku_all))
    print("去重后的SKU_all，共{}个".format(len(sku_all_set)))
    time_end = time.time()
    print('SKU耗时%s秒' % (time_end - time_start))
    return sku_all_set

def getBrand(sku):
    url = 'https://item.jd.com/'+sku+'.html'
    brand = None
    name = None
    model = None
    shop = None
    info = None
    i = 0
    while (brand == None) and (i < 3):
        i += 1
        try:
            html = getHtml(url,kv_sku)
            soup = BeautifulSoup(html,"html.parser")
        except:
            pass
        try:
            brand_html = soup.find_all('ul',id="parameter-brand")
            brand = brand_html[0].a.string
        except:
            brand = None
        if i == 3:
            print("\nbrand解析错误，已设为空值")
    try:
        name_html = soup.find_all('ul',class_="parameter2 p-parameter-list")
        name_html_attr = name_html[0].li.attrs
        name = name_html_attr['title']
    except:
        name = None
    
    try:
        model_html = soup.find_all('div',class_="Ptable-item")
        model_match = re.search(r'型号</dt><dd>(.*)</dd>', str(model_html))
        model = model_match.group(1)
    except:
        model = None
    
    try:
        shop_html = soup.find_all('div',class_="J-hove-wrap EDropdown fr")[0]
        shop = shop_html.a.string
    except:
        shop = None

    try:
        info_html = soup.find_all('div',class_="sku-name")[0]
        if info_html.img:
            info = info_html.img.string.strip()
        else:
            info = info_html.string.strip()
    except:
        info = None
    print(info)
    return [brand] + [name] + [model] + [shop] + [info]

def getPrice(sku):
    url = 'http://p.3.cn/prices/mgets?skuIds=J_' + sku
    price = None
    i = 0
    while (price == None) and (i < 3):
        i += 1
        try:
            html = getHtml(url,kv=None)
            pat = re.compile(r'\"p\":\"(\d+\.\d+)\"')
            match = pat.search(html)
            price = match.group(1)
        except:
            price = None
        if i == 3:
            print("\n{}price解析错误，已设为空值".format(sku))
    return price
    
def getComm(sku):
    url = 'https://club.jd.com/comment/skuProductPageComments.action?callback=fetchJSON_comment98vv51&productId=%d&score=0&sortType=5&page=0&pageSize=10&isShadowSku=0&fold=1'%(eval(sku))
    kv_com = {'Referer': 'https://item.jd.com/'+sku+'.html', 'Sec-Fetch-Mode': 'no-cors', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.90 Safari/537.36'}
    commentcount = None
    i = 0
    while (commentcount == None) and (i < 3):
        i += 1
        try:
            html = getHtml(url,kv_com)
            commentcount_html = re.search(r'"commentCount":(\d*)', html)
            commentcount = commentcount_html.group(1)
        except:
            commentcount = None
        if i == 3:
            print("\n{}comm解析错误，已设为空值".format(sku))
    return commentcount

def data_sku(sku):
    sku = str(sku)
    Brand = getBrand(sku)
    time.sleep(random.randint(3,5))
    price = getPrice(sku)
    time.sleep(random.randint(1,3))
    commentcount = getComm(sku)
    return [sku] + Brand + [price] + [commentcount]

def data_skus(skus):
    jd_datas = []
    columns_name = ['SKU','Brand','Name','Model','Shop','Info','Price','Commcount']
    df_empty = pd.DataFrame(columns=columns_name)
    df_empty.to_csv(save_path, index=False, encoding='GBK')
    i = 0
    len_skus = len(skus)
    for sku in skus:
        i += 1
        progess = i*100/len_skus
        print("共{}个sku，第{}个SKU{}，进度{}%".format(len_skus,i,sku,progess), end='\r')
        jd_datas.append(data_sku(sku)) # 二维数组
        if i % 500 == 0 or i == len(sku_all):
            file = pd.DataFrame(columns=columns_name,data=jd_datas)
            file.to_csv(save_path, mode='a', header=False, index=False, encoding='GBK')
            jd_datas = []

if __name__ == '__main__':
    time_start = time.time()
    start_url = 'https://list.jd.com/list.html?cat=737,738,749&ev=878%5F91715&sort=sort_rank_asc&trans=1&JL=3_%E7%B1%BB%E5%88%AB_%E6%A1%8C%E9%9D%A2%E5%9E%8B#J_crumbsBar'
    today=datetime.date.today()
    formatted_today=today.strftime('%y%m%d')
    file_name = 'jiashiqi_data_200212.csv'
    read_path = 'D:/python/code/crawl/jingdong/savefile/{}'.format(file_name)
    save_path = 'D:/python/code/crawl/jingdong/savefile/jiashiqi_data_{}.csv'.format(formatted_today)
    kv_sku = {'Referer': 'https://list.jd.com/list.html?cat=737,738,749&ev=878%5F1470&sort=sort_rank_asc&trans=1&JL=3_%E7%B1%BB%E5%88%AB_%E5%AE%B6%E7%94%A8%E5%9E%8B','User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.90 Safari/537.36'}
    sku_all_page_set = get_npage_sku(start_url)
    sku_all = get_all_sku_file(sku_all_page_set)
    data_skus(sku_all)
    time_end = time.time()
    print('\n耗时%s秒' % (time_end - time_start))
