# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime, date
import re

class GovinsiderSpider(scrapy.Spider):
    name = 'govinsider'
    allowed_domains = ['govinsider.asia']
    start_urls = ['https://www.govinsider.asia/']
    #     'https://www.govinsider.asia/connected-gov','https://www.govinsider.asia/data','https://www.govinsider.asia/digital-gov'
    # ,'https://www.govinsider.asia/health','https://www.govinsider.asia/inclusive-gov','https://www.govinsider.asia/security','https://www.govinsider.asia/digital-economy'
    # ,'https://www.govinsider.asia/future-of-work','https://govinsider.asia/citizen-centric','https://www.govinsider.asia/intelligent-gov','https://govinsider.asia/insights'
    # ,'https://www.govinsider.asia/smart-gov','https://www.govinsider.asia/transformation']
    # next_page = 2

    def parse(self, response): 
        articles = response.xpath("//h2[contains(@class,'entry-title')]")
        for article in articles:
            title = article.xpath(".//a/text()").get()
            link = article.xpath(".//a/@href").get()
            print(link)
            article_url = f"https://govinsider.asia{link}"
            blurp = article.xpath(".//parent::div/div[contains(@class,'entry-summary')]/p/text()").get()
            # category = article.xpath(".//parent::div/div[@class ='categories']/a/text()").get().strip()
            yield response.follow(url=link, callback=self.parse_article, meta={'article_title': title, 'url': article_url, 'blurp': blurp})
           


        # # get next page, currently stop at second page
        
        # if self.next_page <= 2:
        #     full_url = f"https://govinsider.asia/smart-gov/page/{self.next_page}/"
        #     self.next_page += 1
        #     yield scrapy.Request(url=full_url, callback = self.parse)

            
    def parse_article(self,response):
            title = response.request.meta['article_title']
            url = response.request.meta['url']
            blurp = response.request.meta['blurp']
            # category = response.request.meta['category']
            imgurl = response.selector.xpath('//meta[@property="og:image"]/@content').get()
            category =  response.xpath("//div[@class='post-meta']/a/text()")
            if category:
                category = category.get().strip()
            else:
                pass
            paragraphs = response.xpath("//div[@class='entry-content post-content']/p")
            text =''
            
            for para in paragraphs:
                para_text = para.xpath(".//text()").get()
                        
                if para_text is not None:
                    text = text + para_text
                        
            article_date = response.xpath("//time[@class='updated']/text()").get()
            try:
                article_date = datetime.strptime(article_date, '%d %b %Y')
                article_date = datetime.strftime(article_date, "%d/%m/%Y")
            except:
                article_date = date.today()
                article_date =datetime.strftime(article_date, "%d/%m/%Y")
            if blurp is None and len(text) > 50:
                blurp = "".join(text.split('.')[:4])

            yield {
                'title': title,
                'imgurl': imgurl,
                'date': article_date, 
                'blurp' : blurp,
                'url': url,
                'text': text,
                'category':category,
                'source': self.name,
                'tags':None
            }