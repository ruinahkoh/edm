# -*- coding: utf-8 -*-
import scrapy
import logging
from datetime import datetime, date
import re

class CioSpider(scrapy.Spider):
    name = 'cio'
    allowed_domains = ['www.cio.com']
    start_urls = ['https://www.cio.com/asean/category/analytics','https://www.cio.com/asean/category/cloud-computing','https://www.cio.com/asean/']
    

    def parse(self, response):
        if response.request.url in ['https://www.cio.com/asean/category/analytics/','https://www.cio.com/asean/category/cloud-computing/']:
            articles = response.xpath("//div[@class='main-col']/div")

            category = response.request.url
            category = re.search('([^/]*)/$',category).group(1)
            for article in articles[:2]:
                blurp = None # The 2 topmost articles has no blurp
                title = article.xpath(".//div/h3/a/text()").get()
                link = article.xpath(".//div/h3/a/@href").get()
                article_url = f"https://www.cio.com{link}"
                if 'video' not in link:            
                    yield response.follow(url=link, callback=self.parse_article, meta={'article_title': title, 'url': article_url, 'blurp': blurp, 'category':category})
            
            for article in articles[3:]:
                title = article.xpath(".//div/h3/a/text()").get()
                link = article.xpath(".//div/h3/a/@href").get()
                blurp = article.xpath(".//div/h4/text()").get()
                article_url = f"https://www.cio.com{link}"
                if 'video' not in link:            
                    yield response.follow(url=link, callback=self.parse_article, meta={'article_title': title, 'url': article_url, 'blurp': blurp,'category':category})

            # get next page at the moment, doing 1 hop by specify start=40
            # next_page = response.xpath("//a[@id='load-more-index']/@href").get()
            
            # if next_page and next_page != '?start=40':
            #     if category == 'analytics':
            #         full_url = f"https://www.cio.com/asean/category/analytics/{next_page}"
            #     else:
            #         full_url = f"https://www.cio.com/asean/category/cloud-computing/{next_page}"
            #     yield scrapy.Request(url=full_url, callback = self.parse)

        #scrape from main asean page
        else:
            category = response.request.url
            print(response.request.url)
            category = re.search('([^/]*)/$',category).group(1)
            contents = response.xpath('//div[@class="post-cont"]')
            for content in contents:
                link = content.xpath('.//h3//a//@href').get()
                if 'video' not in link:
                    title= content.xpath('.//h3//a//text()').get()
                    blurp =content.xpath('.//h4//text()').get()
                    article_url = f"https://www.cio.com{link}" 
                    yield response.follow(url=link, callback=self.parse_article, meta={'article_title': title, 'url': article_url, 'blurp': blurp, 'category':category})

        
    def parse_article(self,response):
        title = response.request.meta['article_title']
        url = response.request.meta['url']
        paragraphs = response.xpath("//div[@itemprop='articleBody']/p")
        blurp = response.request.meta['blurp']
        category = response.request.meta['category']
        #img = response.xpath("//div[@class='col-sm-9 post-content-col']/img/@src").get()
        imgurl = response.xpath(".//img/@data-original").get()
        tags = response.selector.xpath("//meta[@itemprop='keywords']//@content").get()
        if type(tags) == list:
            tags = ', '.join(tags)
        

        text =''
        try:
            for para in paragraphs:
                text = text + para.xpath(".//text()").get()
        except:
            pass
        
        if blurp is None:
            blurp =response.xpath('//h3[@itemprop="description"]//text()').get()
                 
        date= response.xpath('//span[@class="pub-date"]//@content').get()
        try:
            date =date.split('T')[0]
            date= datetime.strptime(date, "%Y-%m-%d")
        except:
            date = datetime.today() 
            date = date.replace(day=1) 
        date  =datetime.strftime(date, "%d/%m/%Y")

        yield {
             'title': title,
             'imgurl': imgurl,
             'date': date,
             'blurp' : blurp,
             'url': url,
             'text': text,
             'category': category,
             'tags':tags,
             'source': self.name
         }
