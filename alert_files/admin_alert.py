def invalid_course_exists(subject):
    return '<script>alert("ERROR: Course Code: [' + subject + '] already exists in the database!");window.location.href="/admin";</script>'

def invalid_existing_course_timeslot(subject):
    return '<script>alert("ERROR: Course Code: [' + subject + '] is being scheduled at a timeframe that has an existing schedule. ");window.location.href="/admin";</script>'

def invalid_overlap_course_timeslot(subject):
    return '<script>alert("ERROR: Course Code: [' + subject + '] is overlapping with a timeframe that has an existing schedule. ");window.location.href="/admin";</script>'

def invalid_existing_course_assignment(subject):
    return '<script>alert("ERROR: [' + subject + '] is already assigned to the same section. ");window.location.href="/admin";</script>'

def invalid_existing_room(room):
    print(room)
    for data in room:
        print(data)
        
    return '<script>alert("ERROR: ROOM: ['+ data[3] +'] is already being used from another schedule. ");window.location.href="/admin";</script>'

def invalid_maximum_timeslot(subject, typeSub):
    if typeSub == 'Major':
        return '<script>alert("ERROR: Course Code: [' + subject + '] is already at a maximum timeslot (3 hours). ");window.location.href="/admin";</script>'
    else:
        return '<script>alert("ERROR: Course Code: [' + subject + '] is already at a maximum timeslot (1.5 hours). ");window.location.href="/admin";</script>'

def invalid_existing_professor_in_course(subject):
    return '<script>alert("ERROR: Course Code: [' + subject + '] is already assigned to another professor. ");window.location.href="/admin";</script>'

def invalid_existing_honorVacant_timeslot(honorVacant):
    return '<script>alert("ERROR: [' + honorVacant + '] is being scheduled at a timeframe that has an existing schedule. ");window.location.href="/admin";</script>'

def invalid_maximum_honorVacant_timeslot(honorVacant):
    return '<script>alert("ERROR: [' + honorVacant + '] is already at a maximum  timeslot (1 hr, 30 mins). ");window.location.href="/admin";</script>'

def invalid_filenotfound():
    return '<script>alert("ERROR: File not found.");window.location.href="/admin";</script>'




def success_admin_logout():
    return '<script>alert("You have been logged out.")window.location.href="/login";</script>'

def success_course_add(subject):
    return '<script>alert("SUCCESS: Course Code: [' + subject + '] have been successfully imported.");window.location.href="/admin";</script>'

def success_subject_import():
    return '<script>alert("SUCCESS: Subjects have been successfully imported.");window.location.href="/admin";</script>'

def success_delete_user(profId, profName):
    return '<script>alert("SUCCESS:\nProf. [' + profName + '] with ID: [' + profId + '] has been deleted.\n");window.location.href="/admin";</script>'