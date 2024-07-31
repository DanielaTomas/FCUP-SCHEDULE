module ScheduleObjects.Student exposing (..)

import ScheduleObjects.Event exposing (Event, EventID)
import ScheduleObjects.Id exposing (ID)

type alias Student =
    { name : String, course : String, number : Int, cond : EventID -> Event -> Bool }


type alias StudentID =
    ID


setStudentCond : (EventID -> Event -> Bool) -> Student -> Student
setStudentCond cond student =
    { student | cond = cond }

setStudentNumber: Int -> Student -> Student
setStudentNumber number student =
    { student | number = number }

setStudentCourse: String -> Student -> Student
setStudentCourse course student =
    { student | course = course }


setStudentName : String -> Student -> Student
setStudentName name student =
    { student | name = name }
