import scrapy


class MerchantpointItem(scrapy.Item):
    merchant_name = scrapy.Field()
    mcc = scrapy.Field()
    address = scrapy.Field()
    geo_coordinates = scrapy.Field()
    org_name = scrapy.Field()
    org_description = scrapy.Field()
    source_url = scrapy.Field()


class MerchantSpider(scrapy.Spider):
    name = "merchant"
    allowed_domains = ["merchantpoint.ru"]
    # Это я вручную нашел номера страниц с брендами у которых есть лого
    # (в sitemaps у меня в браузере было много пустых страниц, поэтому я сделал такой костыль) :)
    start_urls = [f"https://merchantpoint.ru/brands/{i}" for i in range(64, 485)]

    def parse(self, response, **kwargs):
        brand_row_list = response.xpath('//table[contains(@class, "table-striped")]//tr')

        if not brand_row_list:
            self.logger.debug(f'brand_row_list EMPTY {brand_row_list=}')
            return

        for brand_row in brand_row_list:
            brand_href = brand_row.xpath('.//td[2]//a/@href').get()
            if brand_href:
                brand_absolute_url = response.urljoin(brand_href)
                yield response.follow(brand_absolute_url, self.parse_merchant_points)

    def parse_merchant_points(self, response):
        merchant_point_href_to_xpath_list = response.xpath('//table[contains(@class, "table-striped")]//tr')

        if not merchant_point_href_to_xpath_list:
            self.logger.debug(f'EMPTY {merchant_point_href_to_xpath_list=}')
            return

        for merchant_point_href_to_xpath in merchant_point_href_to_xpath_list:
            merchant_point_href = merchant_point_href_to_xpath.xpath('.//td[2]//a/@href').get()
            if merchant_point_href:
                merchant_point_href_absolute_url = response.urljoin(merchant_point_href)
                yield response.follow(
                    merchant_point_href_absolute_url,
                    self.merchant_point_info,
                    meta={
                        'org_name': response.css('div.col-lg-12 h1::text').get(),
                        'org_description': response.xpath('(//div[@class="form-group mb-2"]/p)[2]/text()').get(),
                        'source_url': response.url,
                    })

    def merchant_point_info(self, response):
        item = MerchantpointItem()

        item['merchant_name'] = response.xpath('//p[b[text()="MerchantName"]]/text()').get()[3:]

        item['mcc'] = response.xpath('//p/a[starts-with(@href, "/mcc/")]/text()').get()

        address_optional = response.xpath('//p[b[text()="Адрес тороговой точки"]]/text()')
        if address_optional and address_optional.get():
            item['address'] = address_optional.get()

        geo_coordinates_optional = response.xpath('//p[b[text()="Геокоординаты"]]/text()')
        if geo_coordinates_optional and geo_coordinates_optional.get():
            item['geo_coordinates'] = geo_coordinates_optional.get()

        # meta
        item['org_name'] = response.meta['org_name']

        item['org_description'] = response.meta['org_description']

        item['source_url'] = response.meta['source_url']

        yield item
