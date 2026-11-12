-- Write ONE query under each marker. Do not delete the markers.
-- Check with:  python check.py
-- Q1  (all columns of all students)
SELECT *
FROM students;

-- Q2  (name and year of every student)
SELECT name, year
FROM students;

-- Q3  (names of CS students)
SELECT name
FROM students
WHERE program = 'CS';

-- Q4  (name and year of students in year 3 or higher)
SELECT name, year
FROM students
WHERE year >= 3;

-- Q5  (student names, Z to A)
SELECT name
FROM students
ORDER BY name DESC;

-- Q6  (title and credits of 4-credit courses, by title)
SELECT title, credits
FROM courses
WHERE credits = 4
ORDER BY title ASC;

-- Q7  (how many students?)
SELECT COUNT(*)
FROM students;

-- Q8  (number of students per program, by program)
SELECT program, COUNT(*)
FROM students
GROUP BY program
ORDER BY program ASC;

-- Q9  (average grade in CSC10004, rounded to 2 decimals)
SELECT ROUND(AVG(grade), 2)
FROM enrollments
WHERE course_code = 'CSC10004';

-- Q10 (student_id and course_code of enrollments without a grade, by student_id)
SELECT student_id, course_code
FROM enrollments
WHERE grade IS NULL
ORDER BY student_id ASC;

-- Q11 (name and grade of graded students in CSC10014, by name)
SELECT s.name, e.grade
FROM students AS s
JOIN enrollments AS e ON e.student_id = s.id
WHERE e.course_code = 'CSC10014'
  AND e.grade IS NOT NULL
ORDER BY s.name ASC;

-- Q12 (course title and number of enrolled students, most first, then by title)
SELECT c.title, COUNT(e.student_id)
FROM courses AS c
JOIN enrollments AS e ON e.course_code = c.code
GROUP BY c.code, c.title
ORDER BY COUNT(e.student_id) DESC, c.title ASC;

-- Q13 (names of students with a grade below 5, by name)
SELECT DISTINCT s.name
FROM students AS s
JOIN enrollments AS e ON e.student_id = s.id
WHERE e.grade < 5
ORDER BY s.name ASC;

-- Q14 (each student's name and total credits enrolled, most first, then by name)
SELECT s.name, COALESCE(SUM(c.credits), 0) AS total_credits
FROM students AS s
LEFT JOIN enrollments AS e ON e.student_id = s.id
LEFT JOIN courses AS c ON c.code = e.course_code
GROUP BY s.id, s.name
ORDER BY total_credits DESC, s.name ASC;

-- Q15 (names of students NOT enrolled in CSC10014, by name)
SELECT s.name
FROM students AS s
WHERE NOT EXISTS (
    SELECT 1
    FROM enrollments AS e
    WHERE e.student_id = s.id
      AND e.course_code = 'CSC10014'
)
ORDER BY s.name ASC;
