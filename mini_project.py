'''
Created on 2020. 6. 22.

@author: hangaramit07
'''
import os
import json
from sqlalchemy import create_engine
from flask import Blueprint, Flask, url_for, render_template, request, redirect, session, jsonify, make_response, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import time
from sqlalchemy.sql.expression import desc
from werkzeug.utils import secure_filename, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import urllib #urllib.request

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mini_project.db'
db = SQLAlchemy(app)

class User(db.Model):   
    __tablename__ = 'users' #테이블이름

    num = db.Column(db.Integer) #회원수
    id = db.Column(db.String, primary_key = True)   #유저 아이디 
    password = db.Column(db.String) # 유저 비밀번호
    passwordcheck=db.Column(db.String) #유저 비밀번호 다시 입력
    name = db.Column(db.String) #유저 이름(실명)
    phone = db.Column(db.String) #유저 핸드폰번호

    def __init__(self, id, password, passwordcheck, name, phone):
        self.id = id
        self.password = password
        self.passwordcheck = passwordcheck
        self.name = name
        self.phone = phone
   
    def __repr__(self):
        return"<User('%s', '%s', %s, %s, '%s')>" % (self.id, self.password, self.passwordcheck, self.name, self.phone)
    
def format_datetime(timestamp):
    """날짜 시간 포맷 형식 변경해서 문자열로 반환하는 함수"""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')


@app.route("/")
def home():
    return render_template("index.html")
@app.route("/signin",methods=['GET','POST'])
def login():
    if request.method=='GET':
        return render_template("signin.html")
    else:
        uid = request.form['userid']
        upasswd = request.form['password']
        user_data=User.query.filter_by(id=uid, password=upasswd).first()
        if user_data is not None :
            session['user_num']=user_data.num
            session['userid'] = user_data.id
            session['username'] = user_data.name
            session['phone'] = user_data.phone
            session['logged_in']=True #유저가 입력한 아이디와 비밀번호가 DB에 저장되있는 아이디와 비밀번호와 일치하면 로그인상태로 전환
            return redirect(url_for('home'))
            
        else:
            return render_template("message.html")   
                    
    
@app.route("/register",methods=['GET','POST'])
def register():
    if request.method=='POST':
        new_user=User(id=request.form['userid'],
            name=request.form['username'],
            password=request.form['password'],
            passwordcheck=request.form['passwordcheck'],
            phone=request.form['phone'])
        db.session.add(new_user)
        db.session.commit()
        return render_template("signin.html")
       
    else:
        return render_template("register.html")    
    
@app.route("/logout")
def logout():
    session['logged_in']=False #로그아웃하면 로그인상태 해제
    session['user_num']=None #저장하고 있던 유저 번호 초기화
    return redirect(url_for('home'))    


@app.route("/unjoin")
def unjoin():
    if session['logged_in'] == True:
        user_data=User.query.filter_by(id=session['userid']).first()
        db.session.delete(user_data) #DB에서 해당 유저 row삭제
        db.session.commit()
        session['logged_in']=False #로그인상태 해제
        session['user_num']=None    #저장하고 있던 유저번호 초기화 
        return redirect(url_for('home'))
    else:
        return render_template("loginplease.html")
    
@app.route("/mypage", methods=["GET","POST"])
def myPage():
    if session['logged_in'] == True:
        user_data = User.query.filter_by(id=session['userid']).first()
        user_rent_data = Rents.query.filter_by(rentusername=user_data.name, phone=user_data.phone).all()
        desc_rent_data = user_rent_data.reverse()
        return render_template("mypage.html", user=user_data, rents=user_rent_data)
    else:
        return render_template("loginplease.html")



@app.route("/myinfo",methods=['GET','POST'])
def myinfo():
    if session['logged_in'] == True:
        if request.method=='GET':
            user_data = User.query.filter_by(id=session['userid']).first()
            session['password']=user_data.password
            session['passwordcheck']=user_data.passwordcheck
            return render_template("myinfo.html", user = user_data)
    
        
        else :
            edit_user = User.query.filter_by(id=session['userid']).first()
            edit_user.id=request.form['userid']
            edit_user.name=request.form['username']
            edit_user.password=request.form['password']
            edit_user.passwordcheck=request.form['passwordcheck']
            edit_user.phone=request.form['phone']
            db.session.commit()
            return redirect(url_for('home'))
    else :
        return render_template("loginplease.html")
    
