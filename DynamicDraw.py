import json
import time
import datetime
import pymysql
import requests
import string

#程序开始设置
doc_id=int(input("请输入开始的doc_id:"))
delay=0.2
#全局设置
headers={
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"
}
invalid_keys = ['测试', 'vcf']

db = pymysql.connect("localhost", "root", "root", "database",charset='utf8')
cursor = db.cursor()

def connectDB():
    db = pymysql.connect("localhost", "root", "root", "database",charset='utf8')
	return db

def ConnectPing():
    global db
    global cursor
    try:
        db.ping()
    except:
        try:
            db.close()
            cursor.close()
        except:
            pass
        db = connectDB()
        cursor = db.cursor()

# 格式化打印模块
def printer(info, *args):
    at_now = int(time.time())
    time_arr = time.localtime(at_now)
    format_time = time.strftime("%Y-%m-%d %H:%M:%S", time_arr)
    # flag = "," if len(args) else " "
    content = f'[{format_time}] {info} {" ".join(f"{str(arg)}" for arg in args)}'
    print(content)

#获取抽奖详情
def Get_Lottery_Detail(doc_id):
    url=f"http://api.vc.bilibili.com//lottery_svr/v1/lottery_svr/lottery_notice?business_type=2&business_id={doc_id}"
    response=requests.get(url)
    try:
        response=response.json()
        response=response['data']
        first_prize_cmt=response['first_prize_cmt']
        second_prize_cmt=response['second_prize_cmt']
        third_prize_cmt=response['third_prize_cmt']
        first_prize_num=response['first_prize']
        second_prize_num=response['second_prize']
        third_prize_num=response['third_prize']
        lottery_time=response['lottery_time']
        return lottery_time, first_prize_cmt, first_prize_num, second_prize_cmt, second_prize_num, third_prize_cmt, third_prize_num
    except:
        pass

#判断描述内容
def JudgeDes(des):
    des=str(des)
    if des.find('点赞评论')!=-1 and (des.find('最多')!=-1 or des.find('最高')!=-1 or des.find('获得')!=-1):
        flag=True
    elif des.find('评论点赞')!=-1 and (des.find('最多')!=-1 or des.find('最高')!=-1 or des.find('获得')!=-1):
        flag=True
    elif des.find('点赞最多')!=-1:
        flag=True
    elif des.find('点赞最高')!=-1:
        flag=True
    elif des.find('点赞数')!=-1:
        flag=True
    elif des.find('点赞')!=-1 and des.find('获得')!=-1:
        flag=True
    elif des.find('评赞')!=-1 and des.find('获得')!=-1:
        flag=True
    elif des.find('评赞')!=-1 and des.find('获得')!=-1:
        flag=True
    else:
        flag=False
    return flag



#判断动态状态
def Get_doc_Detail(doc_id):
    url=f"https://api.vc.bilibili.com/link_draw/v1/doc/detail?doc_id={doc_id}"
    lottery_detail = {}
    name = 'Null'
    uid = '0'
    try:
        response=requests.get(url,timeout=2)
    except:
        title = "error"
        des = "error"
    else:
        try:
            response=response.json()
            if response['code']==0:
                lottery=(response['data']['item']['extension'])
                des=(response['data']['item']['description'])
                name=response['data']['user']['name']
                uid=response['data']['user']['uid']
                try:
                    lotterylen=len(str(lottery))
                except:
                    lotterylen=0
                if lotterylen>=3:
                    at_time=int(time.time())
                    lottery_detail=Get_Lottery_Detail(doc_id)
                    if at_time < lottery_detail[0]:
                        title = "互动抽奖"
                        for key in invalid_keys:
                            if key in des:
                                title = "该动态是钓鱼抽奖"
                                des = "该动态是钓鱼抽奖"
                    else:
                        title = "动态抽奖已过期"
                        des = "动态抽奖已过期"
                elif JudgeDes(des):
                    title="动态抽奖"
                    des=str(des)
                else:
                    title = "不符合规则的动态"
                    des = "不符合规则的动态"
            elif response['msg'] == "doc not found" and "time" in response['data'].keys():
                title = "该动态被删除"
                des = "该动态被删除"
            elif response['msg'] == "doc not found" and doc_id == response['data']['doc_id']:
                title = "该动态暂未发布"
                des = "该动态暂未发布"
            elif '投票' in response['data']['item']['description']:
                title = "该动态是投票"
                des = "该动态是投票"
            else:
                title = "error"
                des = "error"
        except:
            title = "动态抽奖信息获取失败"
            des = "动态抽奖信息获取失败"

    return title,des,lottery_detail,name,uid,des

# 轮询获取
def polling():
    now_doc_id = doc_id
    printer("当前起始轮询ID：",doc_id)
    flag = 3
    while True:
        printer("当前轮询ID：",now_doc_id)
        time.sleep(delay)
        try:
            data = Get_doc_Detail(now_doc_id)
            if flag==0:
                printer("错误次数过多,跳过",now_doc_id)
                flag = 3
            elif data[0] == "该动态暂未发布":
                printer("该动态暂未发布,休眠 30S 继续")
                flag -= 1
                time.sleep(30)
                continue
            elif data[0] == "该动态被删除":
                printer("该动态被删除", now_doc_id)
            elif data[0] == "该动态是投票":
                printer("该动态是投票", now_doc_id)
            elif data[0] == "不符合规则的动态":
                printer("不符合规则的动态", now_doc_id)
            elif data[0] == "error":
                flag -= 1
                printer("出现了异常情况", now_doc_id)
                printer(flag)
                continue
            elif data[0] == "互动抽奖":
                name=data[3]
                uid=data[4]
                description=data[5]
                lottery_time=data[2][0]
                lottery_time = time.localtime(lottery_time)
                lottery_time=time.strftime("%Y-%m-%d %H:%M:%S",lottery_time)
                printer("互动抽奖ID：",now_doc_id)
                printer("抽奖发起人",name,uid)
                printer("抽奖时间:",lottery_time)
                printer("一等奖",data[2][1],data[2][2])
                printer("二等奖",data[2][3],data[2][4])
                printer("三等奖",data[2][5],data[2][6])
                ConnectPing()
                sql = "insert into dynamicdraw(doc_id,name,uid,description,lottery_time,first_prize_cmt,first_prize_num,second_prize_cmt,second_prize_num,third_prize_cmt,third_prize_num,type) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cursor.execute(sql,(now_doc_id,name,uid,description,lottery_time,data[2][1],data[2][2],data[2][3],data[2][4],data[2][5],data[2][6],"互动抽奖"))
                db.commit()
                printer("插入互动抽奖信息至数据库",now_doc_id)
            elif data[0] == "动态抽奖":
                name = data[3]
                uid = data[4]
                description = data[5]
                printer("动态抽奖ID：", now_doc_id)
                printer("抽奖发起人", name, uid)
                printer("动态内容",description)
                ConnectPing()
                sql = "insert into dynamicdraw(doc_id,name,uid,description,type) values (%s,%s,%s,%s,%s)"
                cursor.execute(sql,(now_doc_id,name,uid,description,"动态抽奖"))
                db.commit()
                printer("插入动态抽奖信息至数据库", now_doc_id)
            elif data[0] == "动态抽奖信息获取失败":
                printer("动态抽奖信息获取失败",now_doc_id)
            else:
                printer("其他情况",data)
        except:
            printer("遇到异常",now_doc_id)
            flag -= 1
            continue
        now_doc_id = now_doc_id + 1

if __name__ == "__main__":
    polling()
