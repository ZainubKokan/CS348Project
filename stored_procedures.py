import sqlite3
import json
import app

# Need to write stored procedures to generate reports


# COMPUTATION FUNCTIONS
def compute_gpa(evals):
    def gpa_conversion(grade):
        if grade == "A+" or grade == "A":
            return 4.0
        elif grade == "A-":
            return 3.7
        elif grade == "B+":
            return 3.3
        elif grade == "B":
            return 3.0
        elif grade == "B-":
            return 2.7
        elif grade == "C+":
            return 2.3
        elif grade == "C":
            return 2.0
        elif grade == "C-":
            return 1.7
        elif grade == "D+":
            return 1.3
        elif grade == "D":
            return 1.0
        elif grade == "D-":
            return 0.7
        elif grade == "F":
            return 0.0
        else:
            return None
    grades = []
    for eval in evals:
        grades.append(gpa_conversion(eval['grade']))
    grades = [grade for grade in grades if grade is not None]
    gpa = sum(grades)/len(grades)
    gpa = round(gpa, 2)
    return gpa


def take_again(evals):
    taken = 0
    would_take_again = 0
    for eval in evals:
        taken += 1
        if eval['would_take_again'] == 'Yes':
            would_take_again += 1
    percentage = would_take_again/taken
    percentage = percentage * 100
    percentage = round(percentage, 2)
    return percentage


def ave_ratings(evals):
    quality = []
    difficulty = []
    organization = []
    for eval in evals:
        quality.append(eval['quality_rating'])
        difficulty.append(eval['difficulty_rating'])
        organization.append(eval['organization_rating'])
    quality = round(sum(quality)/len(quality), 1)
    difficulty = round(sum(difficulty) / len(difficulty), 1)
    organization = round(sum(organization) / len(organization), 1)
    return quality, difficulty, organization


def list_of_tags(evals):
    tags = []
    for eval in evals:
        tags.extend(eval['tags'])
    tags = list(set(tags))
    return tags


def list_of_comments(evals):
    comments = []
    for eval in evals:
        if len(eval['comments']) > 0:
            comments.append(eval['comments'])
    return comments


# REPORT FUNCTIONS
def student_report(student_id):     # GENERATE REPORT PER STUDENT
    conn = app.get_db_connection()  # connect to database
    # find all matching evaluations for that student
    matches = conn.execute(f"SELECT * FROM evaluations WHERE student_id = {student_id}").fetchall()
    # evaluations(evaluation_number, student_id, section_id, evaluation)
    # get list of each course & for each course include evaluation (if created)
    for i in range(len(matches)):
        match = {}
        match['evaluation_number'] = matches[i]['evaluation_number']
        match['section_id'] = matches[i]['section_id']
        match['course_name'] = conn.execute("SELECT course_name FROM sections NATURAL JOIN courses WHERE section_id = ?", (match['section_id'], )).fetchone()[0]
        match['professor_name'] = conn.execute("SELECT professor_name FROM sections NATURAL JOIN professors WHERE section_id = ?", (match['section_id'], )).fetchone()[0]
        match['evaluation'] = json.loads(matches[i]['evaluation'].replace("'", '"'))
        matches[i] = match
    # get average grade/GPA
    evals = [match['evaluation'] for match in matches]
    gpa = compute_gpa(evals)
    # create list of courses not evaluated
    evaluated = [match['section_id'] for match in matches]
    enrolled = conn.execute(f"SELECT section_id FROM enrollment WHERE student_id = {student_id}").fetchall()
    enrolled = [course[0] for course in enrolled]
    no_eval = [course for course in enrolled if course not in evaluated]
    for i in range(len(no_eval)):
        course = {}
        course['section_id'] = no_eval[i]
        course['course_name'] = conn.execute("SELECT course_name FROM sections NATURAL JOIN courses WHERE section_id = ?", (course['section_id'],)).fetchone()[0]
        course['professor_name'] = conn.execute("SELECT professor_name FROM sections NATURAL JOIN professors WHERE section_id = ?", (course['section_id'],)).fetchone()[0]
        no_eval[i] = course
    return gpa, matches, no_eval


def professor_report(professor_id):     # GENERATE REPORT PER PROFESSOR
    conn = app.get_db_connection()  # connect to database
    # get professor info
    prof = conn.execute("SELECT professor_name FROM professors WHERE professor_id = ?", (professor_id,)).fetchone()[0]
    # find all matching evaluations for that professor
    matches = conn.execute("SELECT evaluation FROM evaluations NATURAL JOIN sections WHERE professor_id = ?", (professor_id,)).fetchall()
    evals = []  # create list of the evaluations
    for match in matches:
        evals.append(json.loads(match[0].replace("'", '"')))

    print(prof)
    # get average grade/GPA
    gpa = compute_gpa(evals)
    print("gpa", gpa)
    # Get average ratings: quality, difficulty, organization
    quality, difficulty, organization = ave_ratings(evals)
    print("quality", quality)
    print("difficulty", difficulty)
    print("organization", organization)
    # Get list of tags students included
    tags = list_of_tags(evals)
    print(tags)
    # Include list of comments
    comments = list_of_comments(evals)
    print(comments)
    # structure dictionary to return all info and access on front end
    report = {
        'gpa': gpa,
        'quality_rating': quality, 'difficulty_rating': difficulty, 'organization_rating': organization,
        'tags': tags,
        'comments': comments
    }
    return report


def section_report(section_id):     # GENERATE REPORT PER COURSE SECTION
    conn = app.get_db_connection()  # connect to database
    # find all matching evaluations for that section
    matches = conn.execute("SELECT evaluation FROM evaluations WHERE section_id = ?", (section_id,)).fetchall()
    evals = []  # create list of the evaluations
    for match in matches:
        evals.append(json.loads(match[0].replace("'", '"')))

    # Get average GPA/grade
    gpa = compute_gpa(evals)
    # Get % who would take again
    would_take_again = take_again(evals)
    # Get average ratings: quality, difficulty, organization
    quality, difficulty, organization = ave_ratings(evals)
    # Get list of tags students included
    tags = list_of_tags(evals)
    # Include list of comments
    comments = list_of_comments(evals)
    # structure dictionary to return all info and access on front end
    report = {
        'gpa': gpa, 'take_again': would_take_again,
        'quality_rating': quality, 'difficulty_rating': difficulty, 'organization_rating': organization,
        'tags': tags,
        'comments': comments
    }
    return report


def course_report(course_id):   # GENERATE REPORT PER COURSE OVERALL
    conn = app.get_db_connection()  # connect to database
    # find all matching evaluations for that section
    matches = conn.execute("SELECT evaluation FROM evaluations NATURAL JOIN sections WHERE course_id = ?", (course_id,)).fetchall()
    evals = []  # create list of the evaluations
    for match in matches:
        evals.append(json.loads(match[0].replace("'", '"')))

    # Get average GPA/grade
    gpa = compute_gpa(evals)
    # Get % who would take again
    would_take_again = take_again(evals)
    # Get average ratings: quality, difficulty, organization
    quality, difficulty, organization = ave_ratings(evals)
    # Get list of tags students included
    tags = list_of_tags(evals)
    # Include list of comments
    comments = list_of_comments(evals)
    # structure dictionary to return all info and access on front end
    report = {
        'gpa': gpa, 'take_again': would_take_again,
        'quality_rating': quality, 'difficulty_rating': difficulty, 'organization_rating': organization,
        'tags': tags,
        'comments': comments
    }
    return report
