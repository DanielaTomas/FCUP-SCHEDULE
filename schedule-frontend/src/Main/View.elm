module Main.View exposing (..)

import Dict
import DnD
import Html exposing (..)
import Html.Attributes exposing (..)
import Main.List exposing (renderEventsWithoutTime, renderAvailableRooms, renderBlocks, renderStudents, renderEvents, renderLecturers, renderRooms, renderRecommendations)
import Main.Model exposing (Model)
import Main.Msg exposing (Msg(..))
import Main.Schedule exposing (..)
import Maybe.Extra
import ScheduleObjects.Id exposing (ID)
import Maybe.Extra exposing (isNothing)
import ScheduleObjects.Event exposing (Event)


view : Model -> Html Msg
view model =
    let
        tableWidth =
            90 / (4 |> toFloat) |> floor

        -- To shorten the function call;
        renderScheduleAbbr =
            renderSchedule tableWidth model.draggable

        roomList =
            Dict.filter model.filters.room model.data.events |> Dict.toList

        lectList =
            Dict.filter model.filters.lect model.data.events |> Dict.toList

        blockList =
            Dict.filter model.filters.block model.data.events |> Dict.toList

        studentList =
            Dict.filter model.filters.student model.data.events |> Dict.toList

        -- Here we render the filters, turning them from (EventID -> Event -> Bool) into a List (EventID, Event)
        occupationsList =
            Dict.filter model.filters.occupations model.data.occupations |> Dict.toList

        restrictionList =
            Dict.filter model.filters.restrictions model.data.restrictions |> Dict.toList

        roomName =
            Maybe.map (\( _, r ) -> r.abbr) model.selectedItems.room |> Maybe.Extra.withDefaultLazy (\() -> "")

        lectName =
            Maybe.map (\( _, l ) -> l.abbr) model.selectedItems.lect |> Maybe.Extra.withDefaultLazy (\() -> "")

        blockName =
            Maybe.map (\( _, b ) -> b.nameAbbr) model.selectedItems.block |> Maybe.Extra.withDefaultLazy (\() -> "")

        studentName =
            Maybe.map (\( _, s ) -> s.name) model.selectedItems.student |> Maybe.Extra.withDefaultLazy (\() -> "")

        recommendationsList =
            List.indexedMap (\i (event, _) -> (i, event)) model.data.recommendations

        filteredEvents = 
            model.data.events
                |> Dict.toList
                |> filterEventsWithoutTime

        displayOnDrag : ID -> Html Msg
        displayOnDrag id =
            div [] [ id |> String.fromInt |> text ]
    in
    div []
        [ div [ class "listbox-area" ]
            [ renderStudents model.data.students model.data.hiddenStudents model.selectedItems.student
            , renderLecturers model.data.lecturers model.data.hiddenLecturers model.selectedItems.lect
            , renderRooms model.data.rooms model.data.hiddenRooms model.selectedItems.room
            , renderEvents (Dict.toList model.data.events) (Dict.toList model.data.hiddenEvents) model.data.rooms model.data.lecturers model.selectedItems.event
            , renderAvailableRooms model.selectedItems.event model.data.rooms (Dict.values model.data.events) (Dict.values model.data.occupations)
            , renderBlocks model.data.blocks model.data.hiddenBlocks model.selectedItems.block
            ]
        , div[ class "listbox-area-recommendations"]
            [ renderEventsWithoutTime filteredEvents model.data.rooms model.data.lecturers 
            , renderRecommendations recommendationsList model.data.rooms model.data.lecturers
            ]
        , div [ class "grids-container" ] [ renderScheduleAbbr blockList [] [] ("Bloco:" ++ blockName), renderScheduleAbbr roomList occupationsList [] ("Sala:" ++ roomName), renderScheduleAbbr lectList [] restrictionList ("Docente:" ++ lectName), renderScheduleAbbr studentList [] [] ("Estudante:" ++ studentName) ]
        , DnD.dragged
            model.draggable
            displayOnDrag
        ]

filterEventsWithoutTime : List (Int, Event) -> List (Int, Event)
filterEventsWithoutTime events =
    List.filter (\(_, event) -> isNothing event.start_time && isNothing event.end_time) events