#@app.route("/myinfo/check", methods=['GET','POST'])
#def myinfoCheck():
#    if request.method=='POST':
#        user_data= User.query.filter_by(id=session['userid']).first()
#        return render_template("myinfo.html", user= user_data)
#    else :
#        return render_template("myinfocheck.html")
    
      


@app.route("/board",methods=['GET','POST'])   
class Boards(db.Model):
    __tablename__='bbs'
    num=db.Column(db.Integer,primary_key=True) #게시판 글 번호
    writer=db.Column(db.String)                #게시판 글쓴이
    title=db.Column(db.String)                 #게시판 글 제목
    content=db.Column(db.String)               #게시판 글 내용
    regdate=db.Column(db.String)               #게시판 글쓴 시간, 날짜
    reads=db.Column(db.Integer)                # 게시판 조회수
    picpath=db.Column(db.String)               # 게시판에 첨부한 이미자파일 경로
    def __init__(self, writer, title, content, regdate,reads,picpath):
        self.writer = writer
        self.title = title
        self.content = content
        self.regdate = regdate
        self.reads=reads
        self.picpath=picpath
    
    
    def __repr__(self):
        return"<Board('%s', '%s', '%s', '%d','%s')>" % (self.writer, self.title, self.regdate, self.reads,self.picpath)
    
@app.route("/board/list", methods=["GET","POST"], defaults={"page":1})
@app.route("/board/list/<int:page>",methods=['GET','POST'])
def boardList(page):
    #테이블로부터 모든 데이터 조회
    page = request.args.get('page', type=int, default=1)
    Posts=Boards.query.order_by(desc(Boards.num)).paginate(page,per_page=10,error_out=False)
    return render_template("bbslist.html", posts=Posts) #사용자 응답페이지에 boards변수에 데이터를 저장해서 전송




@app.route("/board/new")
def boardNew():
    if session['logged_in'] == True:
        user = User.query.filter_by(id=session['userid']).first()#유저 번호로 해당 유저 검색 (유저 번호가primary key)
        return render_template("bbsform.html" , username=user.name)
    else :
        return render_template("loginplease.html")

@app.route("/board/add" , methods=['GET', 'POST'])
def addPost():                                         #글 쓰기                  
    temp = str(int(time.time()))
    f = request.files['upfile']
      #저장할 경로 + 파일명
    f.save("static/images/" + temp + secure_filename(f.filename))
    dbfilepath = "/static/images/" + temp + secure_filename(f.filename)
    uploadpath = Boards(writer=request.form['writer'],title=request.form['title'],content=request.form['content'],
                        regdate=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),reads=0,picpath=dbfilepath)
    db.session.add(uploadpath) #사진 경로 DB에 저장
    db.session.commit()                                      
    return redirect(url_for("boardList"))



@app.route("/board/view/<int:bbs_num>")
def viewPost(bbs_num=None):                                         #글 내용 보기
    post = Boards.query.filter_by(num=bbs_num).first()     
    post.reads=  post.reads+1
    db.session.commit()                                            
    return render_template("bbsview.html", bbs = post)

@app.route("/board/edit",methods=['POST','GET'])
def editPost():
    if session['logged_in'] == True:                                                     #글 수정
        post = Boards.query.filter_by(num=request.form["bbsnum"]).first()
        return render_template("bbsedit.html",bbs=post)
    else:
        return render_template("loginplease.html")

@app.route("/board/save",methods=['POST','GET'])
def updatePost():                                                   #글 내용 수정
    post=Boards.query.filter_by(num=request.form["bbsnum"]).first()
    post.title=request.form["title"]
    post.content=request.form["content"]
        
    if request.files == "" :
        pass
    else :
        temp = str(int(time.time()))
        f = request.files['upfile']
        f.save("static/images/" + temp + secure_filename(f.filename))
        dbfilepath = "/static/images/" + temp + secure_filename(f.filename)
        post.picpath = dbfilepath
            
    db.session.commit()
    return redirect(url_for("boardList"))

