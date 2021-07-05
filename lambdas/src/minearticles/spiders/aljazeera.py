# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime, date
import re
from newspaper import Article

class AljazeeraSpider(scrapy.Spider):
    name = 'aljazeera'
    allowed_domains = ['https://www.aljazeera.com/']
    start_urls = ['https://www.aljazeera.com/tag/technology/','https://www.aljazeera.com/tag/Cybersecurity/','https://www.aljazeera.com/tag/Crypto/']

    def parse(self, response):
        #top article
        content = response.xpath('//div[@class="gc__content"]')
        category = response.request.url
        category = re.search('([^/]*)/$',category).group(1)
        for article in content:
            url = 'https://www.aljazeera.com'+article.xpath('.//a//@href').get()
            title = article.xpath('.//a//span//text()').get()
            blurp = article.xpath('.//div[@class="gc__excerpt"]//p//text()').get()
            yield response.follow(url=url, callback=self.parse_article, dont_filter=True, meta={'article_title': title, 'url': url , 'blurp': blurp,'category':category})
  

    


    def parse_article(self,response):
        title = response.request.meta['article_title']
        url = response.request.meta['url']
        blurp = response.request.meta['blurp']
        category = response.request.meta['category']

        def get_key_word(url):
            key_words =[]
            article = Article(url)
            article.download()

            article.html
            article.parse()
            article.nlp()

            return article.text, article.publish_date, article.top_image  
            
        text, article_date, imgurl = get_key_word(url)
        
        try:
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
             'source': self.name,
             'tags':None
         }