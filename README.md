## edm project
Building an article recommender system on AWS 

### Part 1: Scraping articles from relevant websites 

### Scrapy
Scrapy is a fast high-level web crawling and web scraping framework, used to crawl websites and extract structured data from their pages. It can be used for a wide range of purposes, from data mining to monitoring and automated testing.

Spiders can be found at https://github.com/ruinahkoh/edm/tree/main/lambdas/src/minearticles

### Part 2: Respository 
Codecommit was used as a repository for the code. Similar to Github, it allows git actions and allows users to work on the code and push new changes to the repository

### Part 3: AWS Lambda/Step Functions
AWS Lambda was used to run the spiders for it to crawl the web for the articles. Step Functions helped to run the spiders in parallel to overcome the 15 min constraint of AWS lambda. Lambda is used to extract keywords from articles to obtain the trending keywords which will in turn be used to query the elasticsearch.
Lambda functions
1) Crawler Lambda
2) Keyword Extraction lambda
3) Elasticsearch lambda

### Part 4: Storage
AWS S3 was initially used as a storage. However, to facilitate better query of the data in the future, we switched to dynamodb which can work together with elastic search

### Part 5: AWS CICD Pipeline
To ensure that changes made to the code in Codecommit will update the lambda functions and Step functions, codepipeline was used. Using Serverless Application Model, this allows us to deploy resources using a template, for example each time there is a new push to the respositor, new lambda functions and step functions will be deployed using the CICD pipeline.

### Part 6: ElasticSearch
Each time the dyanamodb is refreshed the elasticsearch will update its index. Elasticsearch is used to query the data and output articles with the highest score for the trending keyword


