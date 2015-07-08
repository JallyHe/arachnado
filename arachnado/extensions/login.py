import logging

import scrapy
from scrapy.http.request.form import _get_inputs, _get_form_url
import lxml.html
from scrapy.exceptions import NotConfigured
from formasaurus import FormExtractor


logger = logging.getLogger(__name__)

# Scrapy signals
login_credentials_changed = object()


class LoginFormRequest(scrapy.FormRequest):

    @classmethod
    def from_response(cls, response, formname=None, formnumber=0,
                      formdata=None, clickdata=None, dont_click=False,
                      formxpath=None, form=None, **kwargs):
        kwargs.setdefault('encoding', response.encoding)
        formdata = _get_inputs(form, formdata, dont_click, clickdata, response)
        url = _get_form_url(form, kwargs.pop('url', None))
        method = kwargs.pop('method', form.method)
        return cls(url=url, method=method, formdata=formdata, **kwargs)


class Login(object):

    def __init__(self, crawler):
        self.crawler = crawler
        if not crawler.settings.getbool('LOGIN_ENABLED'):
            raise NotConfigured
        crawler.signals.connect(self._login_credentials_changed,
                                signal=login_credentials_changed)
        self.ex = FormExtractor.load("./myextractor.joblib")

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request, response, spider):
        if 'login_pending' in spider.flags:
            return response
        if self._find_login_form(response):
            spider.flags.add('login_pending')
            spider.login_form_response = response
        return response

    def _find_login_form(self, response):
        tree = lxml.html.fromstring(response.body)
        for form_element, form_type in self.ex.extract_forms(tree):
            if form_type == 'l':
                return form_element

    def _login_credentials_changed(self, spider, username, password):
        if spider.login_form_response is None:
            return
        self._do_login(spider, username, password)

    def _do_login(self, spider, username, password):
        form_element = self._find_login_form(spider.login_form_response)
        if form_element is None:
            return
        text_inputs = form_element.xpath(
            './/input[not(@type) or @type="" or @type="text" '
            'or @type="password"]'
        )
        if len(text_inputs) != 2:
            return
        formdata = {}
        username_field = text_inputs[0].attrib.get('name')
        password_field = text_inputs[1].attrib.get('name')
        if not username_field or not password_field:
            return
        formdata[username_field] = username
        formdata[password_field] = password
        checkboxes = form_element.xpath(
            './/input[@type="checkbox"]'
        )
        for checkbox in checkboxes:
            checkbox_name = checkbox.attrib.get('name')
            if checkbox_name:
                formdata[checkbox_name] = 'on'
        login_request = LoginFormRequest.from_response(
            spider.login_form_response,
            formdata=formdata,
            form=form_element,
            priority=10 ** 9
        )
        self.crawler.engine.crawl(login_request, spider)
