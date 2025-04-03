Attribute VB_Name = "Module1"
Function CountColor(rng As Range, colorcell As Range) As Long
    Dim cell As Range
    Dim clr As Long
    clr = colorcell.Interior.Color
    For Each cell In rng
        If Evaluate("GetColor(" & cell.Address(External:=True) & ")") = clr Then
            CountColor = CountColor + 1
        End If
    Next cell
End Function

Function GetColor(cell As Range) As Long
    GetColor = cell.DisplayFormat.Interior.Color
End Function

Sub addPic()
    Dim pic_file As String
    Dim pic_resolution As Long
    Dim pict As Object
    
    If ActiveCell.Comment Is Nothing Then ActiveCell.AddComment
    pic_file = Application.GetOpenFilename("PNG (*.PNG), *.PNG", Title:="Select chord picture: ")
    Set pict = CreateObject("WIA.ImageFile")
    pict.loadfile pic_file
    pic_resolution = pict.VerticalResolution
    
  With ActiveCell.Comment.Shape
     .Fill.Visible = msoTrue
     .Fill.UserPicture (pic_file)
     .Height = pict.Height / pic_resolution * 45
     .Width = pict.Width / pic_resolution * 45
   End With
 
  Set pict = Nothing
   
  ActiveCell.Comment.Visible = False
End Sub
