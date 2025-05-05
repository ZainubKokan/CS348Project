from flask import Flask
from reactpy import component, use_state, html, use_effect
from reactpy.backend.flask import configure
import requests
import sqlite3
import json
import stored_procedures as sp

app = Flask(__name__)
API_BASE_URL = "http://127.0.0.1:3000"  # Flask server

grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F", "P", "N"]

tags = ["Tough grader", "Participation matters", "Mandatory attendance", "Group projects", "Extra credit",
        "Gives good feedback", "Lots of homework", "Test heavy", "Exams big part of final grade"]


@component
def Home(set_page):
    return html.div(
        html.h1("Welcome to the App"),
        html.button({"on_click": lambda event: set_page("page1")}, "Create/Edit/Delete Course Evaluations"),
        html.button({"on_click": lambda event: set_page("page2")}, "Generate Evaluation Reports"),
    )


@component
def Page1(set_page):
    students, set_students = use_state([])

    # Fetch students when component mounts
    def fetch_students():
        def get_students():
            response = requests.get(f"{API_BASE_URL}/student")
            if response.status_code == 200:
                set_students(response.json())

        return get_students

    use_effect(fetch_students(), [])

    # Handle student selection & navigate to student page
    def handle_student_selection(event):
        student_id = event["target"]["value"]
        if student_id:
            set_page("student_page", student_id = student_id)

    return html.div(
        html.h1("Create/Edit/Delete Course Evaluations"),

        # Student Dropdown (Navigates on Selection)
        html.label("Select Student: "),
        html.select(
            {"onChange": handle_student_selection},
            html.option({"value": ""}, "Select a student"),
            [html.option({"value": student["student_id"]}, student["student_name"]) for student in students]
        ),

        html.br(),
        html.button({"on_click": lambda event: set_page("home")}, "Back to Home"),
    )


@component
def StudentPage(set_page, student_id):
    courses, set_courses = use_state([])

    # Fetch courses for the selected student
    def fetch_courses():
        def get_courses():
            response = requests.get(f"{API_BASE_URL}/enrollment/{student_id}")
            if response.status_code == 200:
                set_courses(response.json())

        return get_courses

    use_effect(fetch_courses(), [student_id])
    curr = sqlite3.connect("evaluations.db")
    name = curr.execute(f"SELECT student_name FROM student WHERE student_id = {student_id}").fetchone()[0]

    def handle_course_selection(event):
        section_id = event["target"]["value"]
        if section_id:
            set_page("student_section_page", student_id = student_id, section_id = section_id)

    return html.div(
        html.h1(f"Create/Edit/Delete Evaluations for {name}, Student_ID: {student_id}"),

        # Course Dropdown
        html.label("Select Course: "),

        # html.select(
        #     {"onChange": lambda event: handle_course_selection},
        #     html.option({"value": ""}, "Select a course"),
        #     [html.option({"value": course['student_id']}, course['section_id']) for course in courses]
        # ),
        html.select(
            {
                "onChange": handle_course_selection,
                "value": ""  # Ensure the default value is the placeholder option
            },
            html.option({"value": "", "disabled": True, "selected": True}, "Select a course"),
            # Force selection placeholder
            [html.option({"value": course['section_id']}, course['section_id']) for course in courses]
        ),

    html.br(),
        html.button({"on_click": lambda event: set_page("home")}, "Back to Home")
    )

