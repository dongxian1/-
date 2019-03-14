from lxml import etree
import requests
import time
from urllib.parse import quote
from lxml import etree
import re
import math,random
import time
import pymysql
HEADER = {
    'Host': 'nvsm.cnki.net',
    'Referer': 'http://nvsm.cnki.net/kns/brief/result.aspx?dbprefix=SCDB&crossDbcodes=CJFQ,CDFD,CMFD,CPFD,IPFD,CCND,CCJD',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36',

}
data = {
    'curUrl':'detail.aspx?dbCode=CJFQ&fileName=SHZX201812009',
    'referUrl':'http://nvsm.cnki.net/kns/brief/brief.aspx?pagename=ASP.brief_result_aspx&isinEn=1&dbPrefix=SCDB&dbCatalog=%e4%b8%ad%e5%9b%bd%e5%ad%a6%e6%9c%af%e6%96%87%e7%8c%ae%e7%bd%91%e7%bb%9c%e5%87%ba%e7%89%88%e6%80%bb%e5%ba%93&ConfigFile=SCDB.xml&research=off&t=1552352294569&keyValue=&S=1&sorttype=',
    'action':'file',
    'td':'1552353944641',
    'userName':'',
    'cnkiUserKey':'bf0fbb19-9346-bdbf-ce94-108ce5a1f230'
}
# 获取cookie
BASIC_URL = 'http://kns.cnki.net/kns/brief/result.aspx'
# 利用post请求先行注册一次
SEARCH_HANDLE_URL = 'http://kns.cnki.net/kns/request/SearchHandler.ashx'
# 发送get请求获得文献资源
GET_PAGE_URL = 'http://kns.cnki.net/kns/brief/brief.aspx?pagename='
# 切换页面基础链接
CHANGE_PAGE_URL = 'http://kns.cnki.net/kns/brief/brief.aspx'

