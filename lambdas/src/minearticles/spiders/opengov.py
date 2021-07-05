# -*- coding: utf-8 -*-
import scrapy
import re
from datetime import datetime, date


class OpengovAugmentedintelligenceSpider(scrapy.Spider):
    name = 'opengov'
    allowed_domains = ['www.opengovasia.com']
    start_urls = ['https://www.opengovasia.com']
    #     'https://www.opengovasia.com/augmented-intelligence','https://www.opengovasia.com/big-data','https://www.opengovasia.com/cloud',
    # 'https://www.opengovasia.com/critical-event-management','http://www.opengovasia.com/cyber-resilience','https://www.opengovasia.com/digital-economy',
    # 'http://www.opengovasia.com/digital-transformation','http://www.opengovasia.com/education','https://www.opengovasia.com/fsi-fintech',
    # 'https://www.opengovasia.com/healthcare','https://www.opengovasia.com/iot','https://www.opengovasia.com/mobility','https://www.opengovasia.com/open-data',
    # 'https://www.opengovasia.com/public-safety','https://www.opengovasia.com/smart-cities','https://www.opengovasia.com/urban-tech',
    # 'https://opengovasia.com/digital-government']
    
 
    def parse(self, response):
        
        #response.xpath("//h2[@class='elementor-heading-title elementor-size-default']//span//text()").get()
        articles = response.xpath("//div[@class='elementor-post__text']")
        otherarticles = response.xpath("//h1[@class='elementor-heading-title elementor-size-default']")
        
        for article in articles:
            title = article.xpath(".//h3/a/text()").get().lstrip()
            link = article.xpath(".//h3/a/@href").get()
            link = link.replace("http://","https://")
            yield response.follow(url=link, callback=self.parse_article, meta={'article_title': title, 'url': link})

        for article in otherarticles:
            title = article.xpath(".//a/text()").get().lstrip()
            link = article.xpath(".//a/@href").get()
            link = link.replace("http://","https://")
            yield response.follow(url=link, callback=self.parse_article, meta={'article_title': title, 'url': link}, dont_filter=True)


    def parse_article(self,response):
        title = response.request.meta['article_title']
        url = response.request.meta['url']
        category =response.selector.xpath('//meta[@property="article:section"]/@content').get()
        paragraphs = response.xpath("//div[contains(@class, 'theme-post-content')]/div/p")
        imgurl = response.xpath("//div[contains(@class, 'theme-post-content')]/preceding-sibling::div[contains(@class,'image')]/div//img/@src").get()
        article_date = response.xpath("//span[contains(@class,'item--type-date')]/text()").get()

        try:       
            regex = re.compile(r'[\n\t,]')
            article_date = regex.sub("", article_date)
            article_date = article_date.lstrip()
            article_date = datetime.strptime(article_date, '%B %d %Y')
        except:
            article_date = datetime.today() 
            article_date = article_date.replace(day=1) 

        article_date =datetime.strftime(article_date, "%d/%m/%Y")

       

        text =''
        for para in paragraphs:
            current = para.xpath(".//text()").get()
            if current is not None:
                text = text + current
        
        blurp = "".join(text.split(".")[:4])

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