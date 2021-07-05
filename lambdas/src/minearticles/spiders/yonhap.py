import scrapy
from scrapy.http import Request
from w3lib.url import add_or_replace_parameters
import json
import requests
from scrapy.http import Request
from datetime import datetime
import re
from scrapy.http import TextResponse


class YonhapSpider(scrapy.Spider):
    
    name = "yonhap"
    download_delay = 5.0
    handle_httpstatus_list = [200]
    def start_requests(self):
        URL = 'https://en.yna.co.kr/business/it'
        response = requests.get(URL)
        response =TextResponse(body = response.text, url = URL, encoding='utf-8')
        content = response.xpath('//div[@class="txt-con"]')
        for article_link in content.xpath('.//h2[@class="tit"]'):
            article_url='https:'+ article_link.xpath('.//@href').get()
            title=article_link.xpath('.//text()').get()
            print(article_url)
            yield(scrapy.Request(url=article_url, callback=self.parse_article, meta={'article_title': title, 'url': article_url}))

    def parse_article(self, response):
        
        content = response.xpath('//section[@class="contents"]')
        title = response.meta['article_title'] 
        url = response.meta['url'] 
        text=  ''.join(content.xpath('.//div[@class="inner"]//p//text()').extract())
        blurp = content.xpath('.//div[@class="inner"]//p//text()').get()
        imgurl = response.xpath('//link[@rel="image_src"]//@href').get() 
        date = content.xpath('.//span[@class="txt"]').get()
        date = re.search('[A-Za-z]+ [0-9]+?, [0-9]{4}',date)[0] 
        if date!='':
            date= datetime.strptime(date, "%B %d, %Y")
        else:
            date = datetime.today() 
            date = date.replace(day=1) 
        date  =datetime.strftime(date, "%d/%m/%Y")
        
        yield {
             'title': title,
             'imgurl': imgurl,
             'date': date,
             'blurp' : blurp,
             'url': url,
             'text': text,
             'category': 'technology',
             'source': self.name,
             'tags':None
         }

    
