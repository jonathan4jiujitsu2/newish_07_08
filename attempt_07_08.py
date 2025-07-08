# -----------------------------------------------------------------------------
#  Mirror‑symmetric 8‑pole strip‑line band‑pass filter
#  • IronPython 2.7 macro for Ansys Electronics Desktop / HFSS 2023‑R2+
#  • Generates PEC resonators, feed, stack‑up, and wave‑ports
#  • All dimensions are driven by the variable table at the top
# -----------------------------------------------------------------------------
import ScriptEnv, math
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
dsk   = ScriptEnv.GetDesktop()
dsk.NewProject()
prj   = dsk.GetActiveProject()
des   = prj.InsertDesign("HFSS", "Filter", "DrivenModal", "")
edt   = des.SetActiveEditor("3D Modeler")
edt.SetModelUnits(["NAME:Units Parameter", "Units:=", "mm"])

# ── units & helpers ───────────────────────────────────────────────────────────
mil = 0.0254
mm  = lambda v_mil: "{}mm".format(v_mil * mil)

# ── global parameters (from drawings) ────────────────────────────────────────
edge_wall_pullback  = 20.0       # mil
Wio                 = 66.0
Port_Width          = 66.0
Lio                 = 315.0
Launch_width        = 20.0
Launch_spacing      = 30.0
XYSpacing_scale     = 1.00
feed_angle_deg      = -20.0

# resonators (8 poles, mirrored)
Res_dir       = [1,3,2,4, 3,1,4,2]       # 1=gapR 2=L 3=T 4=B
Res_tot_len   = [200]*8                  # mil
Res_trace_w   = [10 ]*8
Res_trace_gap = [5  ]*8
Res_x_spacing = [40,15,40]               # inter‑column (mil)
Res_y_spacing = [25]                     # inter‑row   (mil)

# launch path segments (name, dx, dy) mil
launch_seg = [("Lio_one",    0,   Lio),
              ("Lio_two",   XYSpacing_scale*Res_x_spacing[0], 0),
              ("Lio_three", 20,   20),
              ("Lio_four",   0,  -20),
              ("Lio_five",   0,  -Launch_spacing),
              ("Lio_six",    0,  -Res_y_spacing[0]*XYSpacing_scale),
              ("Lio_seven",  0,  -Res_y_spacing[0]*XYSpacing_scale),
              ("Lio_eight",  Lio, 0)]

# stack‑up (single layer above & below signal)
core_h     = 10.0*mil
prepreg_h  = 1.6*mil
cond_thk   = 1.0*mil

# ── materials ────────────────────────────────────────────────────────────────
mat = prj.GetDefinitionManager()
mat.AddMaterial(["NAME:MY_CORE",    "permittivity:=", "3.48", "dielectric_loss_tangent:=", "0.003"])
mat.AddMaterial(["NAME:MY_PREPREG", "permittivity:=", "2.90", "dielectric_loss_tangent:=", "0.002"])
mat.AddMaterial(["NAME:MY_CU",      "conductivity:=", "5.8e7" ])

# ── helper: resonator side length ────────────────────────────────────────────
def ring_side(L,w,g): return (L+g)/4.0 + w

# ── draw one resonator sheet ─────────────────────────────────────────────────
def draw_res(idx, xc, yc):
    L, w, g, dir = Res_tot_len[idx], Res_trace_w[idx], Res_trace_gap[idx], Res_dir[idx]
    s = ring_side(L,w,g)
    pts = [(0,0),(0,s+g/2),(-w,s+g/2),(-w,-w),(s+w,-w),(s+w,s+w),
           (-w,s+w),(-w,-g/2),(0,-g/2)]
    if dir==2: pts = [(-x,y) for x,y in pts]
    if dir==3: pts = [(-y,x) for x,y in pts]
    if dir==4: pts = [( y,-x) for x,y in pts]
    p3d = []
    for x,y in pts:
        p3d.append(["NAME:PLPoint","X:=",mm(xc+x),"Y:=",mm(yc+y),"Z:=","0mm"])
    seg = [["NAME:PLSegment","SegmentType:=","Line","StartIndex:=",i,"NoOfPoints:=",2] for i in range(len(pts))]
    edt.CreatePolyline(
        ["NAME:PolylineParameters","IsPolylineCovered:=",True,"IsPolylineClosed:=",True,
         ["NAME:PolylinePoints"]+p3d, ["NAME:PolylineSegments"]+seg,
         ["NAME:PolylineXSection","XSectionType:=","None"]],
        ["NAME:Attributes","Name:=","Res{}".format(idx+1),
         "MaterialName:=","MY_CU","SolveInside:=",False])

