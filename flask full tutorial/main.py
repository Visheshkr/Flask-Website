import smtplib 
import json
import os
import math
from flask import Flask,render_template,redirect,request,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename

app=Flask(__name__)

app.secret_key='super-secret-key'

with open('config.json' ,'r') as c:
    params=json.load(c)['params']
local_server=True
app.config['UPLOAD_FOLDER']=params['upload_location']
smtp = smtplib.SMTP_SSL('smtp.gmail.com',port=465)
smtp.login(params['gmail-user'],params['gmail-password'])

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)
class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20),nullable=False)
    mes = db.Column(db.String(120), nullable=False)
    phone_num = db.Column(db.String(12),nullable=False)
    date = db.Column(db.String(12),nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(20),nullable=False)
    content = db.Column(db.String(120), nullable=False)
    sub_title = db.Column(db.String(34),nullable=False)
    date = db.Column(db.String(12),nullable=True)
    img_file=db.Column(db.String(12),nullable=True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)



@app.route("/about")    
def about():
    return render_template('about.html',params=params)

@app.route("/sample_post")
def sample_post():
    return render_template('sample_post.html',params=params)

@app.route("/contact",methods=['GET','POST'])    
def contact():
    count=0
    if(request.method=='POST'):
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')
        entry=Contacts(name=name,phone_num=phone,mes=message,date=datetime.now(),email=email)
        db.session.add(entry)
        db.session.commit()
        smtp.sendmail(email,params['gmail-user'],message)
        count+=1
    return render_template('contact.html',params=params,count=count)

@app.route("/dashboard",methods=['GET','POST'])
def dashboard():

    if('user' in session and session['user']==params['admin_user']):
        posts=Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)

    if(request.method=='POST'):
        user_name=request.form.get('uname')
        user_password=request.form.get('pass')
        if(user_name==params['admin_user'] and user_password==params['admin_password']):
            session['user']=user_name
            posts=Posts.query.all()
            return render_template('dashboard.html',params=params,posts=posts)
    return render_template('login.html',params=params)   

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")

@app.route("/delete/<string:sno>")
def delete(sno):
    if('user' in session and session['user']==params['admin_user']):
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect("/dashboard") 


@app.route("/edit/<string:sno>",methods=['GET','POST'])
def edit(sno):
    if('user' in session and session['user']==params['admin_user']):
        if request.method=="POST":
            box_title = request.form.get('title')
            sline = request.form.get('sub_title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            if sno=='0':
                post = Posts(title=box_title, slug=slug, content=content, sub_title=sline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=box_title    
                post.sub_title=sline
                post.content=content
                post.slug=slug
                post.img_file=img_file
                post.date=date
                db.session.commit()
                return redirect('/edit/'+sno)

    post=Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html',params=params,post=post,sno=sno)

@app.route("/uploader",methods=['GET','POST'])
def upload():
    if('user' in session and session['user']==params['admin_user']):
        if(request.method=="POST"):
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "Uploaded Successfully"

@app.route("/post/<string:post_slug>",methods=['GET'])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)            
app.run(debug=True) 
