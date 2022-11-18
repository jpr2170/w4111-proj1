
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python3 server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
#inconsequential code
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask,url_for, flash, request, render_template, g, redirect, Response
import urllib.request
from werkzeug.utils import secure_filename
from datetime import datetime, date
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'forms')
app = Flask(__name__, template_folder=tmpl_dir)


DATABASEURI = "postgresql://jpr2170:5019@34.75.94.195/proj1part2"

engine = create_engine(DATABASEURI)


@app.before_request
def before_request():
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback; traceback.print_exc()
        g.conn = None

@app.teardown_request
def teardown_request(exception):
    try:
        g.conn.close()
    except Exception as e:
        pass

@app.route('/')
def home_page():
    print(request.args)
    cursor = g.conn.execute("SELECT hall_name FROM dining_hall")
    dh = []
    for result in cursor:
        dh.append(result["hall_name"])
    cursor.close()

    context = dict(data = dh)
    return render_template("home_page.html", **context)

@app.route('/plan')
def plan(): 
    print(request.args)
    cursor = g.conn.execute("SELECT * FROM dining_plan")
    plans = []
    for result in cursor:
        plans.append(result)  # can also be accessed using result[0]
    cursor.close()
    context = dict(plan = plans)
    return render_template("plan.html", **context)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method=='POST':
        uni = request.form['uni']
        name = request.form['name']
        username = request.form['username']
        year = request.form['year']
        plan_name = request.form['plan_name']
        if len(username) > 15:
            render_template('auth.html')
        g.conn.execute("INSERT INTO student(uni,name,username,year,plan_name) VALUES (%s, %s, %s, %s, %s)", uni, name, username, year, plan_name)
        return redirect('/')
    if request.method == 'GET':
        plans = []
        cursor = g.conn.execute("SELECT plan_name FROM dining_plan")
        for result in cursor:
            plans.append(result)
        cursor.close()
        context = dict(plans = plans)
        return render_template("auth.html", **context)



@app.route('/hall page/<name>')
def hall_page(name):
    print(request.args)
    hall_name = name
    time = []
    loc = []
    review = []
    review_pics = []
    pics = []
    cursor = g.conn.execute("SELECT * FROM dining_hall WHERE hall_name = '{}'".format(name))
    for result in cursor:
        time.append(result[1:3])
        loc.append(result[4:6])
    cursor = g.conn.execute("SELECT AVG(R.overall) FROM review R, writes W WHERE R.rid=W.rid AND W.hall_name='{}'".format(name))
    rating = cursor.fetchone()[0]
    rating = float('%.2g' % rating)
    cursor = g.conn.execute("SELECT S.username, R.overall, R.food, R.vibe, R.staff, R.comment FROM writes W, review R, student S WHERE W.hall_name='{}' AND W.rid=R.rid AND W.uni=S.uni AND W.rid NOT IN (SELECT rid FROM photos)".format(name))
    for result in cursor:
        review.append(result)
    cursor = g.conn.execute("SELECT S.username, R.overall, R.food, R.vibe, R.staff, R.comment, P.url FROM writes W, review R, student S, photos P WHERE W.rid=R.rid AND W.uni=S.uni AND P.rid=R.rid AND W.hall_name = '{}'".format(name))
    for result in cursor:
        review_pics.append(result)
    cursor.close()
    context = dict(hall_name = hall_name, location = loc, hours = time, review = review, photo = review_pics, rating = rating)
    return render_template("hall_page.html", **context)

