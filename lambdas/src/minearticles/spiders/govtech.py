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
    start_urls =['https://www.govtech.com/security','https://www.govtech.com/biz','https://www.govtech.com/products','https://www.govtech.com/gov-experience']
    def parse(self, response):

        category = response.request.url
        category = re.search('([^/]*)$',category).group(1)
        content = response.xpath('//div[@class="ListA-items"]')
        for article in content:
            for art in article.xpath('//div[@class="ListA-items-item"]'):
                print(art)
                if art.xpath('//div[@class="PromoC"]'):
                    article_url = art.xpath('.//div[@class="Promo-title"]//a/@href').get()
                    title=art.xpath('.//div[@class="Promo-title"]//a//text()').get()
                    yield(scrapy.Request(url=article_url, callback=self.parse_article, meta={'article_title': title, 'url': article_url,'category': category}))
                elif art.xpath('//div[@class="PromoB"]'):
                    article_url = art.xpath('.//div[@class="Promo-title"]//a/@href').get()
                    title=art.xpath('.//div[@class="Promo-title"]//a//text()').get()
                    yield(scrapy.Request(url=article_url, callback=self.parse_article, meta={'article_title': title, 'url': article_url,'category': category}))

        
    def parse_article(self, response):
        title = response.meta['article_title'] 
        url = response.meta['url'] 
        blurp = response.xpath('//h2[@class="Page-subHeadline"]//text()').get()
        text=  response.xpath('//div[@class="Page-articleBody RichTextBody"]//text()').extract()
        text = ''.join([sent.strip() for sent in text])
        imgurl =  response.xpath('//img[@class="Image"]//@srcset').get()
        category =    response.meta['category'] 
        tags = ', '.join(response.xpath('//div[@class="Page-tags"]//a//text()').extract())
        date= response.xpath('//div[@class="Page-datePublished"]//text()').get().strip()
        date =re.sub("[^0-9a-zA-Z, ]","", date).strip()
        try:
            date= datetime.datetime.strptime(date, "%B %d, %Y")
        except:
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
             'source': self.name,
             'tags':tags.lower()
         }

    
