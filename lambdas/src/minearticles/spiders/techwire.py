# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime, date
import re

class TechwireAnalyticsSpider(scrapy.Spider):
    name = 'techwire'
    allowed_domains = ['www.techwireasia.com']
    start_urls = ['https://www.techwireasia.com']

    def parse(self, response):
        #top section
        
        content = response.xpath("//article[@role='article']")
        # print(content.extract())
        for article in content:
            try:
        #     print(article.get())
                title = article.xpath(".//a//@title").get()
                link = article.xpath(".//a//@href").get()
                date = article.xpath(".//p[@class ='byline']//text()").extract()
                if len(date)>1:
                    date =''.join(date).split('|')[1].strip()
                else:
                    date = date[0].strip()
                print(title,date)
                yield response.follow(url=link, callback=self.parse_article, dont_filter=True, meta={'article_title': title, 'url': link, 'date':date})
            except IndexError:
                pass
            
            

    def parse_article(self,response):
        title = response.request.meta['article_title']
        url = response.request.meta['url']
        article_date = response.request.meta['date']
        paragraphs = response.xpath("//div[contains(@class, 'large-7 medium-7 columns single-content')]/p")
        imgurl = response.xpath("//div[contains(@class, 'main-post-thumbnail')]//img/@src").get()
        

        
        try:
            article_date = datetime.strptime(article_date, "%d %B, %Y")
            article_date = datetime.strftime(article_date, "%d/%m/%Y")
        except IndexError:
            article_date = date.today()
            article_date = article_date.replace(day=1) 
            article_date = datetime.strftime(article_date, "%d/%m/%Y")
        text =''
        for para in paragraphs:
            current = para.xpath(".//text()").get()
            if current is not None: 
                text = text + current

        blurp = "".join(text.split('.')[:4])
        tags = response.xpath("//div[@class='tags-panel']//span//text()").extract()
        tags= ', '.join([tag.lower() for tag in tags])
        category =tags[0]
        yield {
             'title': title,
             'imgurl': imgurl,
             'date': article_date,
             'blurp' : blurp,
             'url': url,
             'text': text,
             'category': category,
             'tags':tags,
             'source': self.name
         }