@component
def StudentSectionPage(set_page, student_id, section_id):
    evaluations, set_evaluations = use_state([])

    def fetch_evaluations():
        def get_evaluations():
            response = requests.get(f"{API_BASE_URL}/evaluations/{student_id}/{section_id}")
            if response.status_code == 200:
                set_evaluations(response.json())

        return get_evaluations

    use_effect(fetch_evaluations(), [student_id, section_id])
    if len(evaluations) == 1:
        eval_number = evaluations[0]["evaluation_number"]

        evaluation = evaluations[0]["evaluation"]
        try:
            evaluation = json.loads(json.dumps(evaluation))
            evaluation = evaluation.replace("'", '"')
            evaluation = json.loads(evaluation)
            print(evaluation)
            grade = evaluation["grade"]
            would_take_again = evaluation["would_take_again"]
            quality_rating = evaluation["quality_rating"]
            difficulty_rating = evaluation["difficulty_rating"]
            organization_rating = evaluation["organization_rating"]
            eval_tags = evaluation["tags"]
            comments = evaluation["comments"]

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    # Function to delete an evaluation
    def handle_delete_evaluation(evaluation_number):
        response = requests.delete(f"{API_BASE_URL}/evaluations/{evaluation_number}")
        if response.status_code == 200:
            set_evaluations([])  # Clear state to reflect deletion
            set_page("home")
        else:
            print("Error deleting evaluation")

    curr = sqlite3.connect("evaluations.db")
    name = curr.execute(f"SELECT student_name FROM student WHERE student_id = {student_id}").fetchone()[0]

    return html.div(
        html.h1(f"Create/Edit/Delete Evaluation of {section_id} for {name}, Student_ID: {student_id}"),

        # If no evaluations exist, show Create Evaluation button
        html.div(
            html.p("There is currently no evaluation for this student in this section. Would you like to create one?"),
            html.br(),
            html.button(
                {"on_click": lambda event: set_page("create_evaluation", student_id = student_id, section_id = section_id)},
                "Create Evaluation"
            )
        ) if (len(evaluations) != 1) else html.div(
            html.b(f"Evaluation # {eval_number}"),
            html.br(),

            html.b(f"Grade Received:"),
            html.p(f"{grade}"),

            html.b(f"Would Take Again?"),
            html.p(f"{would_take_again}"),

            html.b("Ratings"),
            html.br(),
            html.p(f"Quality: {quality_rating}"),
            html.p(f"Difficulty: {difficulty_rating}"),
            html.p(f"Organization: {organization_rating}"),

            html.b("Tags:"),
            html.ul([html.li(tag) for tag in eval_tags]),

            html.b("Comments:"),
            html.p(f"{comments}"),
            html.br(),
            html.button(
                {"on_click": lambda event: set_page("edit_evaluation", student_id = student_id, section_id = section_id, eval_number = eval_number)},
                "Edit Evaluation"
            ),
            html.button(
                {"on_click": lambda event: handle_delete_evaluation(eval_number)},
                "Delete Evaluation"
            ),
            html.br()
        ),

        html.br(),
        html.button({"on_click": lambda event: set_page("home")}, "Back to Home")
    )



