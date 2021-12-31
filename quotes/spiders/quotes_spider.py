import csv

import scrapy


class BaseQuoteSpider(scrapy.Spider):
    start_urls = ['https://quotes.toscrape.com/']

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.csvfile = open(f'{self.name}.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.csvfile, fieldnames=self.field_names)
        self.writer.writeheader()

    def write_to_csv(self, quote_data):
        self.writer.writerow(quote_data)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.csvfile.close()


class QuoteSpider(BaseQuoteSpider):
    name = 'quotes'
    field_names = ['Text', 'Author', 'Tags']

    def parse(self, response, **kwargs):
        quotes = response.css('div.quote')
        for quote in quotes:
            quote_data = [
                f"{quote.css('span.text::text').get()}".strip(),
                f"{quote.css('small.author::text').get()}".strip(),
                str(', '.join(quote.css('a.tag::text').getall())).strip()
            ]
            quote_data = dict({k: v for k, v in zip(self.field_names, quote_data)})
            self.write_to_csv(quote_data)
        for next_page in response.css("li.next a::attr(href)"):
            yield response.follow(next_page, self.parse)


class AuthorSpider(BaseQuoteSpider):
    name = 'authors'
    field_names = ['Fullname', 'Born Date', 'Born Location', 'Description']

    def __init__(self, name=None, **kwargs):
        self.authors = set()
        super().__init__(name=name, **kwargs)

    def parse(self, response, **kwargs):
        for author in response.css(".author + a::attr(href)"):
            if author not in self.authors:
                self.authors.add(author)
                yield response.follow(author, self.parse_author_page)
        for next_page in response.css("li.next a::attr(href)"):
            yield response.follow(next_page, self.parse)

    def parse_author_page(self, response):
        author_data_list = [
            response.css("h3.author-title::text").get().strip(),
            response.css("span.author-born-date::text").get().strip(),
            response.css('span.author-born-location::text').get().strip(),
            response.css("div.author-description::text").get().strip()
        ]
        author_data_dict = dict({k: v for k, v in zip(self.field_names, author_data_list)})
        self.write_to_csv(author_data_dict)