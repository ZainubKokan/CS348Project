from flask import Flask
from app import app
from reactpy.backend.flask import configure
from frontend import App  # Import the ReactPy component

configure(app, App)

if __name__ == "__main__":
    app.run(debug=True, port=3000)