@component
def CreateEvaluation(set_page, student_id, section_id):
    grade, set_grade = use_state("")      # grade received
    would_take_again, set_would_take_again = use_state(None)        # boolean would take again
    # multiple ratings
    quality_rating, set_quality_rating = use_state(None)
    difficulty_rating, set_difficulty_rating = use_state(None)
    organization_rating, set_organization_rating = use_state(None)
    selected_tags, set_selected_tags = use_state([])    # select tags
    comments, set_comments = use_state("")

    # Validate ratings to ensure it's a float between 1.0 and 5.0
    def validate_quality_rating(event):
        try:
            value = float(event["target"]["value"])
            if 1.0 <= value <= 5.0:
                set_quality_rating(value)
            else:
                print("Rating must be between 1.0 and 5.0")
        except ValueError:
            print("Please enter a valid float between 1.0 and 5.0")
    def validate_difficulty_rating(event):
        try:
            value = float(event["target"]["value"])
            if 1.0 <= value <= 5.0:
                set_difficulty_rating(value)
            else:
                print("Rating must be between 1.0 and 5.0")
        except ValueError:
            print("Please enter a valid float between 1.0 and 5.0")
    def validate_organization_rating(event):
        try:
            value = float(event["target"]["value"])
            if 1.0 <= value <= 5.0:
                set_organization_rating(value)
            else:
                print("Rating must be between 1.0 and 5.0")
        except ValueError:
            print("Please enter a valid float between 1.0 and 5.0")

    # Handle tags selection
    def handle_tag_change(event, tag):
        if event["target"]["checked"]:
            set_selected_tags(lambda prev_tags: prev_tags + [tag] if tag not in prev_tags else prev_tags)
        else:
            set_selected_tags(lambda prev_tags: [t for t in prev_tags if t != tag])

    # Handle form submission
    def handle_submit():
        # Here, we would send a POST request to the backend with the evaluation data.
        evaluation_data = {
            "student_id": student_id,
            "section_id": section_id,
            "grade": grade,
            "would_take_again": would_take_again,
            "quality_rating": quality_rating,
            "difficulty_rating": difficulty_rating,
            "organization_rating": organization_rating,
            "tags": selected_tags,
            "comments": comments
        }
        # print("Evaluation Data:", evaluation_data)
        set_page("home")
        # Send data to API
        response = requests.post(f"{API_BASE_URL}/create_evaluation", json=evaluation_data)
        if response.status_code == 200:
            set_page("student_page", student_id = student_id)

    curr = sqlite3.connect("evaluations.db")
    name = curr.execute(f"SELECT student_name FROM student WHERE student_id = {student_id}").fetchone()[0]

    def GradeDropdown():
        return html.select(
            {
                "value": grade,  # Default value is an empty string
                "onChange": lambda event: set_grade(event["target"]["value"]),
            },
            html.option({"value": "", "disabled": True, "selected": True}, "Grade"),  # Placeholder
            *[html.option({"value": grade}, grade) for grade in grades],
        )

    def render_tags():
        return html.div(
            *[
                html.div(
                    html.label(tag),
                    html.input(
                        {
                            "type": "checkbox",
                            "value": tag,
                            "on_change": lambda e, t=tag: handle_tag_change(e, t),  # Properly pass event and tag
                        }
                    ),
                )
                for tag in tags
            ]
        )

    return html.div(
        html.h1(f"Create Evaluation of {section_id} for {name}, Student_ID: {student_id}"),

        # Grade Dropdown
        html.label("Grade Received: "),
        # html.select(
        #     {
        #         "value": grade,  # Default value is an empty string
        #         "onChange": lambda event: set_grade(event["target"]["value"]),
        #     },
        #     [html.option({"value": grade}, grade) for grade in grades]
        # ),
        GradeDropdown(),
        html.br(),

        # Would take again question
        html.label("Would Take Again? "),
        html.input(
            {"type": "radio", "name": "would_take_again", "value": "Yes",
             "on_change": lambda e: set_would_take_again("Yes")}
        ),
        html.label("Yes"),
        html.input(
            {"type": "radio", "name": "would_take_again", "value": "No",
             "on_change": lambda e: set_would_take_again("No")}
        ),
        html.label("No"),
        html.br(),

        # Rating input (float check)
        html.p("Rating (1.0 to 5.0): "),
        html.label("Quality"),
        html.input(
            {"type": "text", "value": quality_rating or "", "on_change": validate_quality_rating}
        ),
        html.br(),
        html.label("Difficulty"),
        html.input(
            {"type": "text", "value": difficulty_rating or "", "on_change": validate_difficulty_rating}
        ),
        html.br(),
        html.label("Organization"),
        html.input(
            {"type": "text", "value": organization_rating or "", "on_change": validate_organization_rating}
        ),
        html.br(),
        html.br(),

        # Tags selection (checkboxes)
        html.p("Select Tags"),
        render_tags(),
        html.br(),

        # Comments textbox
        html.label("Comments: "),
        html.textarea(
            {"value": comments, "on_change": lambda e: set_comments(e["target"]["value"])},
            html.br(),
        ),
        html.br(),

        # Submit button
        html.button({"on_click": lambda e: handle_submit()}, "Submit Evaluation"),

        html.br(),
        html.button({"on_click": lambda event: set_page("home")}, "Back to Home")
    )


@component
def Page2(set_page):
    return html.div(
        html.h1("Generate Evaluation Reports"),
        html.button({"on_click": lambda event: set_page("generate_student_report")}, "Report by Student"),
        html.button({"on_click": lambda event: set_page("generate_professor_report")}, "Report by Professor"),
        html.button({"on_click": lambda event: set_page("generate_course_evaluation_report")}, "Report by Courses"),
        html.button({"on_click": lambda event: set_page("home")}, "Back to Home"),
    )


