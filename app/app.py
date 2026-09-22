"""Entry point for the Flask web app."""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "HCMC Traffic A* application is running."


if __name__ == "__main__":
    app.run(debug=True)
