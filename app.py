import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_cors import CORS

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
db = SQLAlchemy(app)
CORS(app)

@app.route('/query', methods=['POST'])
def query_ndvi():
    data = request.json
    state = data.get("state", "").replace(" ", "").lower()
    year = data.get("year")
    month = data.get("month")

    sql = text("""
        SELECT temperature, rainfall, soilmoisture, ndvi_value, ndvi_url
        FROM ndvi_data 
        WHERE state = :state AND year = :year AND month = :month
    """)

    result = db.session.execute(sql, {"state": state, "year": year, "month": month}).fetchone()
    if result:
        return jsonify({
            "temperature": result[0],
            "rainfall": result[1],
            "soilmoisture": result[2],
            "ndvi_value": result[3],
            "ndvi_url": result[4]
        })
    else:
        return jsonify({"error": "No data found"}), 404

if __name__ == "__main__":

    app.run()
