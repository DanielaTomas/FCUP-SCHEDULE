module Pages.EditStudent.Id_ exposing (..)

import Css
import Decoders
import Dict exposing (Dict)
import Effect exposing (Effect)
import Encoders
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Html.Styled as HS
import Html.Styled.Attributes as HSA
import Http
import Maybe.Extra
import Page exposing (Page)
import Route exposing (Route)
import Route.Path
import ScheduleObjects.Student exposing (Student, StudentID, setStudentNumber, setStudentCourse, setStudentCond, setStudentName)
import ScheduleObjects.Data exposing (Data, Token)
import ScheduleObjects.Event exposing (Event, EventID)
import ScheduleObjects.Hide exposing (IsHidden)
import ScheduleObjects.Lecturer exposing (Lecturer, LecturerID)
import ScheduleObjects.Room exposing (Room, RoomID)
import ScheduleObjects.WeekTimeConverters exposing (..)
import Select exposing (..)
import Select.Styles as Styles
import Shared
import View exposing (View)


page : Shared.Model -> Route { id : String } -> Page Model Msg
page shared route =
    Page.new
        { init = init shared route.params.id
        , update = update
        , subscriptions = subscriptions
        , view = view
        }



-- INIT


type alias Model =
    { data : Data
    , studentID : StudentID
    , student : Student
    , evList : EventList
    , deleteConfirmation : Bool
    , errorMsg : String
    , isHidden : Bool
    }



-- Model data ( studentID, student ) evList deleteConfirmation errorMsg isHidden


type alias EventList =
    { selectState : Select.State
    , items : List ( EventID, Event )
    , selectedEvents : List ( EventID, Event )
    }


asStudentIn : { a | student : b } -> b -> { a | student : b }
asStudentIn a student =
    { a | student = student }


setStudent student a =
    { a | student = student }


setEvList evList model =
    { model | evList = evList }


setEvListSelectState state evList =
    { evList | selectState = state }


setEvListSelectEv selectedEvents evList =
    { evList | selectedEvents = selectedEvents }


init : Data -> String -> () -> ( Model, Effect Msg )
init data eventIDParam () =
    let
        studentID =
            case String.toInt eventIDParam of
                Just number ->
                    number

                Nothing ->
                    -1

        ( student, isHidden ) =
            case Dict.get studentID data.students of
                Just b ->
                    ( b, False )

                Nothing ->
                    ( Dict.get studentID data.hiddenStudents |> Maybe.Extra.withDefaultLazy (\() -> Student "" "" 0 (\_ _ -> False)), True )
    in
    ( Model data studentID student (initEventList ( studentID, student ) data) False "" isHidden
    , Effect.none
    )


initEventList : ( StudentID, Student ) -> Data -> EventList
initEventList ( studentID, student ) data =
    let
        eventIDsOfStudent =
            Dict.filter student.cond data.events
                |> Dict.toList

        items =
            Dict.toList data.events
    in
    { selectState =
        Select.initState (Select.selectIdentifier "Event")
            |> Select.keepMenuOpen True
    , items = items
    , selectedEvents = eventIDsOfStudent
    }



-- UPDATE


type Msg
    = NumberChange Int
    | NameChange String
    | CourseChange String
    | SelectEvent (Select.Msg ( EventID, Event ))
    | UpdateStudentRequest
    | UpdateStudentResult (Result Http.Error ( StudentID, ( Student, IsHidden ) ))
    | DeleteStudentRequest
    | DeleteStudentResult (Result Http.Error ())
    | VisibilityChange Bool
    | Return


