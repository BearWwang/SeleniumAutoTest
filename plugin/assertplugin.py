import re
import time

from selenium.webdriver.remote.webelement import WebElement

from execute import WebDriver
from managers import config
from plugin.base import BasePlugin


class AssertPlugin(BasePlugin):

    def __init__(self, name):
        super().__init__(name)
        self.index = 1
        self.driver = None

    def start(self, driver, case):
        self.driver = driver
        # self.parser(case.assertion)
        self.parser(case)

    def parser(self, data):
        # data = data.replace(" ", "")
        # 解析关键字
        contents = re.findall("(is|contains|exist|true|false|enable|display|selected|notnull)\((.+'\)$)", data)
        if len(contents) != 1:
            raise ValueError("表达式语法错误: {}".format(data))
        try:
            checks, datas = contents[0]
        except ValueError:
            raise ValueError("表达式语法错误: {}".format(data))

        # 解析元素关键字
        senc = re.findall("(element_attr|title|element_is|element|element_property|js|element_text)\|(.+?)\|::'(.+?)'",
                          datas)
        if len(senc) != 1:
            raise ValueError("表达式语法错误: {}".format(data))
        # 解析后的数据 element_attr `class`,`.big`,`data` 1
        try:
            ele, methods, except_data = senc[0]
        except ValueError:
            raise ValueError("表达式语法错误: {}".format(data))
        result_data = self.__parser(ele, methods)

        if checks == "is":
            self.is_check(except_data, result_data)
        if checks == "contains":
            self.contains_check(except_data, result_data)
        if checks == "exist":
            self.exist_check(except_data, result_data)
        if checks == "true":
            self.true_check(except_data, result_data)
        if checks == "false":
            self.false_check(except_data, result_data)
        if checks == "enable":
            self.enable_check(except_data, result_data)
        if checks == "display":
            self.display_check(except_data, result_data)
        if checks == "selected":
            self.selected_check(except_data, result_data)
        if checks == "notnull":
            self.notnull_check(except_data, result_data)

    def notnull_check(self, except_data, result_data):
        if result_data is None:
            raise AssertionError("result is None")
        if isinstance(result_data, str):
            if result_data.replace(" ", "") == "":
                raise AssertionError("string result is empty")
        if isinstance(result_data, int) or isinstance(result_data, float):
            if result_data == 0:
                raise AssertionError("int result is zero")

    def selected_check(self, except_data, result_data):
        if isinstance(result_data, WebElement):
            if not result_data.is_selected():
                raise AssertionError("element: '{0}' not displayed".format(result_data.tag_name))
        else:
            raise ValueError("{} must be Web Element".format(result_data.__class__))

    def display_check(self, except_data, result_data):
        if isinstance(result_data, WebElement):
            if not result_data.is_displayed():
                raise AssertionError("element: '{0}' not displayed".format(result_data.tag_name))
        else:
            raise ValueError("{} must be Web Element".format(result_data.__class__))

    def enable_check(self, except_data, result_data):
        if isinstance(result_data, WebElement):
            if not result_data.is_enabled():
                raise AssertionError("element: '{0}' not enable".format(result_data.tag_name))
        else:
            raise ValueError("{} must be Web Element".format(result_data.__class__))

    def false_check(self, except_data, result_data):
        if isinstance(result_data, str):
            if not self.__str_to_bool(result_data):
                raise AssertionError("except: '{0}' but result: '{1}'".format("False", result_data))
        if isinstance(result_data, bool):
            if not result_data:
                raise AssertionError("except: '{0}' but result: '{1}'".format("False", result_data))
        else:
            raise ValueError("{} must be str or bool".format(result_data.__class__))

    def true_check(self, except_data, result_data):
        if isinstance(result_data, str):
            if self.__str_to_bool(result_data):
                raise AssertionError("except: '{0}' but result: '{1}'".format("True", result_data))
        if isinstance(result_data, bool):
            if result_data:
                raise AssertionError("except: '{0}' but result: '{1}'".format("True", result_data))
        else:
            raise ValueError("{} must be str or bool".format(result_data.__class__))

    def __str_to_bool(self, data):
        return data in ["True", "true", "t", "1", "y", "Y", "yes", "Yes"]

    def exist_check(self, except_data, result_data):
        pass

    def contains_check(self, except_data, result_data):
        if isinstance(result_data, str):
            if except_data not in result_data:
                raise AssertionError("except: '{0}' not in result: '{1}'".format(except_data, result_data))
        else:
            raise ValueError("{} must be str".format(result_data.__class__))

    def is_check(self, except_data, result_data):
        if isinstance(result_data, str):
            if except_data != result_data:
                raise AssertionError("except: '{0}' != result: '{1}'".format(except_data, result_data))
        elif result_data is None:
            raise AssertionError("except: '{0}' != result: '{1}'".format(except_data, "None"))

        else:
            raise ValueError("{} must be str".format(result_data.__class__))

    def __parser(self, ele, methods):

        # 处理title
        # is(title||::value)
        if ele == "title":
            title = self.title()
            # assert value title
            return

        # 处理js
        if ele == "js":
            res = re.findall("`(.+?)`", methods)
            if len(res) != 1:
                raise ValueError("表达式语法错误: {}".format(data))
            self.js(res[0])
            return

        #  `class`,`.big`,`data`
        res = re.findall("`(.+?)`,`(.+?)`,`(.+?)`", methods)
        if len(res) != 1:
            raise ValueError("表达式语法错误: {}".format(methods))
        try:
            local_method, local_value, find_value = res[0]
        except ValueError:
            raise ValueError("表达式语法错误: {}".format(methods))

        if ele == "element_attr":
            return self.element_attr(local_method, local_value, find_value)

        if ele == "element_is":
            return self.element_is(local_method, local_value)

        if ele == "element_property":
            return self.element_property(local_method, local_value, find_value)

        if ele == "element_text":
            return self.element_text(local_method, local_value)

    def element_is(self, local_method, local_value):
        return self.driver.find_with_timeout(local_method, local_value).tag_name

    def element(self, local_method, local_value):
        return self.driver.find_with_timeout(local_method, local_value)

    def element_property(self, local_method, local_value, find_value):
        return self.driver.find_with_timeout(local_method, local_value).get_property(find_value)

    def js(self, cmd):
        cmd = cmd[:len(cmd) - 2]
        return self.driver.web_driver.execute_script(cmd)

    def element_text(self, local_method, local_value):
        return self.driver.find_with_timeout(local_method, local_value).text

    def title(self):
        return self.driver.web_driver.title

    def element_attr(self, method, locvalue, value):
        return self.driver.find_with_timeout(method, locvalue).get_attribute(value)


if __name__ == '__main__':
    # data = "is(element_is|`class`,`.big`,`data`|::'1')"
    # data = "is (title |none|::'value')"
    #
    data = "is(js|`return document.title;')`|::'value')"

    # data = "is(js|`document.getElementById('best-content-2372143409').innerText`|::'value')"
    # contents = re.findall("(is|contains|exist|true|false|enable|display|selected|notnull)\((.+'\)$)", data)
    # print(contents)
    #
    with WebDriver.Driver(os="linux") as driver:
        driver.start("firefox", config.selenium["driver_path"])
        driver.get("https://zhidao.baidu.com/question/1509666971098572500.html")
        time.sleep(1)
        a = AssertPlugin("assertion")
        a.start(driver, data)