@app.route("/board/delete",methods=['POST','GET'])
def removePost():                                       #글 삭제
    post=Boards.query.filter_by(num=request.form["bbsnum"]).first()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("boardList"))




    
class Rents(db.Model):
    __tablename__ = 'rents'
    
    rentnum = db.Column(db.Integer, primary_key = True)
    rentusername = db.Column(db.String)
    phone = db.Column(db.String)
    pickupdate = db.Column(db.String)
    returndate = db.Column(db.String)
    pickreturnplace = db.Column(db.String)
    rentaltype = db.Column(db.String)
    rentalqty = db.Column(db.Integer)
    addoption = db.Column(db.String)
    optionqty = db.Column(db.Integer)
    addoption2 = db.Column(db.String)
    optionqty2 = db.Column(db.Integer)
    note = db.Column(db.String)
    
    def __init__(self, rentusername,phone,pickupdate,returndate,pickreturnplace,rentaltype,rentalqty,addoption,optionqty,addoption2,optionqty2,note):
        self.rentusername=rentusername
        self.phone=phone
        self.pickupdate=pickupdate
        self.returndate=returndate
        self.pickreturnplace=pickreturnplace
        self.rentaltype=rentaltype
        self.rentalqty=rentalqty
        self.addoption=addoption
        self.optionqty=optionqty
        self.addoption2=addoption2
        self.optionqty2=optionqty2
        self.note=note
        
    def __repr__(self):
        return"<Rent('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')>" %(self.rentusername, self.phone, self.pickupdate,
                                                                            self.returndate, self.pickreturnplace, self.rentaltype,
                                                                            self.rentalqty, self.addoption, self.optionqty,
                                                                            self.addoption2, self.optionqty2, self.note)
    
@app.route("/booking")
def rentRegister():
    user_data=User.query.filter_by(name=session['username'], phone=session['phone']).first()
    return render_template("booking.html", user=user_data)        
        
        
        
        
@app.route('/checklist', methods = ['GET','POST'])
def checkList():                                                            #예약 확인서
    if request.method == 'POST' :
        new_camping = Rents(rentusername=request.form.get('rentusername'),
                            phone=request.form['phone'],
                            pickupdate=request.form['pickupdate'],
                            returndate=request.form['returndate'],
                            pickreturnplace=request.form['pickreturnplace'],
                            rentaltype=request.form['rentaltype'],
                            rentalqty=request.form['rentalqty'],
                            addoption=request.form['addoption'],
                            optionqty=request.form['optionqty'],
                            addoption2=request.form['addoption2'],
                            optionqty2=request.form['optionqty2'],
                            note=request.form['note'])
        db.session.add(new_camping)
        db.session.commit()
        
        checklist=Rents.query.filter_by(rentusername=request.form.get("rentusername"), phone=request.form["phone"],
                                        pickupdate=request.form["pickupdate"], returndate=request.form['returndate'],
                                        pickreturnplace=request.form['pickreturnplace'], rentaltype=request.form['rentaltype'],
                                        rentalqty=request.form['rentalqty'],addoption=request.form['addoption'],
                                        optionqty=request.form['optionqty'],addoption2=request.form['addoption2'],
                                        optionqty2=request.form['optionqty2'],note=request.form['note']).first()
        mainlist=mainsetPrice.query.filter_by(mainset_name=checklist.rentaltype).first()
        addoptlist=addoptionPrice.query.filter_by(addoption_name=checklist.addoption).first()
        addoptlist2=addoptionPrice2.query.filter_by(addoption_name2=checklist.addoption2).first()
        session['rent_num']= checklist.rentnum
        
        return render_template("checklist.html",rentcheck=checklist, maincheck=mainlist, addoptcheck=addoptlist, addoptcheck2=addoptlist2)
    
    else :
        return render_template("booking.html")




#업로드 HTML 렌더링

@app.route("/rent/pay")
def payment():
    return render_template("payment.html")

