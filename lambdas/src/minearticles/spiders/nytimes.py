# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime, date
import re
from newspaper import Article

class NytimesSpider(scrapy.Spider):
    name = 'nytimes'
    allowed_domains = ['https://www.nytimes.com']
    start_urls = ['https://www.nytimes.com/section/technology']

    def parse(self, response):
        #top article
        content = response.xpath('//h2[@class="css-4tvmog eecsw3u0"]')
        url = 'https://www.nytimes.com'+content.xpath('.//a//@href').get()
        title = content.xpath('.//a//text()').get()
        blurp = content.xpath('.//p[@class="css-1jhf0lz eecsw3u1"]//text()').get()
        yield response.follow(url=url, callback=self.parse_article, dont_filter=True, meta={'article_title': title, 'url': url , 'blurp': blurp})
        #for the top section
        content = response.xpath('//article[@class="css-imuvyx"]')
        for article in content:
            url = 'https://www.nytimes.com'+article.xpath('.//a//@href').get()
            title = article.xpath('.//a//text()').get()
            blurp = article.xpath('.//p[@class="css-1jhf0lz eecsw3u3"]//text()').get()
            # blurp = article.xpath('.//p//text()').get()
            yield response.follow(url=url, callback=self.parse_article, dont_filter=True, meta={'article_title': title, 'url': url , 'blurp': blurp})
        #for the bottom section
        content = response.xpath('//li[@class ="css-ye6x8s"]')
        for article in content:
            url = 'https://www.nytimes.com'+article.xpath('.//a//@href').get()
            title = article.xpath('.//h2//text()').get()
            blurp = article.xpath('.//p//text()').get()
            yield response.follow(url=url, callback=self.parse_article, dont_filter=True, meta={'article_title': title, 'url': url , 'blurp': blurp})

    


    def parse_article(self,response):
        title = response.request.meta['article_title']
        url = response.request.meta['url']
        blurp = response.request.meta['blurp']
        category = response.xpath('//span[@class="css-17xtcya"]//a//@href').get()+'/'
        category = re.search('([^/]*)/$',category).group(1).strip()


        def get_key_word(url):
            key_words =[]
            article = Article(url)
            article.download()

            article.html
            article.parse()
            article.nlp()

            return article.text, article.publish_date, article.top_image ,article.summary 
            
        text, article_date, imgurl ,blurp1= get_key_word(url)
        if blurp == None:
            blurp =blurp1
        try:
            article_date = datetime.strftime(article_date, "%d/%m/%Y")
        except IndexError:
            article_date = date.today().replace(day=1) 
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