@component
def GenerateStudentReport(set_page):
    students, set_students = use_state([])

    # Fetch students when component mounts
    def fetch_students():
        def get_students():
            response = requests.get(f"{API_BASE_URL}/student")
            if response.status_code == 200:
                set_students(response.json())

        return get_students

    use_effect(fetch_students(), [])

    # Handle student selection & navigate to student page
    def handle_student_selection(event):
        student_id = event["target"]["value"]
        if student_id:
            set_page("student_report", student_id = student_id)

    return html.div(
        html.h1("Generate Student Report"),

        # Student Dropdown (Navigates on Selection)
        html.label("Select Student: "),
        html.select(
            {"onChange": handle_student_selection},
            html.option({"value": ""}, "Select a student"),
            [html.option({"value": student["student_id"]}, student["student_name"]) for student in students]
        ),

        html.br(),
        html.button({"on_click": lambda event: set_page("home")}, "Back to Home"),
    )


@component
def StudentReport(set_page, student_id):
    curr = sqlite3.connect("evaluations.db")
    name = curr.execute(f"SELECT student_name FROM student WHERE student_id = {student_id}").fetchone()[0]

    gpa, evals, no_evals = sp.student_report(student_id)

    def listed_evaluation(evaluation_dict):
        return html.li(
            html.b(f"Evaluation #{evaluation_dict['evaluation_number']}, {evaluation_dict['section_id']}: "),
            html.span(evaluation_dict['course_name']), html.span(" with Professor "),
            html.span(evaluation_dict['professor_name']), html.br(),

            html.b("Grade Received: "), html.span(evaluation_dict['evaluation']['grade']), html.span(", "),
            html.b("Would Take Again? "), html.span(evaluation_dict['evaluation']['would_take_again']), html.br(),

            html.b("Quality Rating: "), html.span(evaluation_dict['evaluation']['quality_rating']), html.span(", "),
            html.b("Difficulty Rating: "), html.span(evaluation_dict['evaluation']['difficulty_rating']), html.span(", "),
            html.b("Organization Rating: "), html.span(evaluation_dict['evaluation']['organization_rating']), html.br(),

            html.b("Tags: "), html.span(', '.join(evaluation_dict['evaluation']['tags'])), html.br(),

            html.b("Comment: "), html.span(evaluation_dict['evaluation']['comments']), html.br(), html.br()
        )

    return html.div(
        html.h1(f"Student Report for {name}, Student_ID: {student_id}"),

        # Fill in report info for students
        html.h3("GPA: "), html.span(gpa), html.br(),  # GPA

        # fill in evaluations
        html.h3("Evaluated Courses:"),
        html.ul([listed_evaluation(evaluation) for evaluation in evals]),

        # list non-evaluations
        html.h3("Courses Not Yet Evaluated:"),
        html.ul([html.li(
            html.b(no_eval['section_id'] + ": "),
            html.span(no_eval['course_name']), html.span(" with Professor "), html.span(no_eval['professor_name']),
        ) for no_eval in no_evals]),

        html.button({"on_click": lambda event: set_page("home")}, "Back to Home"),
    )


@component
def GenerateProfessorReport(set_page):
    professors, set_professors = use_state([])

    # Fetch students when component mounts
    def fetch_professors():
        def get_professors():
            response = requests.get(f"{API_BASE_URL}/professor")
            if response.status_code == 200:
                set_professors(response.json())

        return get_professors

    use_effect(fetch_professors(), [])

    # Handle professor selection & navigate to professor page
    def handle_professor_selection(event):
        professor_id = event["target"]["value"]
        if professor_id:
            set_page("professor_report", professor_id = professor_id)

    return html.div(
        html.h2("Generate Professor Report"),

        # Professor Dropdown (Navigates on Selection)
        html.label("Select Professor: "),
        html.select(
            {"onChange": handle_professor_selection},
            html.option({"value": ""}, "Select a professor"),
            [html.option({"value": professor["professor_id"]}, professor["professor_name"]) for professor in professors]
        ),

        html.br(),
        html.button({"on_click": lambda event: set_page("home")}, "Back to Home"),
    )


