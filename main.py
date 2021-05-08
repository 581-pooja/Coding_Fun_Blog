from flask import Flask , render_template , request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
from  datetime import datetime
import math
import json
import pymysql
import os
pymysql.install_as_MySQLdb()


with open('config.json', 'r') as c:
    params = json.load(c)["params"]  # this will open the config file

local_server = "True"
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/db_name'

class Contacts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  nullable=False)
    phone = db.Column(db.String(12),  nullable=False)
    msg = db.Column(db.String(180),  nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20),  nullable=False)


class Posts(db.Model):  #here-post.title = posts.title (db) from db the values will come here
    srno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20),  nullable=False)
    subtitle = db.Column(db.String(21), nullable=False)
    slug = db.Column(db.String(21),  nullable=False)
    content = db.Column(db.String(180),  nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=False)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    
    page = request.args.get('page') # we r taking value of page
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]

    if(page == 1):
        prev = "#"
        next = "/?page=" + str(page+1)
    elif(page == last):
        prev = "/?page=" + str(page-1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    # posts = Posts.query.filter_by().all()[0:params['no_of_posts']]  # my posts variable in which data persent  #This slicing may give error not good practise
    return render_template('index.html',params = params,posts=posts,prev= prev,next=next)  # html.name = py.name.var this posts pass in html posts

@app.route("/about")
def about():
    return render_template('about.html',params = params)

@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():
    if "user" in session and session['user']==params['admin_user']:
        posts = Posts.query.all()
        return render_template("dashboard.html",params=params,posts=posts)

    if (request.method == 'POST'):
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username == params['admin_user'] and userpass == params['admin_password']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('/dashboard.html',params=params,posts=posts)
        return render_template('/login.html',params = params)
        
    else:
        return render_template('/login.html',params = params)


@app.route("/edit/<string:srno>", methods = ['GET', 'POST'])
def edit(srno):
    if('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if srno == '0':
                post = Posts(title = box_title,subtitle=subtitle,slug = slug,content=content,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
                return  render_template('add_new_post.html',params=params,srno=srno)
            else:
                post = Posts.query.filter_by(srno=srno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.subtitle = subtitle
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/' + srno)
        post = Posts.query.filter_by(srno = srno).first()
        return  render_template('edit.html',params=params,post=post)


@app.route("/new_post/<string:srno>", methods = ['GET', 'POST'])
def new_post(srno):
    if('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if srno == '0':
                post = Posts(title = box_title,subtitle=subtitle,slug = slug,content=content,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
        return  render_template('add_new_post.html',params=params,srno=srno)


@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")

@app.route("/delete/<string:srno>", methods = ['GET', 'POST'])
def delete(srno):
    if('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(srno=srno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone_num')  # it is normal/local variable
        message = request.form.get('message')
        # All mention in red colour i.e. first msg ( It is Database name)
        entry = Contacts(name=name, email=email, phone=phone, date=datetime.now(), msg=message,)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message from' + name,
                          sender=email,
                          recipients=[params['gmail-user']],  # there can be many recepit therefore pass list
                          body=message + "\n" + phone
                          )
    return  render_template('contact.html',params = params)

#For auto increment thereshould be a value in first then it can be incrementted
#Since request method is post now get will not come form action = "Post"


@app.route("/post/<string:post_slug>",methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()
    return render_template('post.html',params = params,post=post) # here-post.title = posts.title (db)

app.run(debug=True,port=8000)