class SearchTools(object):

    def __init__(self):
        self.session = requests.Session()
        self.cur_page_num = 1
        # 保持会话
        self.session.get(BASIC_URL, headers=HEADER)
        self.cnkiUserKey = self.set_new_guid()
    def search_reference(self):
        '''
        第一次发送post请求
        再一次发送get请求,这次请求没有写文献等东西
        两次请求来获得文献列表
        '''
        static_post_data = {
            'action': '',
            'NaviCode': '*',
            'ua': '1.21',
            'sinEn': '1',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCDB',
            'DbCatalog': '中国学术文献网络出版总库',
            'ConfigFile': 'SCDB.xml',
            'db_opt': 'CJFQ,CDFD,CMFD,CPFD,IPFD,CCND,CCJD',
            'publishdate_from': '2018-01-01',
            'publishdate_to': '2018-12-01',
            'au_1_sel': 'AU',
            'au_1_sel2': 'AF',
            'au_1_value2': '南京大学',
            'au_1_special1': '=',
            'au_1_special2': '%',
            'his': '0',
            '__': time.asctime(time.localtime()) + ' GMT+0800 (中国标准时间)'
        }
        # 将固定字段与自定义字段组合
        post_data = {**static_post_data}
        # 必须有第一次请求，否则会提示服务器没有用户
        first_post_res = self.session.post(SEARCH_HANDLE_URL, data=post_data, headers=HEADER)
        # get请求中需要传入第一个检索条件的值
        key_value = quote(post_data.get('au_1_value2'))
        self.get_result_url = GET_PAGE_URL + first_post_res.text + '&t=1544249384932&keyValue=' + key_value + '&S=1&sorttype='
        # 检索结果的第一个页面
        second_get_res = self.session.get(self.get_result_url, headers=HEADER)
        lxml = etree.HTML(second_get_res.text)
        link = lxml.xpath('.//table[@class="GridTableContent"]//td/a[@class="fz14"]/@href')
        next_url= lxml.xpath('.//div[@class = "TitleLeftCell"]/a[1]/@href')[0]
        for i in range(2,10):#将下一页的所有链接及以后的所以链接全部存入link列表 转入给详情页函数
            curpage_pattern_compile = re.compile(r'.*?curpage=(\d+).*?')#使用正则将下一页的url中page=替换出来循环处理页数
            self.add = CHANGE_PAGE_URL + re.sub(curpage_pattern_compile, '?curpage=' + str(i),next_url)
            second_get_res = self.session.get(self.add, headers=HEADER)
            lxml = etree.HTML(second_get_res.text)
            add_url = lxml.xpath('.//table[@class="GridTableContent"]//td/a[@class="fz14"]/@href')
            link.extend(add_url)
        return link
    def get_detail_page(self): #抓取详情页内容
        '''
        发送三次请求
        前两次服务器注册 最后一次正式跳转
        '''

        # 这个header必须设置
        page = self.search_reference()
        # for j in page:
        #     if
        for page_url in page:
            time.sleep(3)
            result_url = 'http://nvsm.cnki.net/kns/brief/brief.aspx?pagename=ASP.brief_result_aspx&isinEn=1&dbPrefix=SCDB&dbCatalog=%e4%b8%ad%e5%9b%bd%e5%ad%a6%e6%9c%af%e6%96%87%e7%8c%ae%e7%bd%91%e7%bb%9c%e5%87%ba%e7%89%88%e6%80%bb%e5%ba%93&ConfigFile=SCDB.xml&research=off&t=1552352294569&keyValue=&S=1&sorttype='
            HEADER['Referer'] = result_url
            self.session.cookies.set('cnkiUserKey', self.cnkiUserKey)
            cur_url_pattern_compile = re.compile(
                r'.*?FileName=(.*?)&.*?DbCode=(.*?)&')
            cur_url_set=re.search(cur_url_pattern_compile,page_url)
            # 前两次请求需要的验证参数
            params = {
                'curUrl':'detail.aspx?dbCode=' + cur_url_set.group(2) + '&fileName='+cur_url_set.group(1),
                'referUrl': result_url+'#J_ORDER&',
                'cnkiUserKey': self.session.cookies['cnkiUserKey'],
                'action': 'file',
                'userName': '',
                'td': '1552353944641'
            }
            # 首先向服务器发送两次预请求
            self.session.get(
                'http://i.shufang.cnki.net/KRS/KRSWriteHandler.ashx',
                headers=HEADER,
                params=params)
            self.session.get(
                'http://kns.cnki.net/KRS/KRSWriteHandler.ashx',
                headers=HEADER,
                params=params)
            page_url = 'http://kns.cnki.net' + page_url
            get_res=self.session.get(page_url,headers=HEADER)
            html = etree.HTML(get_res.text)
            # with open('jsc.html','ab+') as f:
            #     f.write(get_res.text.encode('utf-8'))
            title = html.xpath('.//div[@class = "wxTitle"]/h2/text()')
            if title:
                title = title[0]
            else:
                continue
            strs = "-"#拼接字符串
            author = strs.join(html.xpath('.//div[@class="wxTitle"]/div[1]//span/a/text()'))
            orgn = strs.join(html.xpath('.//div[@class="wxTitle"]/div[2]//span/a/text()'))
            content = html.xpath('.//div[contains(@class,"wxBaseinfo")]/p/span[1]/text()')[0]
            key_word =strs.join(html.xpath('.//label[@id="catalog_KEYWORD"]/..//a/text()'))
            key_word = "".join([i.strip() for i in key_word])
            # print(key_word)
            # times =html.xpath('.//p/label/following-sibling::text()')
            Classification = html.xpath('.//p/label[@id="catalog_ZTCLS"]/following-sibling::text()')
            Cdata={
                'title':title,
                'author':author,
                'orgn':orgn,
                'content':content,
                'key_word':key_word,
            }
            # print(Cdata)
            self.mysqls(Cdata)
            # self.pars_page(get_res.text)
    def mysqls(self,Cdata):
        coon = pymysql.connect('127.0.0.1','root','123456','mysql',charset='utf8mb4')
        cursor =coon.cursor()
        cursor.execute('use zhiwang')
        print('成功进入数据库 zhiwang')
        # sql = 'insert into zhiwnagtable(title)values("{东西}")'
        sql = 'insert into zhiwangtable(title,author,orgn,key_word,content)values("{}","{}","{}","{}","{}")'.format(pymysql.escape_string(Cdata['title']),Cdata['author'],Cdata['orgn'],Cdata['key_word'],pymysql.escape_string(Cdata['content']))
        # try:
        print(sql)
        cursor.execute(sql)
        coon.commit()
        print('成功')
        # except:
        #     coon.rollback()
        #     print('失败')


    def set_new_guid(self):
        '''
        生成用户秘钥
        '''
        guid=''
        for i in range(1,32):
            n = str(format(math.floor(random.random() * 16.0),'x'))
            guid+=n
            if (i == 8) or (i == 12) or (i == 16) or (i == 20):
                guid += "-"
        return guid
def main():
    search = SearchTools()
    search.get_detail_page()


if __name__ == '__main__':
    main()
