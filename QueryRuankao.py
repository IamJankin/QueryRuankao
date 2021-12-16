from urllib import request,parse
from http import cookiejar
import time
import requests
import BaiduOCR
import sendMail
import itertools
import json
import os
from bs4 import BeautifulSoup
import configparser

#configparser初始化
dirname = os.path.split(os.path.realpath(__file__))[0]      # python文件的绝对路径
config = configparser.ConfigParser()
config.read(dirname + "/config.ini", encoding="utf-8")

url = 'https://query.ruankao.org.cn/score'
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Referer':'https://query.ruankao.org.cn/score'
}

# cookiejar
cookie = cookiejar.CookieJar()
handler = request.HTTPCookieProcessor(cookie)
opener = request.build_opener(handler)

def detect(KSSJ):
    res = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(res.text, 'lxml')
    data = soup.find(name='li', attrs={'data-value': KSSJ})
    if data:
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        info = '[+] 软考可以查成绩了:' + data.string + '\n' + now_time
        sendMail.sendMail('[软考]查成绩啦！',info)
        print(info)
        print('-'*100)
        return True
    else:
        print('[*] 成绩还没出！')
        return False

def getCookie():            # 访问成绩查询页面，获取Cookie
    req = request.Request(url=url,method='GET',headers=headers)
    opener.open(req)

def getCaptchaIMG():        # 保存验证码到本地
    captcha_url = 'https://query.ruankao.org.cn//score/captcha?'
    captcha_url += str(int(time.time()*1000))
    req = request.Request(url=captcha_url,method='GET',headers=headers)
    res = opener.open(req)
    with open(dirname + '/captcha.png','wb') as f:
        f.write(res.read())

def VerifyCaptcha(captcha):     # 判断验证码是否正确
    varify_url = 'https://query.ruankao.org.cn//score/VerifyCaptcha'
    params = {'captcha':captcha}
    # print(parse.urlencode(params))
    req = request.Request(url=varify_url,data=parse.urlencode(params).encode(encoding='UTF-8'),method='POST',headers=headers)
    res = opener.open(req)
    html = res.read().decode('utf-8')
    flag = json.loads(html)['flag']     #1或0
    return flag

def getCaptcha():
    try:
        captcha = BaiduOCR.getCaptcha()
        print('[*] OCR识别结果：%s'%captcha)
        if len(captcha) == 4:
            captcha_data = list(itertools.permutations(captcha, 4))
            print('[*] 共生成%d种验证码排列，正在判断正确验证码...'%len(captcha_data))
            flag = 0
            for i in range(len(captcha_data)):
                captcha_data[i] = captcha_data[i][0] + captcha_data[i][1] + captcha_data[i][2] + captcha_data[i][3]
                '''VerifyCaptcha'''
                flag = VerifyCaptcha(captcha_data[i])
                if flag:
                    captcha = captcha_data[i]
                    print('[+] 正确验证码：%s'%captcha)
                    return captcha
            if flag == 0:
                print('[*] OCR验证码无正确排列，正在重新获取验证码。')
                time.sleep(1)
                getCaptchaIMG()
                return getCaptcha()
        else:
            print('[*] OCR验证码识别位数不对，正在重新获取验证码。')
            time.sleep(1)
            getCaptchaIMG()
            return getCaptcha()
    except:
        print('[-] 百度识别出错,正在重新识别')
        time.sleep(1)
        return getCaptcha()

def QueryScore(XM,ZJHM,KSSJ):
    getCookie()         #生成Cookie
    getCaptchaIMG()     #从软考上保存验证码图片
    captcha = getCaptcha()  #使用百度API识别验证码
    # captcha = input('请输入验证码：')  #手动输入验证码
    '''查询成绩'''
    result_url = 'https://query.ruankao.org.cn//score/result'
    select_type = config.getint('data','select_type')
    params = {
        'stage':KSSJ,
        'xm':XM,
        'zjhm':ZJHM,
        'jym':captcha,
        'select_type':select_type
    }
    req = request.Request(url=result_url,data=parse.urlencode(params).encode(encoding='UTF-8'),method='POST',headers=headers)
    res = opener.open(req)
    html = res.read().decode('utf-8')
    data = json.loads(html)
    if data['flag']:
        '''输出成绩'''
        print('-'*100)
        print('考试时间：%s'%data['data']['KSSJ'])
        print('资格名称：%s'%data['data']['ZGMC'])
        print('准考证号：%s'%data['data']['ZKZH'])
        print('证件号：%s'%data['data']['ZJH'])
        print('姓名：%s'%data['data']['XM'])
        print('上午成绩：%s'%data['data']['SWCJ'])
        print('下午成绩：%s'%data['data']['XWCJ'])
        if data['data']['LWCJ'] != '-': print('论文成绩：%s'%data['data']['LWCJ'])
        print('-'*100)

        '''邮件正文'''
        info = '姓名：%s\n资格名称：%s\n考试时间：%s\n上午成绩：%s\n下午成绩：%s\n'%(data['data']['XM'], data['data']['ZGMC'], data['data']['KSSJ'], data['data']['SWCJ'], data['data']['XWCJ'])
        if data['data']['LWCJ'] != '-': info += '论文成绩%s\n' % data['data']['LWCJ']

        '''发送成绩'''
        if data['data']['LWCJ'] == '-':
            if float(data['data']['SWCJ'])>=45 and float(data['data']['SWCJ'])>=45:
                print('[+] 恭喜您，通过考试了！')
                info += '恭喜您，通过考试了！\n'
                sendMail.sendMail('[软考]通过考试',info)
            else:
                print('[-] 很遗憾，这次没有通过考试，请继续加油！')
                info += '很遗憾，这次没有通过考试，请继续加油！\n'
                sendMail.sendMail('[软考]就差一点点了',info)
        else:
            if float(data['data']['SWCJ']) >= 45 and float(data['data']['SWCJ']) >= 45 and float(data['data']['LWCJ']) >= 45:
                print('[+] 恭喜您，通过考试了！')
                info += '恭喜您，通过考试了！\n'
                sendMail.sendMail('[软考]通过考试', info)
            else:
                print('[-] 很遗憾，这次没有通过考试，请继续加油！')
                info += '很遗憾，这次没有通过考试，请继续加油！\n'
                sendMail.sendMail('[软考]就差一点点了', info)

    else:
        print('[*] 查询结果：'+data['msg']+'(请检查信息是否正确)')
        sendMail.sendMail('[软考]%s'%data['msg'], data['msg']+'(请检查信息是否正确)')

    # 查询结束，将考试时间保存到文件，用于防止重复查询。
    with open(dirname + '/QueryResult.txt','w') as f:
        f.write(KSSJ)

def main():
    # 读取信息
    XM = config.get('data', 'XM')
    ZJHM = config.get('data', "ZJHM")
    KSSJ = config.get('data', 'KSSJ')

    # 检测是否已经查完，防止重复查询
    Repeat_query = config.getboolean('data','Repeat_query')
    if Repeat_query == False:
        if os.path.isfile(dirname + '/QueryResult.txt'):
            with open(dirname + '/QueryResult.txt','r') as f:
                QueryResult = f.read()
            if QueryResult == KSSJ:
                print('[*] 已查询出结果，不再重复查询。')
                print('[*] 如果需要再次查询，请将Repeat_query配置为true。')
                exit()

    #检测是否出成绩
    if detect(KSSJ):
        QueryScore(XM,ZJHM,KSSJ)

if __name__ == '__main__':
    main()