"""Entry point for the Flask web app."""

from flask import Flask, redirect, url_for
from app.visualization import viz_bp

app = Flask(__name__)
app.register_blueprint(viz_bp)


@app.route("/")
def home():
    return redirect(url_for("visualization.visualization_page"))


if __name__ == "__main__":
    app.run(debug=True)
