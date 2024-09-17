module Main.Model exposing (Model, init, setRecommendations, setFilters, setSelectedBlock, setSelectedStudent, setSelectedEvent, setSelectedItems, setSelectedLect, setSelectedRoom)

-- import Dict

import Effect exposing (Effect)
import Main.Msg exposing (Draggable, Msg(..), dnd)
import ScheduleObjects.Block exposing (Block, BlockID)
import ScheduleObjects.Student exposing (Student, StudentID)
import ScheduleObjects.Data exposing (Data)
import ScheduleObjects.Event exposing (Event, EventID)
import ScheduleObjects.Filters exposing (ScheduleFilter)
import ScheduleObjects.Lecturer exposing (Lecturer, LecturerID)
import ScheduleObjects.Room exposing (Room, RoomID)


type alias Model =
    { data : Data
    , filters : ScheduleFilter
    , draggable : Draggable
    , selectedItems : SelectedItemsInList
    , recommendations : List Event
    }


setSelectedItems : SelectedItemsInList -> { b | selectedItems : SelectedItemsInList } -> { b | selectedItems : SelectedItemsInList }
setSelectedItems selectedItems a =
    { a | selectedItems = selectedItems }


setFilters : ScheduleFilter -> { b | filters : ScheduleFilter } -> { b | filters : ScheduleFilter }
setFilters filters a =
    { a | filters = filters }

setRecommendations : (List Event) -> { b | recommendations : (List Event) } -> { b | recommendations : (List Event) }
setRecommendations recommendations a =
    { a | recommendations = recommendations }

{-| Item (can be either an ev, room, lecturer, student or a block) selected in the lists
-}
type alias SelectedItemsInList =
    { room : Maybe ( RoomID, Room )
    , lect : Maybe ( LecturerID, Lecturer )
    , event : Maybe ( EventID, Event )
    , block : Maybe ( BlockID, Block )
    , student : Maybe ( StudentID, Student )
    }


setSelectedRoom : Maybe ( RoomID, Room ) -> SelectedItemsInList -> SelectedItemsInList
setSelectedRoom room selectedItems =
    { selectedItems | room = room }


setSelectedLect : Maybe ( LecturerID, Lecturer ) -> SelectedItemsInList -> SelectedItemsInList
setSelectedLect lect selectedItems =
    { selectedItems | lect = lect }


setSelectedEvent : Maybe ( EventID, Event ) -> SelectedItemsInList -> SelectedItemsInList
setSelectedEvent event selectedItems =
    { selectedItems | event = event }


setSelectedBlock : Maybe ( BlockID, Block ) -> SelectedItemsInList -> SelectedItemsInList
setSelectedBlock block selectedItems =
    { selectedItems | block = block }


setSelectedStudent : Maybe ( StudentID, Student ) -> SelectedItemsInList -> SelectedItemsInList
setSelectedStudent student selectedItems =
    { selectedItems | student = student }


init : Data -> () -> ( Model, Effect Msg )
init data () =
    ( { data = data
        , filters = ScheduleFilter (\_ _ -> False) (\_ _ -> False) (\_ _ -> False) (\_ _ -> False) (\_ _ -> False) (\_ _ -> False)
        , draggable = dnd.model
        , selectedItems = SelectedItemsInList Nothing Nothing Nothing Nothing Nothing
        , recommendations = []
      }
    , Effect.none
    )