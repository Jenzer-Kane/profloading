import pandas as pd

def readContents(name):
    data = []
    course_codes = []
    df = pd.read_excel(name)
    unique_values = df.drop_duplicates(subset=["COURSE CODE"], keep='first')

    query = f"INSERT INTO Courses (courseId, courseName, courseYear, courseUnits) VALUES "

    for index, row in unique_values.iterrows():
        if (type(row['COURSE CODE']) == float 
        and type(row['COURSE NAME']) == float
        and type(row['YEAR LEVEL']) == float
        and type(row['UNITS']) == float
        and type(row['COURSE TYPE']) == float):
            continue

        data.append((row['COURSE CODE'], row['COURSE NAME'], row['YEAR LEVEL'], int(row['UNITS'])))

    ctr = 0

    for x in data:
        if ctr != len(data)-1:
            query += str(x) + ", "
        else:
            query += str(x)
        ctr += 1

    return query
