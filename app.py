# USERNAME: umakscheduler
# PASSWORD: Adminschedule123

from flask import Flask, render_template, redirect, request, session, url_for
from flask_session import Session
import pypyodbc as odbc

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
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
        getProfessorsQuery = "SELECT employeeId, employeeName, employeeSchedule FROM Professors WHERE employeeId != 0000"
        professorData = executeQuery(getProfessorsQuery)

        getCoursesQuery = "SELECT * FROM Courses"
        courseData = executeQuery(getCoursesQuery)

        getCourseSchedulesQuery = "SELECT * FROM CourseSchedules"
        scheduleData = executeQuery(getCourseSchedulesQuery)

        currentId = int(session['userId'])

        if request.method == 'POST':
            action = request.form['btn']

            if action == 'logout':
                session.pop('userId', 0)
                return redirect("/login")

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
                    return redirect(url_for('admin'))
                else:
                    executeQuery(insertQuery)
                    print("TEST (Admin Page): You have inserted into the database!") # TEST: Test Validation
                    return redirect(url_for('admin'))

            if action == 'checkProfessorSchedule':
                scheduleMode = 1
                current_professor = request.form['professorDetails']
                return render_template('admin.html',
                    professorData=professorData,
                    courseData=courseData,
                    scheduleData=scheduleData,
                    current_professor=int(current_professor),
                    scheduleMode=scheduleMode)

            if action == 'setHonorariumVacantTime':
                scheduleMode = 2
                current_professor = request.form['professorDetails']
                return render_template('admin.html',
                    professorData=professorData,
                    courseData=courseData,
                    scheduleData=scheduleData,
                    current_professor=int(current_professor),
                    scheduleMode=scheduleMode)

            if action == 'manageCourse':
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
                                        AND dayOfWeek = '{newDayOfWeek}'
                                        GROUP BY professorId
                                        HAVING SUM(DATEDIFF(MINUTE, startTime, endTime) / 60.0) >= 3;
                                        """
                
                if (scheduleData): # IF: Records exist in CourseSchedules Table -> proceed with logic
                    
                    if (ifProfessorExists == True): # IF: Current professor being assigned is assigned to the current_course -> proceed with logic
                        if (executeQuery(checkIfSameTime)):
                            print("\n\nTEST (Admin Page): There is a subject already assigned in the same time!\n\n") # TEST: Test Validation
                            return redirect(url_for('admin'))

                        else:
                            if (executeQuery(checkExceeds3Hours)):
                                print("\n\nTEST (Admin Page): Already has 3 hours in slot!\n\n") # TEST: Test Validation
                                return redirect(url_for('admin'))
                            else:
                                print("\n\nTEST (Admin Page): Inserted into the database!\n\n") # TEST: Test Validation
                                executeQuery(insertScheduleQuery)
                                return render_template('admin.html',
                                    professorData=professorData,
                                    courseData=courseData,
                                    scheduleData=scheduleData,
                                    current_professor=0)

                    else:
                        if (ifNoProfessorExists):
                            # NOTE: This if-block needs to be converted into a function for easier debugging
                            if (executeQuery(checkIfSameTime)):
                                print("\n\nTEST (Admin Page): This subject is already assigned in the same time!\n\n") # TEST: Test Validation
                                return redirect(url_for('admin'))

                            else:
                                if (executeQuery(checkExceeds3Hours)):
                                    print("\n\nTEST (Admin Page): Already has 3 hours in slot!\n\n") # TEST: Test Validation
                                    return redirect(url_for('admin'))
                                else:
                                    print("\n\nTEST (Admin Page): Inserted into the database!\n\n") # TEST: Test Validation
                                    executeQuery(insertScheduleQuery)
                                    executeQuery(updateCourseQuery)
                                    return render_template('admin.html',
                                        professorData=professorData,
                                        courseData=courseData,
                                        scheduleData=scheduleData,
                                        current_professor=0)
                        
                        else:
                            print("\n\nTEST (Admin Page): There is already a professor assigned in this course!\n\n") # TEST: Test Validation
                            return redirect(url_for('admin'))

                else: # ELSE: If no records exist, insert new schedule into the table
                    executeQuery(insertScheduleQuery)
                    executeQuery(updateCourseQuery)
                    return render_template('admin.html',
                        professorData=professorData,
                        courseData=courseData,
                        scheduleData=scheduleData,
                        current_professor=0)

            if action == 'insertHonorariumVacant':
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
                        return redirect(url_for('admin'))
                    else:
                        if (executeQuery(checkExceedsHourMins)):
                            print("\n\nTEST (Admin Page): Already has 1.5 hours in slot!\n\n") # TEST: Test Validation
                            return redirect(url_for('admin'))
                        else:
                            print("\n\nTEST (Admin Page): Inserted into the database!\n\n") # TEST: Test Validation
                            executeQuery(insertHonorVacantQuery)
                            return render_template('admin.html',
                                professorData=professorData,
                                courseData=courseData,
                                scheduleData=scheduleData,
                                current_professor=0)
                
                else:
                    executeQuery(insertHonorVacantQuery)
                    print("\n\nTEST (Admin Page): Inserted into the database!\n\n") # TEST: Test Validation
                    return render_template('admin.html',
                                professorData=professorData,
                                courseData=courseData,
                                scheduleData=scheduleData,
                                current_professor=0)

            if action == "deleteCourse":
                selectedCourseId = request.form["courseToBeDeleted"]
                deleteFromCourses = f"DELETE FROM Courses WHERE courseId = '{selectedCourseId}'"
                deleteFromCourseSchedules = f"DELETE FROM CourseSchedules WHERE courseId = '{selectedCourseId}'"

                # NOTE: Schedules first, then the course information after
                executeQuery(deleteFromCourseSchedules)
                executeQuery(deleteFromCourses)
                return redirect(url_for('admin'))

            if action == "deleteUser":
                current_professor = request.form['professorDetails']
                deleteProfessorSchedule = f"DELETE FROM CourseSchedules WHERE professorId = {current_professor}"
                deleteProfessor = f"DELETE FROM Professors WHERE employeeId = {current_professor}"
                updateCourses = f"UPDATE Courses SET professorId = '' WHERE professorId = {current_professor}"
                executeQuery(deleteProfessorSchedule)
                executeQuery(updateCourses)
                executeQuery(deleteProfessor)
                return redirect(url_for('admin'))
            
            if action == "markComplete":
                current_professor = request.form['professorDetails']
                markCompleteQuery = f"UPDATE Professors SET employeeSchedule = 'Complete' WHERE employeeId = {current_professor}"
                executeQuery(markCompleteQuery)
                return redirect(url_for('admin'))
            
            if action == "markIncomplete":
                current_professor = request.form['professorDetails']
                markIncompleteQuery = f"UPDATE Professors SET employeeSchedule = 'Incomplete' WHERE employeeId = {current_professor}"
                executeQuery(markIncompleteQuery)
                return redirect(url_for('admin'))


        print(request.form)

        return render_template('admin.html',
            professorData=professorData,
            courseData=courseData,
            scheduleData=scheduleData,
            current_professor=int(current_professor),
            scheduleMode=scheduleMode)

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




















































































