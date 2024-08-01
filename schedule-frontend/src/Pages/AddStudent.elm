module Pages.AddStudent exposing (Model, Msg, page)

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
import Page exposing (Page)
import Route exposing (Route)
import Route.Path
import Maybe.Extra
import ScheduleObjects.Student exposing (Student, StudentID, setStudentNumber, setStudentCond, setStudentName, setStudentCourse)
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


page : Shared.Model -> Route () -> Page Model Msg
page shared route =
    Page.new
        { init = init shared
        , update = update
        , subscriptions = subscriptions
        , view = view
        }



-- INIT


type alias Model =
    { data : Data, student : Student, evList : EventList, deleteConfirmation : Bool, errorMsg : String, isHidden : Bool }


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


type alias EventList =
    { selectState : Select.State
    , items : List ( EventID, Event )
    , selectedEvents : List ( EventID, Event )
    }


init : Data -> () -> ( Model, Effect Msg )
init data () =
    ( Model data (Student "" "" 0 (\_ _ -> False)) (initEventList data) False "" False
    , Effect.none
    )


initEventList : Data -> EventList
initEventList data =
    let
        items =
            Dict.toList data.events
    in
    { selectState =
        Select.initState (Select.selectIdentifier "Event")
            |> Select.keepMenuOpen True
    , items = items
    , selectedEvents = []
    }



-- UPDATE


type Msg
    = CourseChange String
    | NameChange String
    | NumberChange Int
    | SelectEvent (Select.Msg ( EventID, Event ))
    | UpdateStudentRequest
    | UpdateStudentResult (Result Http.Error ( StudentID, ( Student, IsHidden ) ))
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

        NumberChange newNumber ->
            ( setStudentNumber newNumber model.student |> asStudentIn model, Effect.none )

        NameChange newName ->
            ( setStudentName newName model.student |> asStudentIn model, Effect.none )

        CourseChange newCourse ->
            ( setStudentCourse newCourse model.student |> asStudentIn model, Effect.none )

        UpdateStudentRequest ->
            ( model, Effect.sendCmd <| updateStudent model.student model.isHidden model.data.events model.data.backendUrl model.data.token )

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

        VisibilityChange newVisibility ->
            ( { model | isHidden = newVisibility }, Effect.none )

        Return ->
            ( model, Effect.pushRoute { path = Route.Path.Main, query = Dict.empty, hash = Nothing } )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.none



-- VIEW


view : Model -> View Msg
view model =
    { title = "Criar Estudante"
    , body =
        [ input [ class "input-box", style "width" "100%", value model.student.name, onInput NameChange, Html.Attributes.placeholder "Nome" ] []
        , input [ class "input-box", style "width" "100%", value <| String.fromInt model.student.number, onInput (NumberChange << Maybe.Extra.withDefaultLazy (\() -> model.student.number) << String.toInt), Html.Attributes.placeholder "Número" ] []
        , input [ class "input-box", style "width" "100%", value model.student.course, onInput CourseChange, Html.Attributes.placeholder "Curso" ] []
        , div [] [ input [ type_ "checkbox", checked model.isHidden, onCheck VisibilityChange ] [], label [] [ text "Esconder Estudante" ] ]
        , button [ style "margin-right" "2%", class "button", onClick Return ] [ text "Retornar" ]
        , button [ class "button", onClick UpdateStudentRequest, style "margin-top" "1vh", style "margin-bottom" "1vh" ] [ text "Submeter" ]
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


updateStudent : Student -> IsHidden -> Dict EventID Event -> String -> Token -> Cmd Msg
updateStudent student isHidden events backendUrl token =
    Http.request
        { method = "POST"
        , headers = [ Http.header "Authorization" ("Bearer " ++ token), Http.header "Content-Type" "application/json" ]
        , url = backendUrl ++ "students"
        , body = Http.jsonBody (Encoders.putStudent Nothing events student isHidden)
        , expect = Http.expectJson UpdateStudentResult (Decoders.responseParser Decoders.getStudentAndID)
        , timeout = Nothing
        , tracker = Nothing
        }