@component
def ProfessorReport(set_page, professor_id):
    curr = sqlite3.connect("evaluations.db")
    name = curr.execute(f"SELECT professor_name FROM professors WHERE professor_id = {professor_id}").fetchone()[0]

    report = sp.professor_report(professor_id)

    return html.div(
        html.h1(f"Report for Professor {name}, Professor_ID: {professor_id}"),

        # REPORT STRUCTURE
        # report={
        #     'gpa': gpa,
        #     'quality_rating': quality, 'difficulty_rating': difficulty, 'organization_rating': organization,
        #     'tags': tags,
        #     'comments': comments
        # }

        # Fill in report info for professor
        html.h3("Average GPA: "), html.span(report['gpa']), html.br(),   # GPA

        html.h3("Ratings:"),
        html.ul(
            html.b("Quality Rating: "), html.span(report['quality_rating']), html.br(),
            html.b("Difficulty Rating: "), html.span(report['difficulty_rating']), html.br(),
            html.b("Organization Rating: "), html.span(report['organization_rating']), html.br(),
        ),

        html.h3("Tags:"),
        html.ul([html.li(tag) for tag in report['tags']]),

        html.h3("Comments:"),
        html.ul([html.li(comment) for comment in report['comments']]),

        html.button({"on_click": lambda event: set_page("home")}, "Back to Home"),
    )


@component
def GenerateCourseEvaluationReport(set_page):
    courses, set_courses = use_state([])

    # Fetch courses when component mounts
    def fetch_courses():
        def get_courses():
            response = requests.get(f"{API_BASE_URL}/course")
            if response.status_code == 200:
                set_courses(response.json())

        return get_courses

    use_effect(fetch_courses(), [])

    # Handle professor selection & navigate to professor page
    def handle_course_selection(event):
        course_id = event["target"]["value"]
        if course_id:
            set_page("course_report_type", course_id = course_id)

    return html.div(
        html.h1("Generate Course Report"),

        # Course Dropdown (Navigates on Selection)
        html.label("Select a Course: "),
        html.select(
            {"onChange": handle_course_selection},
            html.option({"value": ""}, "Select a course"),
            [html.option({"value": course["course_id"]}, course["course_name"]) for course in courses]
        ),

        html.br(),
        html.button({"on_click": lambda event: set_page("home")}, "Back to Home"),
    )


@component
def CourseReportType(set_page, course_id):
    curr = sqlite3.connect("evaluations.db")
    name = curr.execute("SELECT course_name FROM courses WHERE course_id = ?", (course_id,)).fetchone()[0]

    sections, set_sections = use_state([])

    # Fetch sections for the selected course
    def fetch_sections():
        def get_sections():
            response = requests.get(f"{API_BASE_URL}/section/{course_id}")
            if response.status_code == 200:
                set_sections(response.json())

        return get_sections

    use_effect(fetch_sections(), [course_id])

    def handle_section_selection(event):
        section_id = event["target"]["value"]
        if section_id:
            set_page("section_report", course_id=course_id, section_id=section_id)

    return html.div(
        html.h1(f"Generate Course Report for {course_id}: {name}"),

        # Section Dropdown (Navigates on Selection)
        html.label("Select a Section: "),
        html.select(
            {"onChange": handle_section_selection},
            html.option({"value": ""}, "Select a section"),
            [html.option({"value": section["section_id"]}, section["section_id"]) for section in sections]
        ),

        html.br(),
        html.button({"on_click": lambda event: set_page("course_report", course_id=course_id)}, "Overall Course Report"),
        html.br(),
        html.button({"on_click": lambda event: set_page("home")}, "Back to Home"),
    )


@component
def SectionReport(set_page, course_id, section_id):
    curr = sqlite3.connect("evaluations.db")
    course_name = curr.execute("SELECT course_name FROM courses WHERE course_id = ?", (course_id,)).fetchone()[0]
    professor_name = curr.execute("SELECT professor_name FROM professors NATURAL JOIN sections WHERE section_id = ?", (section_id,)).fetchone()[0]

    report = sp.section_report(section_id)

    return html.div(
        html.h1(f"Report for {section_id}: {course_name}"),
        # add professor & course name at top of page
        html.h2(f"{course_name} with Professor {professor_name}"),

        # REPORT STRUCTURE
        # report={
        #     'gpa': gpa, 'take_again': would_take_again,
        #     'quality_rating': quality, 'difficulty_rating': difficulty, 'organization_rating': organization,
        #     'tags': tags,
        #     'comments': comments
        # }
        # Fill in report info for course section
        html.h3("Average GPA: "), html.span(report['gpa']), html.br(),  # GPA

        html.h3("Would Take Again: "), html.span(str(report['take_again']) + "%"), html.br(),     # Would take again

        html.h3("Ratings:"),
        html.ul(
            html.b("Quality Rating: "), html.span(report['quality_rating']), html.br(),
            html.b("Difficulty Rating: "), html.span(report['difficulty_rating']), html.br(),
            html.b("Organization Rating: "), html.span(report['organization_rating']), html.br(),
        ),

        html.h3("Tags:"),
        html.ul([html.li(tag) for tag in report['tags']]),

        html.h3("Comments:"),
        html.ul([html.li(comment) for comment in report['comments']]),

        html.button({"on_click": lambda event: set_page("course_report_type", course_id=course_id)}, "Course Report Type"),
        html.button({"on_click": lambda event: set_page("home")}, "Back to Home"),
    )


