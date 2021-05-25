import scrapy
from scrapy.http import Request
import json
import requests
from scrapy.http import Request
import datetime
from scrapy.http import TextResponse
import re

class TechCrunchSpider(scrapy.Spider):
    start_urls = ['https://techcrunch.com/']
    # allowed_domains =['https://techcrunch.com/']
    name = "techcrunch"
    download_delay = 5.0
    handle_httpstatus_list = [200]
    def parse(self,response):
        content = response.xpath('//div[@class="content"]')
        if len(content.xpath('.//header[@class = "post-block__header"]').extract()) >1:
            for article_link in content.xpath('.//header[@class = "post-block__header"]'):
                article_url=article_link.xpath('.//a//@href').get()
                title=article_link.xpath('.//a//text()').get().strip()
                date = article_link.xpath('.//time//@datetime').get()
                if date != '' or None:
                    date =date.split('T')[0]
                    date= datetime.datetime.strptime(date, "%Y-%m-%d")
                else:
                    date = datetime.datetime.today() 
                    date = date.replace(day=1) 
                date  =datetime.datetime.strftime(date, "%d/%m/%Y")
                yield(scrapy.Request(url=article_url, callback=self.parse_article, meta={'article_title': title, 'url': article_url,'date':date}))


    def parse_article(self, response):
        title = response.meta['article_title'] 
        url = response.meta['url'] 
        date = response.meta['date'] 
        article_body = response.xpath('//div[@class="article-content"]')
        blurp = ''.join(article_body.xpath('.//p[@id="speakable-summary"]/descendant-or-self::*[not(self::iframe)]//text()').extract())
        if blurp == None:
            blurp = ''.join(article_body.xpath('.//p[not(ancestor-or-self::iframe)]/text()').get())
        text = ''.join(article_body.xpath('.//p[not(ancestor-or-self::iframe)]/text()').extract())
        # text = re.sub('^\( function\(\) .*\}\)\(\)\;$','',text)
        # imgurl = response.xpath('//div[@class="article__featured-image-wrapper breakout"]//img//@src').get()
        
        imgurl = response.xpath('//div[contains(@class,"article__featured-image")]//img//@src').get()
        
        tags =  response.selector.xpath("//meta[@name='sailthru.tags']").extract()[0][36:-2]
        yield {
            'title': title,
            'imgurl': imgurl,
            'date': date,
            'blurp' : blurp,
            'url': url,
            'text': text,
            'tags': tags,
            'source': self.name,
            'category':None,
            'tags':None
        }

    
