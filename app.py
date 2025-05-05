from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # Allows cross-origin requests

def get_db_connection():
    conn = sqlite3.connect("evaluations.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/student", methods=["GET"])
def get_students():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM student").fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

@app.route("/professor", methods=["GET"])
def get_professors():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM professors").fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

@app.route("/course", methods=["GET"])
def get_courses():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

@app.route("/enrollment/<student_id>", methods=["GET"])
def get_enrollments(student_id):
    conn = get_db_connection()
    query = "SELECT * FROM enrollment WHERE student_id = ?"
    enrollments = conn.execute(query, (student_id, )).fetchall()
    conn.close()
    if not enrollments:
        return jsonify([])  # Return an empty JSON list instead of nothing

    # return jsonify(enrollments)
    return jsonify([dict(enrollment) for enrollment in enrollments])

@app.route("/section/<course_id>", methods=["GET"])
def get_sections(course_id):
    conn = get_db_connection()
    query = "SELECT * FROM sections WHERE course_id = ?"
    enrollments = conn.execute(query, (course_id, )).fetchall()
    conn.close()
    if not enrollments:
        return jsonify([])  # Return an empty JSON list instead of nothing

    # return jsonify(enrollments)
    return jsonify([dict(enrollment) for enrollment in enrollments])

@app.route("/evaluations/<student_id>/<section_id>", methods=["GET"])
def get_evaluation(student_id, section_id):
    print("Fetching evaluations for: ", student_id, section_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Convert if necessary
        student_id = int(student_id)  # Uncomment if student_id is stored as an integer
        section_id = str(section_id)  # Uncomment if section_id is stored as an integer

        query = "SELECT * FROM evaluations WHERE student_id = ? AND section_id = ?"
        evaluations = cursor.execute(query, (student_id, section_id)).fetchall()

        print("app_evaluations: ", evaluations)  # Debugging print statement

        if not evaluations:
            return jsonify([])

        return jsonify([dict(row) for row in evaluations])

    except sqlite3.Error as e:
        print("SQL Error:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


@app.route("/create_evaluation", methods=["POST"])
def create_evaluation():
    data = request.get_json()
    student_id = data.pop("student_id")
    section_id = data.pop("section_id")
    evaluation_data = str(data)
    try:
        conn = sqlite3.connect("evaluations.db")
        cursor = conn.cursor()
        # query = """INSERT INTO evaluations (student_id, section_id, evaluation) VALUES (?, ?, ?)"""
        print(student_id, section_id, data)
        cursor.execute("INSERT INTO evaluations (student_id, section_id, evaluation) VALUES (?, ?, ?)",
                       (student_id, section_id, evaluation_data))

        conn.commit()
        conn.close()

        return jsonify({"message": "Evaluation created successfully"}), 201
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500  # Return error in JSON format

@app.route("/evaluations/<evaluation_number>", methods=["DELETE"])
def delete_evaluation(evaluation_number):
    print(f"Deleting evaluation number {evaluation_number}")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if evaluation exists before deleting
        query = "SELECT * FROM evaluations WHERE evaluation_number = ?"
        evaluation = cursor.execute(query, (evaluation_number, )).fetchone()

        if not evaluation:
            return jsonify({"error": "Evaluation not found"}), 404

        # Delete the evaluation
        delete_query = "DELETE FROM evaluations WHERE evaluation_number = ?"
        cursor.execute(delete_query, (evaluation_number, ))
        conn.commit()

        return jsonify({"message": "Evaluation deleted successfully"}), 200

    except sqlite3.Error as e:
        print("SQL Error:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)
