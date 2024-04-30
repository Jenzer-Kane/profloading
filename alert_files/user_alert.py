def invalid_login_credentials():
    return '<script>alert("Sorry! Your credentials are invalid. Please check your ID Number and Password.")window.location.href="/login";</script>'

def invalid_existing_user():
    return '<script>alert("Sorry! That ID number is already registered.")window.location.href="/register";</script>'

def success_registration():
    return '<script>alert("Registration successful. You may now login using your registered credentials.")window.location.href="/login";</script>'

def success_user_logout():
    return '<script>alert("You have been logged out.")window.location.href="/login";</script>'

def success_submit_inquiry():
    return '<script>alert("Your response was recorded.")window.location.href="/index";</script>'