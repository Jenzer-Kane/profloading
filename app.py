# USERNAME: umakscheduler
# PASSWORD: Adminschedule123

from flask import Flask, render_template, redirect, request, session, url_for
from flask_session import Session
import pypyodbc as odbc
from web_functions import *

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

server = 'umakclassscheduler.database.windows.net'
database = 'SchedulerDB'
connString = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:umakscheduler.database.windows.net,1433;Database='+database+';Uid=umakscheduler;Pwd=Adminschedule123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        currentEmployeeId = request.form['employeeId']
        currentPassword = request.form['password']
        currentProfessorUser = ExistingProfessor(currentEmployeeId, currentPassword)
        result = currentProfessorUser.login_user()

        print(result)
        
        if result == True:
            session["userId"] = currentEmployeeId
            return redirect(url_for('index'))
        elif result == False:
            session['userId'] = '0000'
            return redirect(url_for('admin'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_EmployeeId = request.form['employeeId']
        new_EmployeeFirst = request.form['employeeFirstName']
        new_EmployeeMI = request.form['employeeMI']
        new_EmployeeSurname = request.form['employeeSurname']
        new_EmployeePassword = request.form['password']
        newProfessor = NewProfessor(new_EmployeeFirst, new_EmployeeMI, new_EmployeeSurname, new_EmployeeId, new_EmployeePassword)
        result = newProfessor.register_user()

        if result:
            return redirect(url_for('register'))
        else:
            return redirect(url_for('login'))
 
    return render_template('register.html')

# CODE BLOCK: User Page
@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'userId' not in session:
        return redirect(url_for('login')) # IF: Not logged in, redirect to login page
    
    else:
        currentId = int(session['userId'])
        data = SchedulerData(currentId)

        professorData = data.get_professor_data()
        courseData = data.get_course_data()
        scheduleData = data.get_schedule_data()

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
        currentId = int(session['userId'])
        data = SchedulerData(currentId)

        professorData = data.get_professor_data()
        courseData = data.get_course_data()
        scheduleData = data.get_schedule_data()

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
                course = CourseManagement(newCourseCode, newCourseName, newCourseYear, newCourseUnits)
                result = course.add_course()

                if result:
                    return redirect(url_for('admin'))
                else:
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
                schedule = ScheduleManagement(newCourseSection, newStartTime, newEndTime, newDayOfWeek, newRoom, scheduleData)

                schedule.currentEmployeeID = request.form['currentCourse'].upper()
                schedule.currentCourseID = request.form['professorDetails']

                print(scheduleData)

                ifProfessorExists = schedule.check_professor_from_courses()
                ifNoProfessorExists = schedule.check_noprofessor_from_courses()

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
                    
                    if (schedule.check_professor_from_courses()): # IF: Current professor being assigned is assigned to the current_course -> proceed with logic
                        if (schedule.add_course_to_schedule() == False):
                            return redirect(url_for('admin'))
                        else:
                            return render_template('admin.html',
                                    professorData=professorData,
                                    courseData=courseData,
                                    scheduleData=scheduleData,
                                    current_professor=0)
                    else:
                        if (schedule.check_noprofessor_from_courses):
                            if (schedule.add_course_to_schedule() == False):
                                return redirect(url_for('admin'))
                            else:
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

            # WIP: Delete Course Feature
            if action == "deleteCourse":
                selectedCourseId = request.form["courseToBeDeleted"]
                deleteFromCourses = f"DELETE FROM Courses WHERE courseId = '{selectedCourseId}'"
                deleteFromCourseSchedules = f"DELETE FROM CourseSchedules WHERE courseId = '{selectedCourseId}'"

                # NOTE: Schedules first, then the course information after
                executeQuery(deleteFromCourseSchedules)
                executeQuery(deleteFromCourses)
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




















































