@component
def CourseReport(set_page, course_id):
    curr = sqlite3.connect("evaluations.db")
    name = curr.execute("SELECT course_name FROM courses WHERE course_id = ?", (course_id,)).fetchone()[0]

    report = sp.course_report(course_id)

    return html.div(
        html.h1(f"Overall Report for {course_id}: {name}"),

        # REPORT STRUCTURE
        # report={
        #     'gpa': gpa, 'take_again': would_take_again,
        #     'quality_rating': quality, 'difficulty_rating': difficulty, 'organization_rating': organization,
        #     'tags': tags,
        #     'comments': comments
        # }
        # Fill in report info for overall course
        html.h3("Average GPA: "), html.span(report['gpa']), html.br(),  # GPA

        html.h3("Would Take Again: "), html.span(str(report['take_again']) + "%"), html.br(),  # Would take again

        html.h3("Ratings:"),
        html.ul(
            html.b("Quality Rating: "), html.span(report['quality_rating']), html.br(),
            html.b("Difficulty Rating: "), html.span(report['difficulty_rating']), html.br(),
            html.b("Organization Rating: "), html.span(report['organization_rating']), html.br(),
        ),

        html.h3("Tags:"),
        html.ul([html.li(tag) for tag in report['tags']]),

        html.h3("Comments:"),
        html.ul([html.li(comment) for comment in report['comments']]),

        html.button({"on_click": lambda event: set_page("course_report_type", course_id=course_id)}, "Course Report Type"),
        html.button({"on_click": lambda event: set_page("home")}, "Back to Home"),
    )


@component
def App():
    current_page, set_page = use_state("home")
    selected_student, set_selected_student = use_state(None)
    selected_section, set_selected_section = use_state(None)
    selected_professor, set_selected_professor = use_state(None)
    selected_course, set_selected_course = use_state(None)

    # Wrapper to allow passing extra parameters
    def navigate(page, student_id=None, section_id=None, professor_id=None, course_id=None):
        set_selected_student(student_id)
        set_selected_section(section_id)
        set_selected_professor(professor_id)
        set_selected_course(course_id)
        set_page(page)

    if current_page == "page1":
        return Page1(navigate)
    elif current_page == "student_page" and selected_student:
        return StudentPage(navigate, student_id = selected_student)
    elif current_page == "student_section_page" and selected_student and selected_section:
        return StudentSectionPage(navigate, student_id = selected_student, section_id = selected_section)
    elif current_page == "create_evaluation" and selected_student and selected_section:
        return CreateEvaluation(navigate, student_id = selected_student, section_id = selected_section)
    elif current_page == "page2":
        return Page2(navigate)
    elif current_page == "generate_student_report":
        return GenerateStudentReport(navigate)
    elif current_page == "student_report" and selected_student:
        return StudentReport(navigate, student_id = selected_student)
    elif current_page == "generate_professor_report":
        return GenerateProfessorReport(navigate)
    elif current_page == "professor_report" and selected_professor:
        return ProfessorReport(navigate, professor_id = selected_professor)
    elif current_page == "generate_course_evaluation_report":
        return GenerateCourseEvaluationReport(navigate)
    elif current_page == "course_report_type" and selected_course:
        return CourseReportType(navigate, course_id = selected_course)
    elif current_page == "course_report" and selected_course:
        return CourseReport(navigate, course_id = selected_course)
    elif current_page == "section_report" and selected_course and selected_section:
        return SectionReport(navigate, course_id = selected_course, section_id = selected_section)
    else:
        return Home(navigate)


# Configure ReactPy to work with Flask
configure(app, App)

if __name__ == "__main__":
    app.run(debug=True, port=3000)
