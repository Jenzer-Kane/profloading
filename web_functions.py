import pypyodbc as odbc
from flask import Flask, render_template, redirect, request, session, url_for

server = 'umakclassscheduler.database.windows.net'
database = 'SchedulerDB'
connString = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:umakscheduler.database.windows.net,1433;Database='+database+';Uid=umakscheduler;Pwd=Adminschedule123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

class NewProfessor:
    def __init__(self, first, MI, last, empID, empPass):
        self.first = first
        self.MI = MI
        self.last = last
        self.fullName = first + ' ' + MI + '. ' + last
        self.empID = empID
        self.empPass = empPass

    def register_user(self):
        checkForRegister = f"SELECT * FROM Professors WHERE employeeId = {self.empID}"
        insertProfessorData = f"INSERT INTO Professors (employeeId, employeeName, employeePassword) VALUES ({self.empID}, '{self.fullName}', '{self.empPass}')"
        insertHonorariumToken = f"INSERT INTO Courses (courseId, courseName, courseYear, courseUnits, professorId) VALUES ('{'HT' + str(self.empID)}', 'Honorarium Time', '', 0, {self.empID})"
        insertVacantToken = f"INSERT INTO Courses (courseId, courseName, courseYear, courseUnits, professorId) VALUES ('{'VT' + str(self.empID)}', 'Vacant Time', '', 0, {self.empID})"
        
        result = self.executeQuery(checkForRegister)
        if result:
            print("Professor exists!")
            return True
        else:
            print("Inserted new professor!")
            executeQuery(insertProfessorData)
            executeQuery(insertHonorariumToken)
            executeQuery(insertVacantToken)
            return False

class ExistingProfessor:
    def __init__(self, empID, empPass):
        self.empID = int(empID)
        self.empPass = empPass

    def login_user(self):
        checkForLogin = f"SELECT * FROM Professors WHERE employeeId = {self.empID} AND employeePassword = '{self.empPass}'"
        loginResult = executeQuery(checkForLogin)

        if loginResult:
            if self.empID == 0000 and self.empPass == 'passadmin':
                print("Logged in as: [ADMIN]")
                print(self.empID, self.empPass)
                return False
            else:
                print(f"Logged in as: [{self.empID}]")
                print(self.empID, self.empPass)
                return True

class SchedulerData:
    getProfessorsQuery = "SELECT employeeId, employeeName FROM Professors WHERE employeeId != 0000"
    getCoursesQuery = "SELECT * FROM Courses"
    getCourseSchedulesQuery = "SELECT * FROM CourseSchedules"

    def __init__(self, empID):
        self.empID = empID

    def get_professor_data(self):
        return executeQuery(SchedulerData.getProfessorsQuery)

    def get_course_data(self):
        return executeQuery(SchedulerData.getCoursesQuery)

    def get_schedule_data(self):
        return executeQuery(SchedulerData.getCourseSchedulesQuery)

class CourseManagement():
    def __init__(self, courseID, courseName, courseYear, courseUnits):
        self.courseID = courseID
        self.courseName = courseName
        self.courseYear = courseYear
        self.courseUnits = courseUnits

    def add_course(self):
        checkCurrentCourse = f"SELECT * FROM Courses WHERE courseId = '{self.courseID}'"
        insertCourseData = f"INSERT INTO Courses (courseId, courseName, courseYear, courseUnits) VALUES ('{self.courseID}', '{self.courseName}', '{self.courseYear}', {self.courseUnits})"
        checkResult = executeQuery(checkCurrentCourse)

        if checkResult:
            print(f'{self.courseID} already exists!')
            return True
        else:
            executeQuery(insertCourseData)
            print(f'{self.courseID} added!')
            return False

    def remove_course(self):
        pass

class ScheduleManagement(CourseManagement, SchedulerData):
    currentEmployeeID = 0000
    currentCourseID = 0000

    def __init__(self, courseSection, startTime, endTime, dayOfWeek, room, scheduleData):
        self.courseSection = courseSection
        self.startTime = startTime
        self.endTime = endTime
        self.dayOfWeek = dayOfWeek
        self.room = room
        self.scheduleData = scheduleData

    def add_course_to_schedule(self):
        insertScheduleQuery = f"INSERT INTO CourseSchedules (courseId, professorId, room, section, dayOfWeek, startTime, endTime) VALUES ('{ScheduleManagement.currentCourseID}', {ScheduleManagement.currentEmployeeID}, '{self.room}', '{self.courseSection}', '{self.dayOfWeek}', '{self.startTime}', '{self.endTime}')"
        updateCourseQuery = f"UPDATE Courses SET professorId = {ScheduleManagement.currentEmployeeID} WHERE courseId = '{ScheduleManagement.currentCourseID}'"
        checkIfSameTime = f"SELECT * FROM CourseSchedules WHERE startTime = '{self.startTime}' AND endTime = '{self.endTime}' and dayOfWeek = '{self.dayOfWeek}'" 
        checkExceeds3Hours = f"""
                                SELECT professorId, 
                                    SUM(DATEDIFF(MINUTE, startTime, endTime) / 60.0) AS totalScheduledHours
                                FROM CourseSchedules
                                WHERE professorId = {ScheduleManagement.currentEmployeeID}
                                AND courseId = '{ScheduleManagement.currentCourseID}'
                                AND dayOfWeek = '{self.dayOfWeek}'
                                GROUP BY professorId
                                HAVING SUM(DATEDIFF(MINUTE, startTime, endTime) / 60.0) >= 3;
                                """
        
        if (executeQuery(checkIfSameTime)):
            print("\n\nTEST (Admin Page): Subject/Honorarium or Vacant Time already assigned in the same time!\n\n") # TEST: Test Validation
        else:
            if (executeQuery(checkExceeds3Hours)):
                print("\n\nTEST (Admin Page): Already has 3 hours in slot!\n\n") # TEST: Test Validation
            else:
                print("\n\nTEST (Admin Page): Inserted into the database!\n\n") # TEST: Test Validation
                executeQuery(insertScheduleQuery)

                if (self.check_noprofessor_from_courses()):
                    executeQuery(updateCourseQuery)
                return True
        
    def populate_empty_schedule(self):
        if (self.scheduleData is None):
            executeQuery(insert)
        pass


    def check_professor_from_courses(self):
        courseData = self.get_course_data()
        for courses in courseData:
            if courses[0] == ScheduleManagement.currentCourseID and courses[4] == ScheduleManagement.currentEmployeeID:
                return True
        return False

    def check_noprofessor_from_courses(self):
        courseData = self.get_course_data()
        for courses in courseData:
            if courses[0] == ScheduleManagement.currentCourseID and courses[4] is None:
                return True
        return False


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

prof1 = NewProfessor('Juan', 'T', 'Dela Cruz', 6969, 6969)
print(prof1.fullName)

prof2 = ExistingProfessor(6969, 6969)
prof2.login_user()