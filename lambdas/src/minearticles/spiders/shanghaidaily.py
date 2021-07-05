import scrapy
from scrapy.http import Request
from w3lib.url import add_or_replace_parameters
import json
import requests
from scrapy.http import Request
from datetime import datetime
import re
from scrapy.http import TextResponse


class ShanghaiSpider(scrapy.Spider):
    
    name = "shanghai"
    download_delay = 5.0
    handle_httpstatus_list = [200]
    allowed_domains = ['www.shine.cn']
    start_urls = ['https://www.shine.cn/biz/tech/']

    def parse(self, response):
        content = response.xpath('//div[@class="list-story"]')
        category = response.request.url
        category = re.search('([^/]*)/$',category).group(1)
        if category == 'tech':
            category = 'technology'
        for article_link in content:
            article_url='https://www.shine.cn'+ article_link.xpath('.//a//@href').get()
            title=article_link.xpath('.//div[@class="list-card-text"]//h2//text()').get()
            imgurl= article_link.xpath('.//img//@data-original').get()
            # print(imgurl)
            yield(scrapy.Request(url=article_url, callback=self.parse_article, meta={'article_title': title, 'url': article_url, 'imgurl': imgurl, 'category': category}))

    def parse_article(self, response):
        
        title = response.meta['article_title'] 
        url =response.meta['url']
        imgurl = response.meta['imgurl']
        text = ''.join(response.xpath('//div[@class="content"]//p//text()').extract())
        blurp = response.xpath('//div[@class="caption"]//p//text()').get()
        if blurp == None:
            blurp = response.xpath('//div[@class="content"]//p//text()').get()
        date = ''.join(response.xpath('//span[@class="glyphicon glyphicon-time"]/../text()').extract()).strip()
        date = re.search('[0-9]{4}-[0-9]{2}-[0-9]{2}',date)[0]
        try:
            date= datetime.strptime(date, "%Y-%m-%d")
        except:
            date = datetime.today() 
            date = date.replace(day=1) 
        date=datetime.strftime(date, "%d/%m/%Y")
        category = response.meta['category'] 


        yield {
             'title': title,
             'imgurl': imgurl,
             'date': date,
             'blurp' : blurp,
             'url': url,
             'text': text,
             'category': category,
             'source': self.name,
             'tags':None
         }

    
