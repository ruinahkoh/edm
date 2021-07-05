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
        try:
            date =date.split('T')[0]
            date= datetime.datetime.strptime(date, "%Y-%m-%d")
        except:
            date = datetime.datetime.today() 
            date = date.replace(day=1) 
        date  =datetime.datetime.strftime(date, "%d/%m/%Y")
        

        #get the blurp
        blurp = request.xpath('//h3[@itemprop="description"]//text()').get()
        text = ''.join(request.xpath('//div[@itemprop="articleBody"]/descendant::text()').extract()).strip()
        text = re.sub('\[.*\]', '',text)
        tags = ', '.join(request.xpath('//span[@class="primary-cat-name2"]//text()').extract()).lower()
        
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




   
