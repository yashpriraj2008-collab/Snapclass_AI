import pandas as pd

STUDENTS = pd.DataFrame([
    {"roll":"SC001","name":"Yashraj Mehta", "class_name":"12-A","attendance":85,"email":"yashraj@demo.com"},
    {"roll":"SC002","name":"Aarav Singh",   "class_name":"12-A","attendance":78,"email":"aarav@demo.com"},
    {"roll":"SC003","name":"Meera Patel",   "class_name":"12-A","attendance":92,"email":"meera@demo.com"},
    {"roll":"SC004","name":"Kabir Khan",    "class_name":"12-A","attendance":68,"email":"kabir@demo.com"},
    {"roll":"SC005","name":"Riya Sharma",   "class_name":"12-B","attendance":74,"email":"riya@demo.com"},
    {"roll":"SC006","name":"Dev Joshi",     "class_name":"12-B","attendance":55,"email":"dev@demo.com"},
    {"roll":"SC007","name":"Ananya Rao",    "class_name":"11-A","attendance":90,"email":"ananya@demo.com"},
    {"roll":"SC008","name":"Rohan Verma",   "class_name":"11-A","attendance":82,"email":"rohan@demo.com"},
])

TEACHERS = pd.DataFrame([
    {"id":"T01","name":"Dr. Sharma",    "subject":"Mathematics","class_name":"12-A","email":"sharma@demo.com"},
    {"id":"T02","name":"Prof. Gupta",   "subject":"Physics",    "class_name":"12-A","email":"gupta@demo.com"},
    {"id":"T03","name":"Dr. Patel",     "subject":"Chemistry",  "class_name":"12-B","email":"patel@demo.com"},
    {"id":"T04","name":"Ms. Rao",       "subject":"English",    "class_name":"11-A","email":"rao@demo.com"},
])

SUBJECTS = pd.DataFrame([
    {"subject":"Mathematics","teacher":"Dr. Sharma", "total":42,"present":36,"class_name":"12-A"},
    {"subject":"Physics",    "teacher":"Prof. Gupta","total":40,"present":34,"class_name":"12-A"},
    {"subject":"Chemistry",  "teacher":"Dr. Patel",  "total":39,"present":31,"class_name":"12-A"},
    {"subject":"English",    "teacher":"Ms. Rao",    "total":38,"present":26,"class_name":"12-A"},
    {"subject":"Biology",    "teacher":"Dr. Gupta",  "total":36,"present":32,"class_name":"12-A"},
    {"subject":"Computer Sc","teacher":"Mr. Singh",  "total":35,"present":30,"class_name":"12-A"},
])
SUBJECTS["attendance"] = (SUBJECTS["present"] / SUBJECTS["total"] * 100).round(1)

ATTENDANCE_TREND = pd.DataFrame({
    "month":      ["Jan","Feb","Mar","Apr","May","Jun"],
    "attendance": [82, 85, 78, 88, 85, 90],
})

WEEKLY_TREND = pd.DataFrame({
    "day":  ["Mon","Tue","Wed","Thu","Fri"],
    "rate": [88, 92, 85, 90, 87],
})

CLASSES = pd.DataFrame([
    {"class_id":"CL01","class_name":"12-A","subject":"Mathematics","time":"9:00 AM", "teacher":"Dr. Sharma","students":40},
    {"class_id":"CL02","class_name":"12-A","subject":"Physics",    "time":"11:00 AM","teacher":"Prof. Gupta","students":40},
    {"class_id":"CL03","class_name":"12-B","subject":"Chemistry",  "time":"2:00 PM", "teacher":"Dr. Patel","students":38},
    {"class_id":"CL04","class_name":"11-A","subject":"English",    "time":"10:00 AM","teacher":"Ms. Rao","students":42},
])

NOTIFICATIONS = [
    {"type":"warning","message":"Your Mathematics attendance is 72% — below 75% threshold."},
    {"type":"info",   "message":"Physics class rescheduled to Friday 11 AM."},
    {"type":"success","message":"Chemistry attendance updated: Present on 12 May."},
    {"type":"info",   "message":"Monthly attendance report is now available."},
]

INSTITUTES = [
    {"name":"Sunrise Academy",   "city":"Mumbai",  "teachers":12,"students":320,"attendance":86},
    {"name":"Bright Coaching",   "city":"Delhi",   "teachers":8, "students":180,"attendance":79},
    {"name":"Future Institute",  "city":"Pune",    "teachers":15,"students":450,"attendance":91},
]