update : Msg -> Model -> ( Model, Effect Msg )
update msg model =
    case msg of
        SelectEvent selectMsg ->
            let
                ( maybeAction, updatedSelectState, selectCmds ) =
                    Select.update selectMsg model.evList.selectState

                updatedSelectedEvents =
                    case maybeAction of
                        Just (Select.Select ( id, ev )) ->
                            ( id, ev ) :: model.evList.selectedEvents

                        Just (Select.Deselect deselectedItems) ->
                            List.filter (\( id, ev ) -> not (List.member ( id, ev ) deselectedItems)) model.evList.selectedEvents

                        Just Clear ->
                            []

                        _ ->
                            model.evList.selectedEvents

                newStudentCond =
                    \id _ -> List.member id (List.map Tuple.first updatedSelectedEvents)
            in
            ( model
                |> setStudent (model.student |> setStudentCond newStudentCond)
                |> setEvList (model.evList |> setEvListSelectState updatedSelectState |> setEvListSelectEv updatedSelectedEvents)
            , Effect.sendCmd (Cmd.map SelectEvent selectCmds)
            )

        -- ( Model data ( studentID, { student | cond = newStudentCond } ) { evList | selectState = updatedSelectState, selectedEvents = updatedSelectedEvents } deleteConfirmation errorMsg isHidden, Effect.sendCmd (Cmd.map SelectEvent selectCmds) )
        NameChange newName ->
            ( model |> setStudent (model.student |> setStudentName newName), Effect.none )

        NumberChange newNumber ->
            ( model |> setStudent (model.student |> setStudentNumber newNumber), Effect.none )

        CourseChange newCourse ->
            ( model |> setStudent (model.student |> setStudentCourse newCourse), Effect.none )


        UpdateStudentRequest ->
            ( model, Effect.sendCmd <| updateStudent ( model.studentID, model.student ) model.isHidden model.data.events model.data.backendUrl model.data.token )

        DeleteStudentRequest ->
            if model.deleteConfirmation then
                ( { model | deleteConfirmation = False }, Effect.sendCmd <| deleteStudent model.studentID model.data.backendUrl model.data.token )

            else
                ( { model | deleteConfirmation = True }, Effect.none )

        UpdateStudentResult result ->
            case result of
                Ok ( id, updatedStudent ) ->
                    let
                        route =
                            { path = Route.Path.Main
                            , query = Dict.empty
                            , hash = Nothing
                            }
                    in
                    ( model, Effect.updateStudent ( id, updatedStudent ) (Just route) )

                Err err ->
                    ( { model | errorMsg = Decoders.errorToString err }, Effect.none )

        DeleteStudentResult result ->
            case result of
                Ok () ->
                    let
                        route =
                            { path = Route.Path.Main
                            , query = Dict.empty
                            , hash = Nothing
                            }
                    in
                    ( model, Effect.deleteStudent model.studentID (Just route) )

                Err err ->
                    ( { model | errorMsg = Decoders.errorToString err }, Effect.none )

        VisibilityChange newVisibility ->
            ( {model | isHidden = newVisibility}, Effect.none )

        Return ->
            let
                route =
                    { path = Route.Path.Main
                    , query = Dict.empty
                    , hash = Nothing
                    }
            in
            ( model, Effect.pushRoute route )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.none



-- VIEW


view : Model -> View Msg
view model =
    { title = "Editar Estudantes"
    , body =
        [ --input [ class "input-box", style "width" "100%", value (String.fromInt model.student.number), onInput NumberChange, Html.Attributes.placeholder "Número" ] []
        input [ class "input-box", style "width" "100%", value model.student.name, onInput NameChange, Html.Attributes.placeholder "Nome" ] []
        , input [ class "input-box", style "width" "100%", value model.student.course, onInput CourseChange, Html.Attributes.placeholder "Course" ] []
        , div [] [ input [ type_ "checkbox", checked model.isHidden, onCheck VisibilityChange ] [], label [] [ text "Esconder Estudante" ] ]
        , button [ style "margin-right" "2%", class "button", onClick Return ] [ text "Retornar" ]
        , button [ class "button", onClick UpdateStudentRequest, style "margin-top" "1vh", style "margin-bottom" "1vh" ] [ text "Submeter" ]
        , button [ style "margin-left" "2%", style "color" "red", class "button", onClick DeleteStudentRequest ]
            [ text
                (if model.deleteConfirmation then
                    "Tem a certeza?"

                 else
                    "Eliminar"
                )
            ]
        , div [ style "width" "100%" ] [ text model.errorMsg ]
        , Html.map SelectEvent (HS.toUnstyled <| renderEventsList model.data model.evList)
        ]
    }


renderEventsList : Data -> EventList -> HS.Html (Select.Msg ( EventID, Event ))
renderEventsList data eventList =
    let
        selectedItems =
            List.map (\( id, ev ) -> Select.basicMenuItem { item = ( id, ev ), label = ev.subjectAbbr }) eventList.selectedEvents

        menuItems =
            List.map (\( id, ev ) -> Select.customMenuItem { item = ( id, ev ), label = ev.subjectAbbr, view = renderEvent data.rooms data.lecturers ( id, ev ) }) eventList.items
    in
    Select.view
        (Select.multi selectedItems
            |> Select.state eventList.selectState
            |> Select.menuItems menuItems
            |> Select.placeholder "Selecione os eventos"
            |> Select.searchable True
            |> Select.clearable True
            |> Select.setStyles (Styles.default |> Styles.setMenuStyles menuBranding)
        )


