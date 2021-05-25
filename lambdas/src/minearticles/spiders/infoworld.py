import json
import scrapy
import datetime
from scrapy.http import Request
from w3lib.url import add_or_replace_parameters
import requests
from scrapy.http import TextResponse
import re

class InfoworldSpider(scrapy.Spider):
    name = "infoworld"
    download_delay = 5.0
    handle_httpstatus_list = [200]
    start_urls =['https://www.infoworld.com/category/analytics/','https://www.infoworld.com/category/machine-learning/','https://www.infoworld.com/category/software-development/','https://www.infoworld.com/category/cloud-computing/']
    def parse(self,response):
        # catdict = {'machine-learning': {'4049' :"4995,4825"}, 
        #     'software-development': {'3646':"3646,4403,3443,3808,3469,3761,4434,3470,3881,4047,3471"},
        #     'cloud-computing':{'3255':"4309,3374,3375,3378,3712,4774"}, 
        #     'analytics':{'3551':"3256,3474,3781,3408,4048"}}
        # API_URL = 'https://www.infoworld.com/napi/tile?'
        # for topic in catdict: 
        #     for catid in catdict[topic]:     
        # #     Get parameters
        #         params = {
        #             'def': 'loadMoreList',
        #             'pageType' : 'index',
        #             'catId' : catid,
        #             'includeMediaResources': False,
        #             'createdTypeIds': 1,
        #             'categories': catdict[topic][catid],
        #             'days':-7,
        #             'pageSize':10,
        #             'Offset' : 0,
        #             'ignoreExcludedIds': True,
        #             'brandContentOnly': False,
        #             'includeBlogTypeIds': "1,3",
        #             'includeVideo' : False,
        #             'sortOrder': "date",
        #             'locale_id': 0,
        #             'startIndex': 0
        #             }
        # response = requests.get(API_URL,params=params)
        # response =TextResponse(body = response.text, url = API_URL, encoding='utf-8')
        category = response.request.url
        topic = re.search('([^/]*)/$',category).group(1)
        content=response.xpath('//div[@class="river-well article"]')
        for article_link in content.xpath('.//h3//a'):
            article_url=   article_link.xpath('.//@href').extract_first()
            if article_url.startswith("/article/"):  
                url =  "https://www.infoworld.com" +  article_url   
                request = scrapy.Request(url,cookies={'store_language':'en'}, callback=self.parse_article_pages,meta={'url':url, 'category':topic})
                yield request

    def parse_article_pages(self, request):
       
        #extract image
        imgurl = request.xpath('//img[@itemprop="contentUrl"]/@data-original').get()
        title = request.xpath('//h1[@itemprop="headline"]//text()').get()
        #get date
        date = request.xpath('//span[@class="pub-date"]/@content').get()
        if date!='':
            date =date.split('T')[0]
            date= datetime.datetime.strptime(date, "%Y-%m-%d")
        else:
            date = datetime.datetime.today() 
            date = date.replace(day=1) 
        date  =datetime.datetime.strftime(date, "%d/%m/%Y")
        

        #get the blurp
        blurp = request.xpath('//h3[@itemprop="description"]//text()').get()
        text = ''.join(request.xpath('//div[@itemprop="articleBody"]/descendant::text()').extract()).strip()
        text = re.sub('\[.*\]', '',text)
        tags = request.xpath('//span[@class="primary-cat-name2"]//text()').extract()
        
        url= request.meta['url']
        category = request.meta['category']
         
        yield {
            'title': title,
            'imgurl': imgurl,
            'date': date,
            'blurp' : blurp,
            'url': url,
            'text': text,
            'category': category,
            'tags':tags,
            'source': self.name
         }




   
