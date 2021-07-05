# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime, date
import re
from newspaper import Article


class GuardianSpider(scrapy.Spider):
    name = 'guardian'
    allowed_domains = ['www.theguardian.com/technology','https://www.theguardian.com/uk/technology']
    start_urls = ['https://www.theguardian.com/technology/all', 'https://www.theguardian.com/uk/technology'] #internationala and uk specific site

    def parse(self, response):
        if 'uk/technology' in response.request.url:
            for article in response.xpath('//div[@class="fc-item__container"]//a'):
                url = article.xpath('.//@href').get()
                if re.search('technology', url) and  ('/video/' not in url and '/gallery/' not in url): #remove videos and galleries
                    yield response.follow(url=url, callback=self.parse_article, meta={ 'url': url })
        else:
            articles = response.xpath('//div[@class="u-cf index-page"]')
            for article in articles.xpath('//h3[@class="fc-item__title"]//a'):
                url = article.xpath('.//@href').get()
                yield response.follow(url=url, callback=self.parse_article, meta={ 'url': url })

        
    


    def parse_article(self,response):
       
        url = response.request.meta['url']

        #many versions of blurp
        blurp =response.xpath('//div[@class="dcr-mj1r7n"]//text()').get()
        if blurp is None:
            blurp =response.xpath('//div[@class="dcr-1wzmzme"]//p//text()').get()
            if blurp is None:
                blurp =response.xpath('//div[@class="dcr-zcv58i"]//p//text()').get()
            


        tags =response.xpath('//ul[@class="dcr-1r2wmvc"]//a//text()').extract()
        category = response.xpath('//li[@class="dcr-18or3t6"]//a//text()').get()
        tags.append(category)
        tags =', '.join(tags).lower()
        def get_key_word(url):
            article = Article(url)
            article.download()

            article.html
            article.parse()
            article.nlp()

            return article.text, article.publish_date, article.top_image ,article.title
            
        text, article_date, imgurl ,title= get_key_word(url)

        #remove reviews and products 
        if re.search('review', title) or re.search('best',title.lower()):
            pass 
        else:
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
                'tags':tags.lower(),
                'source': self.name
            }