menuBranding : Styles.MenuConfig
menuBranding =
    Styles.getMenuConfig Styles.default
        |> Styles.setMenuMaxHeightVh (Css.vh 50)


{-| Transforms an event into a list item
-}
renderEvent : Dict RoomID Room -> Dict LecturerID Lecturer -> ( EventID, Event ) -> HS.Html Never
renderEvent rooms lecturers ( eventID, event ) =
    let
        room =
            case event.room of
                Just roomID ->
                    case Dict.get roomID rooms of
                        Just val ->
                            val

                        -- ERROR: RoomID is missing from the database!
                        Nothing ->
                            Room "----" "----" -1 "----"

                -- Event still has no room assigned
                Nothing ->
                    Room "----" "----" -1 "----"

        lecturer =
            case event.lecturer of
                Just lecturerID ->
                    case Dict.get lecturerID lecturers of
                        Just val ->
                            val

                        -- ERROR: RoomID is missing from the database!
                        Nothing ->
                            Lecturer "----" "----" ""

                -- Event still has no room assigned
                Nothing ->
                    Lecturer "----" "----" ""
    in
    HS.li [ HSA.class "list-item" ]
        [ HS.div [ HSA.class "custom-scrollbar", HSA.class "list-text", HSA.style "width" "10%", HSA.attribute "title" event.subjectAbbr ] [ HS.text event.subjectAbbr ]
        , HS.div [ HSA.class "custom-scrollbar", HSA.class "list-text", HSA.style "width" "35%", HSA.attribute "title" event.subject, HSA.style "margin-left" "1%" ] [ HS.text event.subject ]
        , HS.div [ HSA.class "custom-scrollbar", HSA.class "list-text", HSA.style "width" "5%", HSA.style "margin-left" "1%" ] [ HS.text (convertWeekDay event.start_time) ]
        , HS.div [ HSA.class "custom-scrollbar", HSA.class "list-text", HSA.style "width" "10%", HSA.style "margin-left" "1%" ] [ HS.text (convertWeekTimeHourAndMinute event.start_time) ]
        , HS.div [ HSA.class "custom-scrollbar", HSA.class "list-text", HSA.style "width" "10%", HSA.style "margin-left" "1%" ] [ HS.text (convertWeekTimeHourAndMinute event.end_time) ]
        , HS.div [ HSA.class "custom-scrollbar", HSA.class "list-text", HSA.style "width" "15%", HSA.attribute "title" room.abbr, HSA.style "margin-left" "1%" ] [ HS.text room.abbr ]
        , HS.div [ HSA.class "custom-scrollbar", HSA.class "list-text", HSA.style "width" "5%", HSA.style "margin-left" "1%" ] [ HS.text (String.fromInt room.capacity) ]
        , HS.div [ HSA.class "custom-scrollbar", HSA.class "list-text", HSA.style "width" "10%", HSA.style "margin-left" "1%" ] [ HS.text lecturer.abbr ]
        ]



------------------------ HTTP ------------------------


updateStudent : ( StudentID, Student ) -> IsHidden -> Dict EventID Event -> String -> Token -> Cmd Msg
updateStudent ( id, student ) isHidden events backendUrl token =
    Http.request
        { method = "PUT"
        , headers = [ Http.header "Authorization" ("Bearer " ++ token), Http.header "Content-Type" "application/json" ]
        , url = backendUrl ++ "students\\" ++ String.fromInt id
        , body = Http.jsonBody (Encoders.putStudent Nothing events student isHidden)
        , expect = Http.expectJson UpdateStudentResult (Decoders.responseParser Decoders.getStudentAndID)
        , timeout = Nothing
        , tracker = Nothing
        }


deleteStudent : StudentID -> String -> Token -> Cmd Msg
deleteStudent id backendUrl token =
    Http.request
        { method = "DELETE"
        , headers = [ Http.header "Authorization" ("Bearer " ++ token), Http.header "Content-Type" "application/json" ]
        , url = backendUrl ++ "students\\" ++ String.fromInt id
        , body = Http.emptyBody
        , expect = Http.expectWhatever handleDeleteResponse
        , timeout = Nothing
        , tracker = Nothing
        }


handleDeleteResponse : Result Http.Error () -> Msg
handleDeleteResponse response =
    case response of
        Ok _ ->
            DeleteStudentResult (Ok ())

        Err err ->
            DeleteStudentResult (Err err)
