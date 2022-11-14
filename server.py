
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python3 server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
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

UPLOAD_FOLDER = 'static/uploads/'
app.secret_key="canyonjack"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16*1024*1024
ALLOWED_EXT = set(['png', 'jpg', 'jpeg'])
def allowed_type(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


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
        g.conn.execute("INSERT INTO student(uni,name,username,year,plan_name) VALUES (%s, %s, %s, %s, %s)", uni, name, username, year, plan_name)
        return redirect('/')
    return render_template('auth.html')



@app.route('/hall page/<name>')
def hall_page(name):
    print(request.args)
    hall_name = name
    time = []
    loc = []
    info = []
    cursor = g.conn.execute("SELECT * FROM dining_hall WHERE hall_name = '{}'".format(name))
    for result in cursor:
        time.append(result[1:3])
        loc.append(result[4:6])
    cursor = g.conn.execute("SELECT * FROM writes W, review R WHERE W.rid=R.rid AND W.hall_name='{}'".format(name))
    for result in cursor:
        info.append(result)
    cursor.close()
    context = dict(hall_name = hall_name, location = loc, hours = time, review = info)
    return render_template("hall_page.html", **context)

  
@app.route('/review', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename== '':
        flash('NO image selected')
        return redirect(request.url)
    if file and allowed_type(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print('upload_image filename: ' +filename)
        flash('image uploaded succesfully')
        return render_template('review.html', filename=filename)
    else:
        flash('allowed image types are: png, jpg, jpeg')
        return redirect(request.url)

@app.route('/display/<filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)
   
@app.route('/review/<name>', methods=['GET', 'POST'])
def review(name):
    if request.method=='POST':
        UNI = ""
        user = request.form['username']
        food = int(request.form['food'])
        vibe = int(request.form['vibe'])
        staff = int(request.form['staff'])
        overall = int((food+vibe+staff)/3)
        comment = request.form['comment']

        file = request.files['file']
        if file.filename=='':
            return "no image", redirect(request.url)
        if file and allowed_type(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return render_template('review.html', filename=filename)
        
        cursor = g.conn.execute("SELECT MAX(rid) FROM review")
        for result in cursor:
            rid = result[0]
        rid += 1
        stamp = date.today()
        cursor = g.conn.execute("SELECT uni FROM student WHERE username='{}'".format(user))
        UNI = cursor.fetchone()[0]
        cursor.close()
        if UNI != "":
            g.conn.execute("INSERT INTO review(rid, overall, food, vibe, staff, date, comment) VALUES(%s,%s,%s,%s,%s,%s,%s)", rid, overall, food, vibe, staff, stamp, comment)
            g.conn.execute("INSERT INTO writes(rid, uni, hall_name) VALUES(%s,%s,%s)", rid, UNI, name)
            g.conn.execute("INSERT INTO photos(url, rid) VALUES(%s,%s)", filename, rid)
            return redirect('hall page',name)
        else: return render_template("auth.html")
    context = dict(hall_name = name)
    return render_template('review.html', **context) 

@app.route('/dining_plan')
def dining_plan():
    return render_template("dining_plan.html")


@app.route('/search', methods=['GET', 'POST'])
def search():
    li = ["john jay", "jjs place", "ferris booth commons", "faculty house", "chef mikes sub shop"]
    print(request.args)
    if request.method == 'POST':

        hall_name = request.form['hall_name']

        time = []
        loc = []
        info = []
        if hall_name.lower() not in li:
            #flash("Dining Hall not found")
            return redirect('/')

        cursor = g.conn.execute("SELECT hall_name FROM dining_hall WHERE hall_name='{}'".format(hall_name))
        for result in cursor:
            time.append(result[1:3])
            loc.append(result[4:6])
        cursor = g.conn.execute("SELECT * FROM writes W, review R WHERE W.rid=R.rid AND W.hall_name='{}'".format(hall_name))
        for result in cursor:
            info.append(result)
        cursor.close()
        context = dict(hall_name = hall_name, location = loc, hours = time, review = info)
        return render_template("hall_page.html", **context)
    return render_template("form_practice.html")

@app.route('/another')
def another():
    return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
  return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


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
