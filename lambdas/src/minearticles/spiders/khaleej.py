
import scrapy
from scrapy.http import Request
from w3lib.url import add_or_replace_parameters
import json
import requests
from scrapy.http import Request
import datetime
import re
from scrapy.http import TextResponse


class KhaleejSpider(scrapy.Spider):
    
    name = "khaleej"
    download_delay = 5.0
    handle_httpstatus_list = [200]
    def start_requests(self):
        URL = 'https://www.khaleejtimes.com/technology'
        response = requests.get(URL)
        response =TextResponse(body = response.text, url = URL, encoding='utf-8')
        content = response.xpath('//div[@class="listing_main_news"]')
        article_url = 'https://www.khaleejtimes.com' + content.xpath('.//h1//a//@href').get()
        title=content.xpath('.//h1//a//text()').get()
        yield(scrapy.Request(url=article_url, callback=self.parse_article, meta={'article_title': title, 'url': article_url}))
        
        content = response.xpath('//div[@class="liting_list"]')
        for article_link in content.xpath('.//h2'):
            article_url = 'https://www.khaleejtimes.com' +article_link.xpath('.//a//@href').get()
            title=article_link.xpath('.//text()').get()
            yield(scrapy.Request(url=article_url, callback=self.parse_article, meta={'article_title': title, 'url': article_url}))

    def parse_article(self, response):
        
        content = response.xpath('//div[@class="main_content_bg"]')
        title = response.meta['article_title'] 
        url = response.meta['url'] 
        text=  ''.join(content.xpath('.//div[contains(@class,"articlepage_content_zz")]//p//text()').extract()).strip()
        blurp = content.xpath('.//div[@class="articlepage_summary"]/h2//text()').get().strip()
        imgurl = content.xpath('.//div[@class="main_article_img_main"]//img//@src').get()
        date = response.xpath('//div[@class="author_detail"]').get()
        date = re.search('[A-Za-z]+ [0-9]+?, [0-9]{4}',date)[0]
        if date!='':
            date= datetime.datetime.strptime(date, "%B %d, %Y")
        else:
            date = datetime.datetime.today() 
            date = date.replace(day=1) 
        date  =datetime.datetime.strftime(date, "%d/%m/%Y")

        yield{
             'title': title,
             'imgurl': imgurl,
             'date': date,
             'blurp' : blurp,
             'url': url,
             'text': text,
             'category': 'technology',
             'source': self.name
         }

    
