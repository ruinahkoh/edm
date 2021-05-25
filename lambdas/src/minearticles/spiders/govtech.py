import re
import scrapy
from scrapy.http import Request
from w3lib.url import add_or_replace_parameters
import json
import requests
from scrapy.http import Request
import datetime
from scrapy.http import TextResponse


class GovtechSpider(scrapy.Spider):
    
    name = "govtech"
    download_delay = 5.0
    handle_httpstatus_list = [200]
    start_urls =['https://www.govtech.com/security/','https://www.govtech.com/biz/','https://www.govtech.com/products/','https://www.govtech.com/gov-experience/']
    def parse(self, response):
        category = response.request.url
        category = re.search('([^/]*)/$',category).group(1)
        content = response.xpath('//div[@class="feature-article"]')
        article_url = content.xpath('.//a//@href').get()
        title=content.xpath('.//h1//a//text()').get()
        yield(scrapy.Request(url=article_url, callback=self.parse_article, meta={'article_title': title, 'url': article_url,'category': category}))

        content = response.xpath('//div[@class="sub-feature-article"]')
        for article_link in content.xpath('.//h2//a'):
            article_url=article_link.xpath('.//@href').get()
            article_url = article_url.split('?')[0]
            title=article_link.xpath('.//text()').get()
            print(article_url)
            yield(scrapy.Request(url=article_url, callback=self.parse_article, meta={'article_title': title, 'url': article_url, 'category': category}))

    def parse_article(self, response):
        title = response.meta['article_title'] 
        url = response.meta['url'] 
        blurp = response.xpath('//p[@class="description"]//text()').get()
        text=  ''.join(response.xpath('//div[@id="article_body"]//p//text()').extract())
        imgurl = 'https:' + response.xpath('//div[@id="feature_image"]//amp-img//@src').get()
        category =    response.meta['category'] 
        date= response.xpath('//div//span[@class="date"]//text()').get().strip()   
        if date!='':
            date= datetime.datetime.strptime(date, "%B %d, %Y")
        else:
            date = datetime.datetime.today() 
            date = date.replace(day=1) 
        date  =datetime.datetime.strftime(date, "%d/%m/%Y")

        yield {
             'title': title,
             'imgurl': imgurl,
             'date': date,
             'blurp' : blurp,
             'url': url,
             'text': text,
             'category': category,
             'source': self.name
         }

    