@app.route('/review/<name>', methods=['GET', 'POST'])
def review(name):
    if request.method=='POST':
        hall_name = name
        #uni= ""
        url = ""
        user = request.form['username']
        food = int(request.form['food'])
        vibe = int(request.form['vibe'])
        staff = int(request.form['staff'])
        overall = int((food+vibe+staff)/3)
        comment = request.form['comment']
        url = request.form['url']
        cursor = g.conn.execute("SELECT MAX(rid) FROM review")
        rid = cursor.fetchone()[0]
        rid += 1
        stamp = date.today()
        cursor = g.conn.execute("SELECT uni FROM student WHERE username='{}'".format(user))
        uni = cursor.fetchone()
        if uni != None:
            uni = uni[0]
            g.conn.execute("INSERT INTO review(rid, overall, food, vibe, staff, date, comment) VALUES(%s,%s,%s,%s,%s,%s,%s)", rid, overall, food, vibe, staff, stamp, comment)
            g.conn.execute("INSERT INTO writes(rid, uni, hall_name) VALUES(%s,%s,%s)", rid, uni, hall_name)
            if url != "":
                g.conn.execute("INSERT INTO photos(url, rid) VALUES(%s,%s)", url, rid)
            context = dict(hall_name=name)
            return redirect(url_for('hall_page', name=name))
        else: return render_template("auth.html")
        cursor.close()
    context = dict(hall_name = name)
    return render_template('review.html', **context) 


@app.route('/search', methods=['GET','POST'])
def search():
    if request.method == "POST":
        print(request.args)
        username_list = []
        review = []
        review_pics = []
        friends = []
        cursor = g.conn.execute("SELECT username FROM student")
        for res in cursor:
            username_list.append(res[0])
        username = request.form['user']
        if username not in username_list:
            context = dict(username=username)
            return render_template('search_fail.html', **context)
        cursor = g.conn.execute("SELECT uni FROM student WHERE student.username='{}'".format(username))
        uni = cursor.fetchone()[0]
        cursor = g.conn.execute("SELECT W.hall_name, R.overall, R.food, R.vibe, R.staff, R.comment FROM writes W, review R, student S WHERE W.rid=R.rid AND W.uni=S.uni AND S.username='{}' AND W.rid NOT IN (SELECT rid FROM photos)".format(username))
        for result in cursor:
            review.append(result)
        cursor = g.conn.execute("SELECT W.hall_name, R.overall, R.food, R.vibe, R.staff, R.comment, P.url FROM writes W, review R, student S, photos P WHERE W.rid=R.rid AND W.uni=S.uni AND S.username='{}' AND P.rid=R.rid".format(username))
        for result in cursor:
            review_pics.append(result)
        cursor = g.conn.execute("SELECT * FROM is_friends WHERE uni1='{}' OR uni2='{}'".format(uni,uni))
        for result in cursor:
            if result[0] != uni:
                friends.append(result[0])
            else:
                friends.append(result[1])
        cursor.close()
        context = dict(username=username, review = review, pics = review_pics, friends = friends)
        return render_template('user_review.html', **context)
    return render_template('user_search.html')


    
@app.route('/add', methods=['GET', 'POST'])
def add_friend():
    print(request.args)
    if request.method=='POST':
        username_list = []
        cursor = g.conn.execute("SELECT username FROM student")
        for res in cursor:
            username_list.append(res[0])

        username1 = request.form['username1']
        if username1 not in username_list:
            context = dict(username=username1)
            return render_template('search_fail.html', **context)

        cursor = g.conn.execute("SELECT uni FROM student WHERE student.username='{}'".format(username1))
        uni1 = cursor.fetchone()[0]

        username2 = request.form['username2']
        if username2 not in username_list:
            context = dict(username=username2)
            return render_template('search_fail.html', **context)

        cursor = g.conn.execute("SELECT uni FROM student WHERE student.username='{}'".format(username2))
        uni2 = cursor.fetchone()[0]
        
        cursor = g.conn.execute("SELECT uni1, uni2 FROM is_friends")
        group = {uni1,uni2}
        in_friends = False
        for result in cursor:
            try_set = {result[0],result[1]}
            if group == try_set:
                in_friends = True
        if in_friends == True:
            return redirect('/')
        cursor = g.conn.execute("INSERT INTO is_friends(uni1, uni2) VALUES (%s, %s)", uni1, uni2)

        cursor.close()
        return redirect('/')
        
    return render_template('add_friend.html')

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):

    """Show the help text using:
        python3 server.py --help
    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
