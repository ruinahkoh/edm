# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime, date
import re
from newspaper import Article

class ApnewsSpider(scrapy.Spider):
    name = 'apnews'
    allowed_domains = ['https://www.apnews.com']
    start_urls = ['https://apnews.com/hub/technology/']

    def parse(self, response):
        #top article
        content = response.xpath('//div[@data-key="feed-card-wire-story-with-image"]')
        category = response.request.url
        category = re.search('([^/]*)/$',category).group(1)
        for article in content:
            url = 'https://apnews.com' +article.xpath('.//@href').get()
            title = article.xpath('.//h1[@class="Component-h1-0-2-42"]//text()').get()
            blurp =article.xpath('.//p//text()').get()
            date =article.xpath('.//span//@data-source').get().split('T')[0]
            yield response.follow(url=url, callback=self.parse_article, dont_filter=True, meta={'article_title': title, 'url': url , 'blurp': blurp, 'article_date':date, 'category': category})
       


    def parse_article(self,response):
        title = response.request.meta['article_title']
        url = response.request.meta['url']
        blurp = response.request.meta['blurp']
        category = response.request.meta['category']
        article_date = response.request.meta['article_date']
        
        imgurl =response.selector.xpath("//meta[contains(@property,'url')]//@content").get()
            
        text =''.join(response.xpath('//div[@data-key="article"]//p//text()').extract()).strip()
        
        try:
            article_date = datetime.strptime(article_date, "%Y-%m-%d")
            article_date = datetime.strftime(article_date, "%d/%m/%Y")
        except IndexError:
            article_date = date.today()
            article_date = datetime.strftime(article_date, "%d/%m/%Y")
        

        

        yield {
             'title': title,
             'imgurl': imgurl,
             'date': article_date,
             'blurp' : blurp,
             'url': url,
             'text': text,
             'category': category,
             'source': self.name
         }