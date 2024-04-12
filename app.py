# USERNAME: umakscheduler
# PASSWORD: Adminschedule123

from flask import Flask, render_template, redirect, request, session, url_for
from flask_session import Session
from werkzeug.utils import secure_filename
import os
import pypyodbc as odbc
import process_excel as pe

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

app.config["UPLOAD_FOLDER"] = "static/files/"
ALLOWED_EXTENSIONS = {'xlsx'}
Session(app)

server = 'umakclassscheduler.database.windows.net'
database = 'SchedulerDB'
connString = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:umakscheduler.database.windows.net,1433;Database='+database+';Uid=umakscheduler;Pwd=Adminschedule123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

@app.route('/')
def home():
    if 'userId' not in session:
        return redirect(url_for('login')) # IF: Not logged in, redirect to login page

    query = "SELECT * FROM Professors"
    return executeQuery(query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        currentEmployeeId = request.form['employeeId']
        currentPassword = request.form['password']
        query = f"SELECT * FROM Professors WHERE employeeId = {currentEmployeeId} AND employeePassword = '{currentPassword}'"
        result = executeQuery(query)
        
        if result:
            if currentEmployeeId != 0000 and currentPassword != 'admin':
                session["userId"] = currentEmployeeId
                return redirect(url_for('index'))
            
            # IF: User is 'admin': proceed to Admin Portal
            session['userId'] = '0000'
            return redirect(url_for('admin'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_EmployeeId = request.form['employeeId']
        new_EmployeeName = request.form['employeeName']
        new_EmployeePassword = request.form['password']

        checkQuery = f"SELECT * FROM Professors WHERE employeeId = {new_EmployeeId}"
        insertQuery = f"INSERT INTO Professors (employeeId, employeeName, employeePassword, employeeSchedule) VALUES ({new_EmployeeId}, '{new_EmployeeName}', '{new_EmployeePassword}', 'Incomplete')"
        insertHonorariumToken = f"INSERT INTO Courses (courseId, courseName, courseYear, courseUnits, professorId) VALUES ('{'HT' + new_EmployeeId}', 'Honorarium Time', '', 0, {new_EmployeeId})"
        insertVacantToken = f"INSERT INTO Courses (courseId, courseName, courseYear, courseUnits, professorId) VALUES ('{'VT' + new_EmployeeId}', 'Vacant Time', '', 0, {new_EmployeeId})"
        checkResult = executeQuery(checkQuery)

        if checkResult: # IF: an existing professorId is detected -> return redirect('/register')
            return redirect(url_for('register'))
        else:
            executeQuery(insertQuery)
            executeQuery(insertHonorariumToken)
            executeQuery(insertVacantToken)
            print("TEST (Register Page): You have inserted into the database!")
            return redirect(url_for('login'))
 
    return render_template('register.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'userId' not in session:
        return redirect(url_for("login")) # IF: Not logged in, redirect to login page
    
    else:
        currentId = int(session['userId'])
        getProfessorsQuery = "SELECT employeeId, employeeName, employeeSchedule FROM Professors WHERE employeeId != 0000"
        professorData = executeQuery(getProfessorsQuery)

        getCoursesQuery = "SELECT * FROM Courses"
        courseData = executeQuery(getCoursesQuery)

        getCourseSchedulesQuery = "SELECT * FROM CourseSchedules"
        scheduleData = executeQuery(getCourseSchedulesQuery)

        if request.method == 'POST':
            action = request.form['btn']

            if action == 'logout':
                session.pop('userId', 0)
                return redirect("/login")

            if action == 'submitInquiry':
                inquirySubject = request.form['messageSubject']
                inquiryMessage = request.form['message']
                insertInquiryQuery = f"INSERT INTO ProfessorInquiries (professorId, inqSubject, inqMessage, inqStatus) VALUES ({currentId}, '{inquirySubject}', '{inquiryMessage}', 'Unresolved')"
                executeQuery(insertInquiryQuery)
                return "<script>alert('Your response was recorded.')</script>"

        return render_template("index.html",
        current_professor=currentId,
        professorData=professorData,
        courseData=courseData,
        scheduleData=scheduleData)

# CODE BLOCK: Admin Page
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'userId' not in session or session['userId'] != '0000':
        return redirect(url_for("login")) # IF: Not logged in, redirect to login page
    
    else:
        getProfessorsQuery = "SELECT employeeId, employeeName, employeeSchedule FROM Professors WHERE employeeId != 0000"
        professorData = executeQuery(getProfessorsQuery)

        getCoursesQuery = "SELECT * FROM Courses"
        courseData = executeQuery(getCoursesQuery)

        getCourseSchedulesQuery = "SELECT * FROM CourseSchedules"
        scheduleData = executeQuery(getCourseSchedulesQuery)

        current_professor = 0 # INIT: No value needed
        scheduleMode = 0
        
        if request.method == "POST":
            action = request.form['btn']

            if action == 'backToAdmin':
                return redirect("/admin")

            if action == 'logout':
                session.pop('userId', 0)
                return redirect("/login")

            if action == 'addCourse':
                newCourseCode = request.form['courseCode'].upper()
                newCourseName = request.form['courseName'].upper()
                newCourseYear = request.form['courseYear']
                newCourseUnits = request.form['courseUnits']
                checkQuery = f"SELECT * FROM Courses WHERE courseId = '{newCourseCode}'"
                insertQuery = f"INSERT INTO Courses (courseId, courseName, courseYear, courseUnits) VALUES ('{newCourseCode}', '{newCourseName}', '{newCourseYear}', {newCourseUnits})"
                checkResult = executeQuery(checkQuery)

                if checkResult:
                    print("TEST (Admin Page): The course already exists!") # TEST: Test Validation
                else:
                    executeQuery(insertQuery)
                    print("TEST (Admin Page): You have inserted into the database!") # TEST: Test Validation
                    professorData = executeQuery(getProfessorsQuery)
                    courseData = executeQuery(getCoursesQuery)
                    scheduleData = executeQuery(getCourseSchedulesQuery)
                    return render_template('admin.html',
                        professorData=professorData,
                        courseData=courseData,
                        scheduleData=scheduleData,
                        current_professor=int(current_professor),
                        scheduleMode=scheduleMode)

            if action == 'checkProfessorSchedule':
                scheduleMode = 1
                try:
                    current_professor = request.form['professorDetails']
                except:
                    return redirect(url_for('admin'))

            if action == 'setHonorariumVacantTime':
                scheduleMode = 2
                try:
                    current_professor = request.form['professorDetails']
                except:
                    return redirect(url_for('admin'))

            if action == 'manageCourse':
                scheduleMode = 1
                current_course = request.form['currentCourse'].upper()
                current_professor = request.form['professorDetails']
                newCourseSection = request.form['courseSection'].upper()
                newStartTime = request.form['startTime']
                newEndTime = request.form['endingTime']
                newDayOfWeek = request.form['dayOfWeek']
                newRoom = request.form['courseRoom'].upper()

                ifProfessorExists = False
                ifNoProfessorExists = False

                for courses in courseData:
                    if courses[0] == current_course and courses[4] == int(current_professor):
                        ifProfessorExists = True
                        break

                for courses in courseData:
                    if courses[0] == current_course and courses[4] is None:
                        ifNoProfessorExists = True
                        break

                insertScheduleQuery = f"INSERT INTO CourseSchedules (courseId, professorId, room, section, dayOfWeek, startTime, endTime) VALUES ('{current_course}', {current_professor}, '{newRoom}', '{newCourseSection}', '{newDayOfWeek}', '{newStartTime}', '{newEndTime}')"
                updateCourseQuery = f"UPDATE Courses SET professorId = {current_professor} WHERE courseId = '{current_course}'"
                checkIfSameTime = f"SELECT * FROM CourseSchedules WHERE startTime = '{newStartTime}' AND endTime = '{newEndTime}' and dayOfWeek = '{newDayOfWeek}'"

                checkExceeds3Hours = f"""
                                        SELECT professorId, 
                                            SUM(DATEDIFF(MINUTE, startTime, endTime) / 60.0) AS totalScheduledHours
                                        FROM CourseSchedules
                                        WHERE professorId = {int(current_professor)}
                                        AND courseId = '{current_course}'
                                        GROUP BY professorId
                                        HAVING SUM(DATEDIFF(MINUTE, startTime, endTime) / 60.0) >= 3;
                                        """
                
                if (scheduleData): # IF: Records exist in CourseSchedules Table -> proceed with logic
                    
                    if (ifProfessorExists == True): # IF: Current professor being assigned is assigned to the current_course -> proceed with logic
                        if (executeQuery(checkIfSameTime)):
                            print("\n\nTEST (Admin Page): There is a subject already assigned in the same time!\n\n") # TEST: Test Validation
                        else:
                            if (executeQuery(checkExceeds3Hours)):
                                print("\n\nTEST (Admin Page): Already has 3 hours in slot!\n\n") # TEST: Test Validation
                            else:
                                print("\n\nTEST (Admin Page): Inserted into the database!\n\n") # TEST: Test Validation
                                executeQuery(insertScheduleQuery)
                                professorData = executeQuery(getProfessorsQuery)
                                courseData = executeQuery(getCoursesQuery)
                                scheduleData = executeQuery(getCourseSchedulesQuery)
                                return render_template('admin.html',
                                    professorData=professorData,
                                    courseData=courseData,
                                    scheduleData=scheduleData,
                                    current_professor=int(current_professor),
                                    scheduleMode=scheduleMode)

                    else:
                        if (ifNoProfessorExists):
                            if (executeQuery(checkIfSameTime)):
                                print("\n\nTEST (Admin Page): This subject is already assigned in the same time!\n\n") # TEST: Test Validation
                            else:
                                if (executeQuery(checkExceeds3Hours)):
                                    print("\n\nTEST (Admin Page): Already has 3 hours in slot!\n\n") # TEST: Test Validation
                                else:
                                    print("\n\nTEST (Admin Page): Inserted into the database!\n\n") # TEST: Test Validation
                                    executeQuery(insertScheduleQuery)
                                    executeQuery(updateCourseQuery)
                                    professorData = executeQuery(getProfessorsQuery)
                                    courseData = executeQuery(getCoursesQuery)
                                    scheduleData = executeQuery(getCourseSchedulesQuery)
                                    return render_template('admin.html',
                                        professorData=professorData,
                                        courseData=courseData,
                                        scheduleData=scheduleData,
                                        current_professor=int(current_professor),
                                        scheduleMode=scheduleMode)
                        else:
                            print("\n\nTEST (Admin Page): There is already a professor assigned in this course!\n\n") # TEST: Test Validation

                else: # ELSE: If no records exist, insert new schedule into the table
                    executeQuery(insertScheduleQuery)
                    executeQuery(updateCourseQuery)
                    professorData = executeQuery(getProfessorsQuery)
                    courseData = executeQuery(getCoursesQuery)
                    scheduleData = executeQuery(getCourseSchedulesQuery)
                    return render_template('admin.html',
                        professorData=professorData,
                        courseData=courseData,
                        scheduleData=scheduleData,
                        current_professor=int(current_professor),
                        scheduleMode=scheduleMode)

            if action == 'insertHonorariumVacant':
                scheduleMode = 2
                current_professor = request.form['professorDetails']
                otherScheduleType = request.form['honorVacantChoice']
                honorVacantDayOfWeek = request.form['honorVacantDayOfWeek']
                honorVacantStartTime = request.form['honorVacantStartTime']
                honorVacantEndTime = request.form['honorVacantEndingTime']
                
                getHonorariumID = f"SELECT courseId FROM Courses where courseId = '{'HT' + current_professor}'"
                getVacantID = f"SELECT courseId FROM Courses where courseId = '{'VT' + current_professor}'"
                honorIDquery = executeQuery(getHonorariumID)
                vacantIDquery = executeQuery(getVacantID)

                if otherScheduleType == 'Honorarium Time':
                    choiceID = honorIDquery[0][0]
                
                if otherScheduleType == 'Vacant Time':
                    choiceID = vacantIDquery[0][0]

                insertHonorVacantQuery = f"INSERT INTO CourseSchedules (courseId, professorId, room, section, dayOfWeek, startTime, endTime) VALUES ('{choiceID}', {current_professor}, '', '', '{honorVacantDayOfWeek}', '{honorVacantStartTime}', '{honorVacantEndTime}')"
                checkSameHonorVacantTime = f"SELECT * FROM CourseSchedules WHERE startTime = '{honorVacantStartTime}' AND endTime = '{honorVacantEndTime}' AND dayOfWeek = '{honorVacantDayOfWeek}'"
                checkExceedsHourMins = f"""
                                        SELECT professorId, 
                                            SUM(DATEDIFF(MINUTE, startTime, endTime) / 60.0) AS totalScheduledHours
                                        FROM CourseSchedules
                                        WHERE professorId = {int(current_professor)}
                                        AND courseId = '{choiceID}'
                                        AND dayOfWeek = '{honorVacantDayOfWeek}'
                                        GROUP BY professorId
                                        HAVING SUM(DATEDIFF(MINUTE, startTime, endTime) / 60.0) >= 1.5;
                                        """

                if scheduleData:
                    if (executeQuery(checkSameHonorVacantTime)):
                        print(f"\n\nTEST (Admin Page): {otherScheduleType} is already assigned in the same time!\n\n") # TEST: Test Validation
                    else:
                        if (executeQuery(checkExceedsHourMins)):
                            print("\n\nTEST (Admin Page): Already has 1.5 hours in slot!\n\n") # TEST: Test Validation
                        else:
                            print("\n\nTEST (Admin Page): Inserted into the database!\n\n") # TEST: Test Validation
                            executeQuery(insertHonorVacantQuery)
                            professorData = executeQuery(getProfessorsQuery)
                            courseData = executeQuery(getCoursesQuery)
                            scheduleData = executeQuery(getCourseSchedulesQuery)
                            return render_template('admin.html',
                                professorData=professorData,
                                courseData=courseData,
                                scheduleData=scheduleData,
                                current_professor=int(current_professor),
                                scheduleMode=scheduleMode)
                else:
                    executeQuery(insertHonorVacantQuery)
                    print("\n\nTEST (Admin Page): Inserted into the database!\n\n") # TEST: Test Validation
                    professorData = executeQuery(getProfessorsQuery)
                    courseData = executeQuery(getCoursesQuery)
                    scheduleData = executeQuery(getCourseSchedulesQuery)
                    return render_template('admin.html',
                        professorData=professorData,
                        courseData=courseData,
                        scheduleData=scheduleData,
                        current_professor=int(current_professor),
                        scheduleMode=scheduleMode)

            if action == "deleteCourse":
                selectedCourseId = request.form["courseToBeDeleted"]
                deleteFromCourses = f"DELETE FROM Courses WHERE courseId = '{selectedCourseId}'"
                deleteFromCourseSchedules = f"DELETE FROM CourseSchedules WHERE courseId = '{selectedCourseId}'"

                # NOTE: Schedules first, then the course information after
                executeQuery(deleteFromCourseSchedules)
                executeQuery(deleteFromCourses)
                professorData = executeQuery(getProfessorsQuery)
                courseData = executeQuery(getCoursesQuery)
                scheduleData = executeQuery(getCourseSchedulesQuery)
                return render_template('admin.html',
                    professorData=professorData,
                    courseData=courseData,
                    scheduleData=scheduleData,
                    current_professor=int(current_professor),
                    scheduleMode=scheduleMode)

            if action == "deleteUser":
                current_professor = request.form['professorDetails']
                deleteProfessorSchedule = f"DELETE FROM CourseSchedules WHERE professorId = {current_professor}"
                deleteHonorariumVacant = f"DELETE FROM Courses WHERE courseId = '{'HT' + current_professor}' or courseId = '{'VT' + current_professor}'"
                deleteProfessor = f"DELETE FROM Professors WHERE employeeId = {current_professor}"
                updateCourses = f"UPDATE Courses SET professorId = '' WHERE professorId = {current_professor}"
                executeQuery(deleteProfessorSchedule)
                executeQuery(deleteHonorariumVacant)
                executeQuery(updateCourses)
                executeQuery(deleteProfessor)
                return redirect(url_for('admin'))
            
            if action == "markComplete":
                current_professor = request.form['professorDetails']
                markCompleteQuery = f"UPDATE Professors SET employeeSchedule = 'Complete' WHERE employeeId = {current_professor}"
                executeQuery(markCompleteQuery)
                professorData = executeQuery(getProfessorsQuery)
                courseData = executeQuery(getCoursesQuery)
                scheduleData = executeQuery(getCourseSchedulesQuery)
                return render_template('admin.html',
                    professorData=professorData,
                    courseData=courseData,
                    scheduleData=scheduleData,
                    current_professor=int(current_professor),
                    scheduleMode=1)

            if action == "markIncomplete":
                current_professor = request.form['professorDetails']
                markIncompleteQuery = f"UPDATE Professors SET employeeSchedule = 'Incomplete' WHERE employeeId = {current_professor}"
                executeQuery(markIncompleteQuery)
                professorData = executeQuery(getProfessorsQuery)
                courseData = executeQuery(getCoursesQuery)
                scheduleData = executeQuery(getCourseSchedulesQuery)
                return render_template('admin.html',
                    professorData=professorData,
                    courseData=courseData,
                    scheduleData=scheduleData,
                    current_professor=int(current_professor),
                    scheduleMode=1)

            if action == "uploadExcel":
                if 'file' not in request.files:
                    return '<script>alert("File not found.");</script>'
                
                file = request.files['file']
                if file.filename == '':
                    return "No selected file."
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    executeQuery(pe.readContents(filename))
                    return '<script>alert("Subjects have been successfully imported.");window.location.href="/admin";</script>'

            if action == "inquiries":
                return redirect(url_for('inquiries'))

        return render_template('admin.html',
                professorData=professorData,
                courseData=courseData,
                scheduleData=scheduleData,
                current_professor=int(current_professor),
                scheduleMode=scheduleMode)

# CODE BLOCK: User Inquiries
@app.route('/admin/inquiries', methods=['GET', 'POST'])
def inquiries():
    if 'userId' not in session or session['userId'] != '0000':
        return redirect(url_for("login")) # IF: Not logged in, redirect to login page
        
    else:
        getInquiriesQuery = "SELECT * FROM ProfessorInquiries"
        inquiryData = executeQuery(getInquiriesQuery)

        getProfessorsQuery = "SELECT employeeId, employeeName, employeeSchedule FROM Professors WHERE employeeId != 0000"
        professorData = executeQuery(getProfessorsQuery)

        if request.method == "POST":
            action = request.form['btn']

            if action == 'logout':
                session.pop('userId', 0)
                return redirect("/login")

            if action == 'backToAdminPage':
                return redirect("/admin")
            
            if action == 'resolveInquiry':
                currentId = int(request.form['currentId'])
                resolveQuery = f"UPDATE ProfessorInquiries SET inqStatus = 'Resolved' WHERE ID = {currentId}"
                executeQuery(resolveQuery)
                inquiryData = executeQuery(getInquiriesQuery)
                professorData = executeQuery(getProfessorsQuery)

            if action == 'denyInquiry':
                currentId = int(request.form['currentId'])
                denyQuery = f"UPDATE ProfessorInquiries SET inqStatus = 'Denied' WHERE ID = {currentId}"
                executeQuery(denyQuery)
                inquiryData = executeQuery(getInquiriesQuery)
                professorData = executeQuery(getProfessorsQuery)

        return render_template('inquiries.html',
        inquiryData=inquiryData,
        professorData=professorData)

# CODE BLOCK: Checking the file extension for import
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# CODE BLOCK: Executing the queries
def executeQuery(checkQuery, params=None):
    conn = odbc.connect(connString)
    cursor = conn.cursor()

    try:
        if params:
            cursor.execute(checkQuery, params)
        else:
            cursor.execute(checkQuery)

        if checkQuery.strip().upper().startswith("SELECT"):
            data = cursor.fetchall()
        else:
            data = None

        conn.commit()

    except odbc.Error as e:
        print(f"ERROR: Problems executing query: {e}")
        conn.rollback()
        data = None

    finally:
        cursor.close()
        conn.close()

    return data

if __name__ == '__main__':
    app.run(debug=True)