@app.route("/rent/cancel")
def cancel():                                   #예약 취소
    rent_data=Rents.query.filter_by(rentnum=session['rent_num']).first()
    user_data=User.query.filter_by(name=session['username'], phone=session['phone']).first()
    db.session.delete(rent_data) #DB에서 해당 유저 row삭제
    db.session.commit()
    session['rent_num']=None    #저장하고 있던 유저번호 초기화 
    return render_template("booking.html", user=user_data)

     

class mainsetPrice(db.Model):
    __tablename__ = 'mainset_price'
    
    mainset_num = db.Column(db.Integer,primary_key = True)
    mainset_name = db.Column(db.String)
    mainset_price = db.Column(db.Integer)
    
    def __init__(self, mainset_name, mainset_price):
        self.mainset_name = mainset_name
        self.mainset_price = mainset_price
        
    def __repr__(self):
        return"<Price('%s', '%s')>" %(self.mainset_name, self.mainset_price)
    
class addoptionPrice(db.Model):
    __tablename__ = 'addoption_price'
    
    addoption_num = db.Column(db.Integer,primary_key = True)
    addoption_name = db.Column(db.String)
    addoption_price = db.Column(db.Integer)
    
    def __init__(self, addoption_name, addoption_price):
        self.addoption_name = addoption_name
        self.addoption_price = addoption_price
        
    def __repr__(self):
        return"<Price('%s', '%s')>" %(self.addoption_name, self.addoption_price)
    
class addoptionPrice2(db.Model):
    __tablename__ = 'addoption_price2'
    
    addoption_num2 = db.Column(db.Integer,primary_key = True)
    addoption_name2 = db.Column(db.String)
    addoption_price2 = db.Column(db.Integer)
    
    def __init__(self, addoption_name2, addoption_price2):
        self.addoption_name2 = addoption_name2
        self.addoption_price2 = addoption_price2
        
    def __repr__(self):
        return"<Price('%s', '%s')>" %(self.addoption_name2, self.addoption_price2)
    
    
@app.route("/price/register", methods=["GET","POST"])
def priceregister():
    return render_template("pricechoice.html")
    

@app.route("/price/register/main", methods=["GET","POST"])
def mainpriceregister():
    if request.method == 'POST' :
        new_mainset_price = mainsetPrice(mainset_name = request.form['mainset_name'],
                                         mainset_price = request.form['mainset_price'])
        
        db.session.add(new_mainset_price)
        db.session.commit()
        
        main_pricelist=mainsetPrice.query.filter_by(mainset_name=request.form['mainset_name']).first()
        return render_template("mainpricelist.html",mainprice=main_pricelist)
    
    else :
        return render_template("mainpriceregister.html")
    
    
@app.route("/price/register/addoption", methods=["GET","POST"])
def addoptionregister():
    if request.method == 'POST' :
        new_addoption_price = addoptionPrice(addoption_name=request.form['addoption_name'],
                                             addoption_price=request.form['addoption_price'])
        
        db.session.add(new_addoption_price)
        db.session.commit()
        
        addoption_pricelist=addoptionPrice.query.filter_by(addoption_name=request.form['addoption_name']).first()
        return render_template("addoptionpricelist.html", addoptionprice=addoption_pricelist)
    
    else :
        return render_template("addoptionpriceregister.html")
    
    
@app.route("/aboutus")
def howtoCome():
    return render_template("aboutus.html")

class Office(db.Model):
    __tablename__='office'
    
    office_num =db.Column(db.Integer, primary_key = True)
    office_name=db.Column(db.String)
    address=db.Column(db.String)
    tel=db.Column(db.String)
    opentime=db.Column(db.String)
    
    def __init__(self, office_name, address, tel, opentime):
        self.office_name = office_name
        self.address = address
        self.tel = tel
        self.opentime = opentime
        
    def __repr__(self):
        return"<Price('%s','%s','%s','%s')>" %(self.office_name, self.address, self.tel, self.opentime)
    
    
    
    
#@app.route("/weather", methods=["GET","POST"])
#def weatherCheck():
    #return render_template("weather.html")


        
      
    

app.jinja_env.filters['datetimeformat'] = format_datetime


if __name__ == '__main__':
    app.debug=True
    #db.create_all()
    app.secret_key = '1234567890'
    app.run(host='0.0.0.0', threaded=True)