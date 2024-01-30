# USERNAME: umakscheduler
# PASSWORD: Adminschedule123

from flask import Flask, render_template, redirect, request, session
from flask_session import Session
import pypyodbc as odbc

app = Flask(__name__)

# NOTE: Session Package is not yet implemented
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

server = 'umakclassscheduler.database.windows.net'
database = 'SchedulerDB'
connString = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:'+server+',1433;Database='+database+';Uid=umakscheduler;Pwd=Adminschedule123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

@app.route('/')
def home():
    if not session.get("employeeId"):
        return redirect("/login") # IF: Not logged in, redirect to login page

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
            session["employeeId"] = request.form.get("employeeId") # Record the Session Variable
            return redirect('/')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_EmployeeId = request.form['employeeId']
        new_EmployeeName = request.form['employeeName']
        new_EmployeePassword = request.form['password']

        checkQuery = f"SELECT * FROM Professors WHERE employeeId = {new_EmployeeId}"
        insertQuery = f"INSERT INTO Professors (employeeId, employeeName, employeePassword) VALUES ({new_EmployeeId}, '{new_EmployeeName}', '{new_EmployeePassword}')"
        checkResult = executeQuery(checkQuery)

        if checkResult: # IF: an existing professorId is detected -> return redirect('/register')
            return redirect('/register')
        else:
            executeQuery(insertQuery)
            print("TEST (Register Page): You have inserted into the database!")

        return redirect("/login")
 
    return render_template('register.html')

# CODE BLOCK: Admin Page
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get("employeeId"):
        return redirect("/login") # IF: Not logged in, redirect to login page
        
    getProfessorsQuery = "SELECT employeeId, employeeName FROM Professors"
    professorData = executeQuery(getProfessorsQuery)

    getCoursesQuery = "SELECT * FROM Courses"
    courseData = executeQuery(getCoursesQuery)

    getCourseSchedulesQuery = "SELECT * FROM CourseSchedules"
    scheduleData = executeQuery(getCourseSchedulesQuery)
    print(scheduleData)

    current_professor = 0 # INIT: No value needed
    
    if request.method == "POST":
        action = request.form['btn']

        if action == 'addCourse':
            newCourseCode = request.form['courseCode'].upper()
            newCourseName = request.form['courseName'].upper()
            newCourseYear = request.form['courseYear']
            newCourseUnits = request.form['courseUnits']
            checkQuery = f"SELECT * FROM Courses WHERE courseId = '{newCourseCode}'"
            insertQuery = f"INSERT INTO Courses (courseId, courseName, courseYear, courseUnits) VALUES ('{newCourseCode}', '{newCourseName}', '{newCourseYear}', {newCourseUnits})"
            checkResult = executeQuery(checkQuery)

            if checkResult:
                return redirect('/admin') # WIP: Add a notification that the courseId specified already exists
            else:
                executeQuery(insertQuery)
                print("TEST (Admin Page): You have inserted into the database!") # TEST: Test Validation
                return redirect('/admin')

        if action == 'checkProfessorSchedule':
            current_professor = request.form['professorDetails']
            print(current_professor)
            return render_template('admin.html',
                professorData=professorData,
                courseData=courseData,
                scheduleData=scheduleData,
                current_professor=int(current_professor))

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
            checkIfSameTime = f"SELECT * FROM CourseSchedules WHERE startTime = '{newStartTime}' AND endTime = '{newEndTime}'"

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
                        print("\n\nTEST (Admin Page): This subject is already assigned in the same time!\n\n") # TEST: Test Validation
                        return redirect('/admin')

                    else:
                        if (executeQuery(checkExceeds3Hours)):
                            print("\n\nTEST (Admin Page): Already has 3 hours in slot!\n\n") # TEST: Test Validation
                            return redirect('/admin')
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
                            return redirect('/admin')

                        else:
                            if (executeQuery(checkExceeds3Hours)):
                                print("\n\nTEST (Admin Page): Already has 3 hours in slot!\n\n") # TEST: Test Validation
                                return redirect('/admin')
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
                        return redirect('/admin')

            else: # ELSE: If no records exist, insert new schedule into the table
                executeQuery(insertScheduleQuery)
                executeQuery(updateCourseQuery)
                return render_template('admin.html',
                    professorData=professorData,
                    courseData=courseData,
                    scheduleData=scheduleData,
                    current_professor=0)

        # WIP: Delete Course Feature
        if action == "deleteCourse":
            selectedCourseId = request.form["courseToBeDeleted"]
            deleteFromCourses = f"DELETE FROM Courses WHERE courseId = '{selectedCourseId}'"
            deleteFromCourseSchedules = f"DELETE FROM CourseSchedules WHERE courseId = '{selectedCourseId}'"

            # NOTE: Schedules first, then the course information after
            executeQuery(deleteFromCourseSchedules)
            executeQuery(deleteFromCourses)

            return redirect('/admin')

    return render_template('admin.html',
        professorData=professorData,
        courseData=courseData,
        scheduleData=scheduleData,
        current_professor=int(current_professor))

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




















































































