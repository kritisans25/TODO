from flask import Flask, redirect,render_template,request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)  # Initialize Flask application app is my name of the application
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Configure the database URI
db = SQLAlchemy(app)  # Initialize SQLAlchemy with the Flask app

class MyTask(db.Model):  # Define a model named MyTask
    id=db.Column(db.Integer, primary_key=True)  # Primary key column
    content=db.Column(db.String(100),nullable=False)  # Content column with a max length of 100 characters
    complete=db.Column(db.Integer,default=0)  # Complete status column with default value 0
    created=db.Column(db.DateTime,default=datetime.utcnow)  # Created timestamp column with default value as current UTC time

    def __repr__(self):
        return '<Task %r>' % self.id  # String representation of the MyTask model


@app.route('/',methods=['GET','POST'])  # Define route for the root URL
def index():
    #adding tasks to the database
    if request.method=="POST":
        print("test post method")
        print(request.form)
        current_task=request.form['task']  # Get the current task from the form data
        new_task=MyTask(content=current_task)  # Create a new task instance
        try:
            db.session.add(new_task)  # Add the new task to the session
            db.session.commit()  # Commit the session to save the task to the database
            return redirect('/')  # Redirect to the root URL
        except Exception as e:
            print(f"Error adding task: {e}")
            return f"Error adding task: {e}"
    else:
        tasks=MyTask.query.order_by(MyTask.created).all()  # Query all tasks ordered by creation time
        return render_template("index.html", tasks=tasks)  # this is the text to be displayed on my home main page.
# deleting tasks
@app.route('/delete/<int:id>')  # Define route for deleting a task by ID
def delete(id:int):
    delete_task= MyTask.query.get_or_404(id)  # Get the task to be deleted by ID or return 404 if not found
    try:
        db.session.delete(delete_task)  # Delete the task from the session
        db.session.commit()  # Commit the session to save changes to the database
        return redirect('/')  # Redirect to the root URL
    except Exception as e:
        print(f"Error deleting task: {e}")
        return f"Error deleting task: {e}"

@app.route('/edit/<int:id>',methods=['GET','POST'])  # Define route for editing a task by ID
def edit(id:int):
    edit_task= MyTask.query.get_or_404(id)  # Get the task to be edited by ID or return 404 if not found
    if request.method=="POST":
        edit_task.content=request.form['task']  # Update the task content from the form data
        try:
            db.session.commit()  # Commit the session to save changes to the database
            return redirect('/')  # Redirect to the root URL
        except Exception as e:
            print(f"Error updating task: {e}")
            return f"Error updating task: {e}"
    else:
        return render_template("edit.html", task=edit_task)  # Render the edit template with the task data




if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)  # Run the application in debug mode

