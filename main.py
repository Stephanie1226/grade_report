import sys
import json
import statistics
import pandas as pd
import numpy as np


class npEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, np.integer):
      return int(obj)
    elif isinstance(obj, np.floating):
      return float(obj)
    elif isinstance(obj, np.ndarray):
      return obj.tolist()
    else:
      return super(npEncoder, self).default(obj)


class ReadData():
  def __init__(self, courses_filename, students_filename, tests_filename, marks_filename):
    self.filenames = [courses_filename, students_filename, tests_filename, marks_filename]
    self.all_data = {}

  def open_and_store(self):
    # Store course data, students data, tests data and marks data 
    # into all_data dictionary [0], [1], [2], [3], respectively.
    for i, filename in enumerate(self.filenames):
      try:
        self.all_data[i] = pd.read_csv(filename, index_col=0)
      except Exception:
        print("Error Reading from file: " + filename)
    return (self.all_data[0], self.all_data[1], self.all_data[2], self.all_data[3])


class CheckData():
  def __init__(self, tests_data):
    self.tests_data = tests_data.values

  def check_weights(self):
    # Return 1 means the total weights for a course is not added up to 100
    # Return 0 means the weights for the courses are all valid
    key = self.tests_data[0][0]
    total_weights = 0
    for i in range(self.tests_data.shape[0]):
      if self.tests_data[i][0] == key:
        total_weights = total_weights + self.tests_data[i][1]
      else:
        if total_weights != 100:
          return 1
        else:
          key = self.tests_data[i][0]
          total_weights = 0
          total_weights = total_weights + self.tests_data[i][1]
    if total_weights != 100:
      return 1
    return 0


class ProcessData():
  def __init__(self, courses_data, students_data, tests_data, marks_data):
    # Combine tests_data and marks_data in order to calculate
    self.marks_tests_data = marks_data.join(tests_data, on='test_id').values
    self.courses_data = courses_data.reset_index().values
    self.students_data = students_data.reset_index().values

  def calculate_weighted_marks(self, weighted_marks, i):
    weighted_marks = weighted_marks + (self.marks_tests_data[i][1] * self.marks_tests_data[i][3]) / 100
    return weighted_marks

  # Store one course information for one student
  def info_per_student_per_course(self, weighted_marks, course_id, courses_list, courses_avg_list):
    for i in range(self.courses_data.shape[0]):
      if self.courses_data[i][0] == course_id:
        course_name = self.courses_data[i][1]
        course_teacher = self.courses_data[i][2]
      else:
        pass
    course_avg = round(weighted_marks, 1)
    courses_info = {"id": course_id, "name": course_name,
                    "teacher": course_teacher, "courseAverage": course_avg}
    courses_list.append(dict(courses_info))
    courses_avg_list.append(course_avg)
    return courses_list, courses_avg_list

  # Store all of the courses information for one student
  def info_per_student(self, student_id, courses_list, students_list, courses_avg_list):
    for i in range(self.students_data.shape[0]):
      if self.students_data[i][0] == student_id:
        student_name = self.students_data[i][1]
      else:
        pass
    student_info = {"id": student_id, "name": student_name,
                    "totalAverage": round(statistics.mean(courses_avg_list), 2), "courses": courses_list}
    students_list.append(dict(student_info))
    return students_list

  # Deal with all of the incoming data
  def calculate_data(self):
    student_id = self.marks_tests_data[0][0]
    course_id = self.marks_tests_data[0][2]
    weighted_marks = 0
    courses_avg_list = []
    courses_list = []
    students_list = []
    for i in range(self.marks_tests_data.shape[0]):
      if self.marks_tests_data[i][0] == student_id:
        if self.marks_tests_data[i][2] == course_id:
          weighted_marks = self.calculate_weighted_marks(weighted_marks, i)
        else:
          # Store the information of the previous course
          courses_list, courses_avg_list = self.info_per_student_per_course(weighted_marks, course_id,
                                                                            courses_list, courses_avg_list)
          # Deal with the next course
          course_id = self.marks_tests_data[i][2]
          weighted_marks = 0
          weighted_marks = self.calculate_weighted_marks(weighted_marks, i)

      else:
        # Store the information of the previous course and student
        courses_list, courses_avg_list = self.info_per_student_per_course(weighted_marks, course_id,
                                                                          courses_list, courses_avg_list)
        students_list = self.info_per_student(student_id, courses_list, students_list, courses_avg_list)

        # Deal with the next student
        student_id = self.marks_tests_data[i][0]
        course_id = self.marks_tests_data[i][2]
        weighted_marks = 0
        courses_avg_list = []
        courses_list = []
        weighted_marks = self.calculate_weighted_marks(weighted_marks, i)

    # Store the information of the previous course and student
    courses_list, courses_avg_list = self.info_per_student_per_course(weighted_marks, course_id,
                                                                      courses_list, courses_avg_list)
    students_list = self.info_per_student(student_id, courses_list, students_list, courses_avg_list)

    return students_list


if __name__ == '__main__':
  # Open input files and save the data
  read_data = ReadData(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
  courses_data, students_data, tests_data, marks_data = read_data.open_and_store()

  # Check if the course weights are invalid
  check_data = CheckData(tests_data)
  validation_code = check_data.check_weights()

  # If validation_code = 1, then print out error in JSON file
  if validation_code == 1:
    reports = {"error": "Invalid course weights"}
  # If validation_code = 0, then process data from four csv files
  else:
    process_data = ProcessData(courses_data, students_data, tests_data, marks_data)
    students_list = process_data.calculate_data()
    reports = {"students": students_list}

  # Generate JSON file
  with open(sys.argv[5], 'w') as fp:
    json.dump(reports, fp, indent=4, cls=npEncoder)