# ── place resonators ─────────────────────────────────────────────────────────
xcol = [0.0]
for k,dx in enumerate(Res_x_spacing):
    left = ring_side(Res_tot_len[k],   Res_trace_w[k],   Res_trace_gap[k])
    right= ring_side(Res_tot_len[k+1], Res_trace_w[k+1], Res_trace_gap[k+1])
    xcol.append(xcol[-1] + (left+right)/2.0 + dx*XYSpacing_scale)
yRow = (ring_side(Res_tot_len[0],Res_trace_w[0],Res_trace_gap[0]) +
        Res_y_spacing[0]*XYSpacing_scale)/2.0
for c in range(4):  draw_res(c,   xcol[c]*mil,  yRow*mil)
for c in range(4):  draw_res(c+4, xcol[c]*mil, -yRow*mil)

# ── build launch trace ───────────────────────────────────────────────────────
parts=[]; x0=-(edge_wall_pullback+Port_Width/2.0); y0=0.0
for name,dx,dy in launch_seg:
    w = Wio if name=="Lio_one" else Launch_width
    ln = math.hypot(dx,dy); ang = math.degrees(math.atan2(dy,dx)) if ln else 0
    edt.CreateRectangle(
        ["NAME:RectangleParameters","IsCovered:=",True,
         "XStart:=",mm(x0),"YStart:=",mm(y0-w/2),"ZStart:=","0mm",
         "Width:=",mm(ln),"Height:=",mm(w)],
        ["NAME:Attributes","Name:=",name,"MaterialName:=","MY_CU","SolveInside:=",False])
    if ang: edt.Rotate(["NAME:Selections","Selections:=",name,"NewPartsModelFlag:=","Model"],
                       ["NAME:RotateParameters","RotateAxis:=","Z","RotateAngle:=","{}deg".format(ang)])
    x0+=dx; y0+=dy; parts.append(name)
edt.Unite(["NAME:Selections","Selections:=",",".join(parts)],
          ["NAME:UniteParameters","KeepOriginals:=",False])
