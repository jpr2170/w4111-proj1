
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
from flask import Flask, request, render_template, g, redirect, Response

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
def dining_hall():
    print(request.args)
    cursor = g.conn.execute("SELECT hall_name FROM dining_hall")
    dh = []
    for result in cursor:
        dh.append(result["hall_name"])
    cursor.close()

    context = dict(data = dh)
    return render_template("dining_halls.html", **context)

@app.route('/plan')
def plan(): 
    print(request.args)
    cursor = g.conn.execute("SELECT plan_name FROM dining_plan")
    plans = []
    for result in cursor:
        plans.append(result['plan_name'])  # can also be accessed using result[0]
    cursor.close()

    context = dict(data = plans)

    return render_template("plan.html", **context)

@app.route('/dining_plan')
def dining_plan():
    return render_template("dining_plan.html")


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        hall_name = request.form['hall_name']
        #g.conn.execute("SELECT hall_name FROM dining_hall WHERE hall_name like '%{hallName}%';")
        #g.conn.execute("SELECT hall_name FROM dining_hall WHERE hall_name={}".format(hallName))

        cursor = g.conn.execute("SELECT hall_name FROM dining_hall WHERE hall_name like '%(%s)%'", (hall_name))

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