edt.ChangeProperty(["NAME:AllTabs",
                    ["NAME:Geometry3DAttributeTab",
                     ["NAME:PropServers",parts[0]],
                     ["NAME:ChangedProps",["NAME:Name","Value:=","FeedLine"]]])

# ── substrate & ground planes ───────────────────────────────────────────────
xl = -(edge_wall_pullback + Lio + Port_Width)*mil
xr =  (edge_wall_pullback + xcol[-1] + ring_side(Res_tot_len[3],Res_trace_w[3],Res_trace_gap[3]))*mil
yt =  (edge_wall_pullback + yRow + ring_side(Res_tot_len[0],Res_trace_w[0],Res_trace_gap[0]))*mil
yb = -yt
core_z0 = -core_h-prepreg_h
edt.CreateBox(["NAME:BoxParameters","XPosition:=",mm(xl),"YPosition:=",mm(yb),
               "ZPosition:=",mm(core_z0),"XSize:=",mm(xr-xl),"YSize:=",mm(yt-yb),
               "ZSize:=",mm(core_h)],
              ["NAME:Attributes","Name:=","SUB_CORE_BOT","MaterialName:=","MY_CORE","SolveInside:=",True])
edt.CreateBox(["NAME:BoxParameters","XPosition:=",mm(xl),"YPosition:=",mm(yb),
               "ZPosition:=","0mm","XSize:=",mm(xr-xl),"YSize:=",mm(yt-yb),
               "ZSize:=",mm(prepreg_h)],
              ["NAME:Attributes","Name:=","PREPREG","MaterialName:=","MY_PREPREG","SolveInside:=",True])
edt.CreateBox(["NAME:BoxParameters","XPosition:=",mm(xl),"YPosition:=",mm(yb),
               "ZPosition:=",mm(prepreg_h),"XSize:=",mm(xr-xl),"YSize:=",mm(yt-yb),
               "ZSize:=",mm(core_h)],
              ["NAME:Attributes","Name:=","SUB_CORE_TOP","MaterialName:=","MY_CORE","SolveInside:=",True])
# copper reference planes
edt.CreateRectangle(["NAME:RectangleParameters","IsCovered:=",True,
                     "XStart:=",mm(xl),"YStart:=",mm(yb),
                     "ZStart:=",mm(core_z0-cond_thk),"Width:=",mm(xr-xl),"Height:=",mm(yt-yb),"WhichAxis:=","Z"],
                    ["NAME:Attributes","Name:=","GND_BOT","MaterialName:=","MY_CU","SolveInside:=",False])
edt.CreateRectangle(["NAME:RectangleParameters","IsCovered:=",True,
                     "XStart:=",mm(xl),"YStart:=",mm(yb),
                     "ZStart:=",mm(prepreg_h+core_h),"Width:=",mm(xr-xl),"Height:=",mm(yt-yb),"WhichAxis:=","Z"],
                    ["NAME:Attributes","Name:=","GND_TOP","MaterialName:=","MY_CU","SolveInside:=",False])

# ── simple wave‑ports (left & right) ─────────────────────────────────────────
bnd = des.GetModule("BoundarySetup")
# Port1
edt.CreateRectangle(["NAME:RectangleParameters","IsCovered:=",True,
                     "XStart:=",mm(-(edge_wall_pullback+Port_Width)),"YStart:=",mm(-Port_Width/2),
                     "ZStart:=","0mm","Width:=",mm(Port_Width),"Height:=",mm(Port_Width),"WhichAxis:=","X"],
                    ["NAME:Attributes","Name:=","Port1_sheet","MaterialName:=","air","SolveInside:=",True])
bnd.AssignWavePort(["NAME:Port1","Objects:",["Port1_sheet"],"NumModes:=",1,
                    "RenormalizeAllTerminals:=",True])

# Port2 (mirror)
edt.CreateRectangle(["NAME:RectangleParameters","IsCovered:=",True,
                     "XStart:=",mm(xr),"YStart:=",mm(-Port_Width/2),
                     "ZStart:=","0mm","Width:=",mm(Port_Width),"Height:=",mm(Port_Width),"WhichAxis:=","X"],
                    ["NAME:Attributes","Name:=","Port2_sheet","MaterialName:=","air","SolveInside:=",True])
bnd.AssignWavePort(["NAME:Port2","Objects:",["Port2_sheet"],"NumModes:=",1,
                    "RenormalizeAllTerminals:=",True])

# ── analysis setup & sweep ───────────────────────────────────────────────────
setup = des.GetModule("AnalysisSetup")
setup.InsertSetup("HfssDriven",
    ["NAME:Setup1","Frequency:=","15GHz","MaxDeltaS:=",0.01,
     "MaximumPasses:=",15,"MinimumPasses:=",1])
setup.InsertFrequencySweep("Setup1",
    ["NAME:Sweep","Type:=","Interpolating","StartFrequency:=","10GHz",
     "StopFrequency:=","20GHz","StepSize:=","0.02GHz"])

# ── save project ─────────────────────────────────────────────────────────────
prj.SaveAs(dsk.GetDirectory()+"\\Mirror8Pole_filter.aedt",True)
