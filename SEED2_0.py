# Main SEED 2.0 Code
# Created by Michael Vause, 12/06/2020

# Import all required modules
try:
    import sys
    from sys import platform
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox
    from tkinter import filedialog as fd
    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import os
    import io
    from PIL import Image, ImageTk
    from urllib.request import urlopen
    import ssl
    import pysindy as ps
    import ast
    from scipy.signal import savgol_filter
    import csv
    import webbrowser
except ImportError as e:
    print("Install the required modules before starting. " + e)
    sys.exit()
except Exception as err:
    print("Error while importing: " + str(err))
    sys.exit()

# Any global variables used throughout Seed 2.0

pysindypath = os.path.dirname(ps.__file__) # Find file path for pysindy module
hidden = False # Is the file own data browser button shown
to_open = " " # Variable storing the filepath for the own data file
adv = False # Is the advanced options panel shown
opt_widgets = [] # Storing information for the advanced optimization option widgets
diff_widgets = [] # Storing information for the advanced differentiation option widgets

# Any functions used throughout SEED 2.0

# Function to run on closing the window
def on_closing():    
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        window.destroy()

# Take a file path and return all of the non hidden files
def non_hidden(path):
    files = [file for file in os.listdir(path) if not file.startswith(".")]
    return files

# Show & hide the file browser button depending on whether or not own data is selected
def toggle_browser(command):
    global hidden
    global to_open
    filename = to_open.split('/')[-1] # Show filename portion of filepath
    sel_op = sel_var.get()
    if sel_op == "Own Data": # Show/hide browser widgets depending on previous state
        if hidden:
            file_button.grid()
            file_label.configure(text="File Selected: " + filename)
            hidden = False
        else:
            pass
    else:# If own data not selected, hide everything
        if not hidden:
            file_button.grid_remove()
            file_label.configure(text=" ")
            hidden = True
        else:
            pass

# Show file browser
def browse():
    global to_open
    to_open = fd.askopenfilename(initialdir = "/", filetypes = (("CSV files", "*.csv"), ("all files", "*.*")))
    filename = to_open.split('/')[-1]
    file_label.configure(text="File Selected: " + filename) # Update label to show selected file

# Hide and show optimization/differentiation option variable selection
def advanced():
    global adv

    if(adv):
        size = str(min_w)+"x"+str(min_h)
        adv_button["text"] = "Show Advanced"
        adv = False
    elif(not adv):
        size = adv_size
        adv_button["text"] = "Hide Advanced"
        adv = True
    
    window.geometry(size)

# Get optimizer or differentiator selection class name
def get_od_class(selection):
    if(selection == "opt"):
        opt = str(opt_var.get())
        fil = open(pysindypath+"/optimizers/"+opt+".py")
    elif(selection == "diff"):
        diff = str(diff_var.get())
        fil = open(pysindypath+"/differentiation/"+diff+".py")

    contents = fil.read()
    par = ast.parse(contents)
    classes = [node.name for node in ast.walk(par) if isinstance(node, ast.ClassDef)]
    return classes[0]

# Get optimization option variables and update on advanced option panel
def get_opt(command):
    class_name = get_od_class("opt")
    opt_inst = eval("ps."+class_name+"()")
    opt_params = opt_inst.get_params()

    disp_opt_select(opt_params)

# Display the optimization option variables on advanced option panel
def disp_opt_select(opt_params):
    global opt_fram
    global opt_widgets
    opt_widgets = []
    opt_fram.destroy() # Remove all current widgets in advanced option panel to repopulate with new selection variables

    opt_fram = tk.Frame(window,bd=2,bg=bgc,width=5)

    ofram_label = tk.Label(opt_fram,text="Optimization Option Variables",font=("Times",18,"bold"),pady=10,bg=bgc)
    ofram_label.grid(row=0,column=0,sticky="W")

    var_list = list(opt_params)
    for x in range(len(var_list)): # Create a widget for all inbuilt parameters 
        var_label = tk.Label(opt_fram,text=var_list[x],font=("Times",15,"bold"),pady=10,bg=bgc)
        var_label.grid(row=x+1,column=0,sticky="E")

        if str(opt_params[var_list[x]]) == "True" or str(opt_params[var_list[x]]) == "False": # Create dropdown with True/False option for boolean variables
            ovar_x = tk.StringVar(opt_fram)
            ovar_options = ["True", "False"]
            ovar_x.set(str(opt_params[var_list[x]]))

            opt_widgets.append([var_label,tk.OptionMenu(opt_fram,ovar_x,*ovar_options),type(opt_params[var_list[x]]),ovar_x])
            opt_widgets[x][1].config(width=drop_w,font=("Times",15),bg=bgc)
        else: # For any other variable input type, create an entry box and enter default value
            opt_widgets.append([var_label,type(opt_params[var_list[x]]),tk.Entry(opt_fram,font=("Times",15),highlightbackground=bgc,width=drop_w)])
            opt_widgets[x][2].insert(0, str(opt_params[var_list[x]]))

        opt_widgets[x][5-len(opt_widgets[x])].grid(row=x+1,column=1)

    opt_fram.grid(row=4,column=4,rowspan=len(var_list),padx=5,sticky="W")

# Get differentiation option variables
def get_diff(command):
    diff_param_def = []
    class_name = get_od_class("diff")

    diff_params = list(eval("ps."+class_name+".__init__.__code__.co_varnames")) # Make instance of the differentiator class and get inbuilt parameters
    if "self" in diff_params:
        diff_params.remove("self")

    temp_params = eval("ps."+class_name+".__init__.__defaults__") # Get inbuilt parameter default values
    diff_param_def[:] = [(("func "+thing.__name__) if(callable(thing)) else thing) for thing in temp_params] # If the input type for a deafult value is a function, enter func at the start

    disp_diff_select(diff_params, diff_param_def)

# Display the differentiation option variables on GUI
def disp_diff_select(diff_params, diff_param_def):
    global diff_fram
    global diff_widgets
    diff_widgets = []
    diff_fram.destroy()

    diff_fram = tk.Frame(window,bd=2,bg=bgc,width=5)

    dfram_label = tk.Label(diff_fram,text="Differentiation Option Variables",font=("Times",18,"bold"),pady=10,bg=bgc)
    dfram_label.grid(row=0,column=0,sticky="W")

    for x in range(len(diff_params)):
        var_label = tk.Label(diff_fram,text=diff_params[x],font=("Times",15,"bold"),pady=10,bg=bgc)
        var_label.grid(row=x+1,column=0,sticky="E")

        if(x+1>len(diff_param_def)): # If there's an empty variable, create an empty entry box
            diff_widgets.append([var_label,type(""),tk.Entry(diff_fram,font=("Times",15),highlightbackground=bgc,width=drop_w)])
        elif str(diff_param_def[x]) == "True" or str(diff_param_def[x]) == "False": # Create dropdown for boolean variables
            dvar_x = tk.StringVar(diff_fram)
            dvar_options = ["True", "False"]
            dvar_x.set(str(diff_param_def[x]))

            diff_widgets.append([var_label,tk.OptionMenu(diff_fram,dvar_x,*dvar_options),type(diff_param_def[x]),dvar_x])
            diff_widgets[x][1].config(width=drop_w,font=("Times",15),bg=bgc)
        else: # Create an entry box for any other variables and enter deafualt value
            diff_widgets.append([var_label,type(diff_param_def[x]),tk.Entry(diff_fram,font=("Times",15),highlightbackground=bgc,width=drop_w)])
            diff_widgets[x][2].insert(0, diff_param_def[x])

        diff_widgets[x][5-len(diff_widgets[x])].grid(row=x+1,column=1)

    for y in range(len(diff_params)+1,4): # Fill in the rest of the frame with blank lines
        blank = tk.Label(diff_fram,text=" ",font=("Times",15,"bold"),pady=10,bg=bgc)
        blank.grid(row=y,column=0)
    
    diff_fram.grid(row=0,column=4,rowspan=4,padx=5,sticky="W")

# Instantiate the differentiator or optimizer
def od_inst(widget_list,selection):
    class_name = get_od_class(selection)

    instance = "ps."+class_name+"("
    count = 0

    for widget in widget_list: # Form executable line in a string
        value = None
        try: # For option menu widgets
            value = widget[3].get()
        except Exception: # For entry widgets
            value = widget[2].get()

        if(str(widget[-2]) == "<class 'str'>" and not value.startswith("func")):
            value = "\"" + value + "\""
        elif(str(widget[-2]) == "<class 'str'>" and value.startswith("func")):
            value = value.split(' ', 1)[1]

        var_name = widget[0].cget("text")

        if(not value == "\"\""):
            instance = instance + var_name + "=" + value
            if(count+1<len(widget_list)):
                instance = instance + ","
        
        count += 1

    instance = instance + ")"

    inst = eval(instance) # Instantiate the line
    return inst

# Get feature library selection class name
def get_feat_class():
    feat = str(feat_var.get())
    fil = open(pysindypath+"/feature_library/"+feat+".py")

    contents = fil.read()
    par = ast.parse(contents)
    classes = [node.name for node in ast.walk(par) if isinstance(node, ast.ClassDef)]
    return classes[0]

# Instantiate the feature library
def feat_inst():
    class_name = get_feat_class()
    instance = "ps."+class_name+"()"
    inst = eval(instance)
    return inst

# Reset opt and diff advanced options to default values
def reset():
    get_opt("<command>")
    get_diff("<command>")

# Read selected file and return array with data
def read_file():
    if(sel_var.get() == "Own Data"):
        to_read = to_open      
    else:
        to_read = "./data/" + sel_var.get()

    with open(to_read, newline='') as csvfile:
        data = list(csv.reader(csvfile))  

    return(data)

# Create output window
def show_output(table_size, coefs, feats, variable_names):
    out_window = tk.Tk()
    out_window.title("Model Output: " + str(sel_var.get()))
    out_window.config(bg=bgc)

    # Create all output widgets
    tv = create_table(out_window, table_size, variable_names)
    if(len(coefs) < 6):
        create_plot(out_window)
    create_eq_box(out_window, coefs, feats, variable_names)

    # Populate output widgets
    pop_table(tv, coefs, feats)
    if(len(coefs) < 6):
        pop_plot(coefs, feats, variable_names)

    out_window.mainloop()

# Create output table
def create_table(out_window, table_size, variable_names):
    # Create frame for output values title & treeview table
    fig1_fram = tk.Frame(out_window,bd=2,bg=bgc,width=5)

    fig1_label = tk.Label(fig1_fram,text="Coefficient Values",font=("Times",18,"bold"),pady=10,bg=bgc)
    fig1_label.grid(row=0,column=0,sticky="W")

    y_scroll = tk.Scrollbar(fig1_fram)
    y_scroll.grid(row=1,column=1,rowspan=4,sticky="nsew")
    x_scroll = tk.Scrollbar(fig1_fram,orient=tk.HORIZONTAL)
    x_scroll.grid(row=2,column=0,columnspan=1,sticky="nsew")

    tv = ttk.Treeview(fig1_fram, xscrollcommand = x_scroll.set, yscrollcommand = y_scroll.set)
    tv = resize_table(table_size, tv, fig1_fram, x_scroll, y_scroll, variable_names) # Make table the correct size for the output model

    fig1_fram.grid(row=0,column=0,rowspan=3,columnspan=3,padx=5,sticky="NW")

    return tv

# Create output plot
def create_plot(out_window):
    # Create frame for output graph title & plot
    fig2_fram = tk.Frame(out_window,bd=2,bg=bgc)

    fig2_label = tk.Label(fig2_fram,text="Coefficient Plot",font=("Times",18,"bold"),pady=10,bg=bgc)
    fig2_label.grid(row=0,column=0,sticky="NW")

    fig2 = plt.figure()
    fig2.add_subplot(111)
    fig2.patch.set_facecolor(bgc)
    fig2.subplots_adjust(left=0.07,hspace=0.4)
    canvas = FigureCanvasTkAgg(fig2, fig2_fram)
    canvas.get_tk_widget().grid(row=1,column=0,sticky="NW")
    canvas.get_tk_widget().configure(background=bgc,width=(fig_w),height=(fig_h))

    fig2_fram.grid(row=0,column=3,rowspan=4,columnspan=3,padx=5,sticky="NW")

# Create scrollable box for output equations
def create_eq_box(out_window, coefs, feats, variable_names):
    # Create frame for a scrollable box for the output equations
    fig3_fram = tk.Frame(out_window,bd=2,bg=bgc)

    fig3_label = tk.Label(fig3_fram,text="Output Equations",font=("Times",18,"bold"),pady=10,bg=bgc)  
    fig3_label.grid(row=0,column=0,sticky="NW")

    x_scroll = tk.Scrollbar(fig3_fram,orient="horizontal")
    x_scroll.grid(row=2,column=0,sticky="nsew")
    y_scroll = tk.Scrollbar(fig3_fram)
    y_scroll.grid(row=1,column=3,rowspan=3,sticky="nsew")

    eq_text = tk.Text(fig3_fram,wrap="none",xscrollcommand=x_scroll.set,yscrollcommand=y_scroll.set,font=("Times",15),height=10,pady=10,bg=bgc)
    eq_text.grid(row=1,column=0)

    eqn_num = len(coefs)

    for num in range(eqn_num): # Form each of the equations to print to the text box
        eqn = coefs[num]
        eqn = [round(float(item),3) for item in eqn]
        out = "d" + str(variable_names[num]) + "/dt = "
        for val in range(len(feats)):
            coef = eqn[val]
            desc = feats[val]
            if(coef != 0):
                if(float(coef) < 0):
                    out = out.rstrip("+ ")
                    out = out + " "

                out = out + str(coef) + " "
                if(desc == "1"):
                    out = out + "+ "
                else:
                    out = out + str(desc) + " + "

        out = out.rstrip("+ ")
        out = out + "    \n \n"
        eq_text.insert("end", out)

    eq_text.config(state="disabled")
    x_scroll.config(command=eq_text.xview)
    y_scroll.config(command=eq_text.yview)

    fig3_fram.grid(row=3,column=0,rowspan=4,columnspan=3,padx=5,sticky="NW")

# Resize output table
def resize_table(cols, tv, fig1_fram, x_scroll, y_scroll, variable_names):
    tv = ttk.Treeview(fig1_fram, xscrollcommand = x_scroll.set, yscrollcommand = y_scroll.set)

    tv['columns'] = ('col1',)
    if(cols > 1):
        for x in range(2, cols+1):
            name = 'col' + str(x)
            tv['columns'] = tv['columns']+(name,)

    tv.heading("#0", text='Descriptor', anchor='w')

    if(cols<3):
        tv.column("#0", anchor="w", width=(cols+1)*col_width, minwidth=col_width, stretch=True) 
    else:
        tv.column("#0", anchor="w", width=4*col_width, minwidth=col_width, stretch=True)

    for x in range(cols):
        head = 'd' + str(variable_names[x]) + "/dt"
        column = 'col' + str(x+1)
        tv.heading(column,text=head)
        tv.column(column, anchor='center', width=0, minwidth=col_width, stretch=True)

    tv.grid(row=1,column=0,columnspan=1)

    y_scroll.config(command = tv.yview)
    x_scroll.config(command = tv.xview)

    fig1_fram.grid()
    return tv

# Populate the output table with coefficients
def pop_table(tv, coefs, feats):
    for item in range(len(coefs[0])):
        new_val = []
        for col in range(len(coefs)):
            new_val.append(str(coefs[col,item]))
        tv.insert('', 'end', text=str(feats[item]), values=new_val)

# Populate the output plot
def pop_plot(coefs, feats, variable_names):
    rows = len(coefs)
    length = len(coefs[0])

    for row_no in range(rows): # For each input variable, make a list of non zero output coefficients
        coef_plt = []
        desc_plt = []
        row = coefs[row_no]
        for item in range(length):
            val = row[item]
            des = feats[item]
            if val != 0:
                coef_plt.append(val)
                desc_plt.append(des)
        if length > 3:
            size = 8
        else:
            size = 10
        matplotlib.rc('xtick', labelsize=size)
        subp = plt.subplot(rows,1,(row_no+1))
        plt.bar(desc_plt,coef_plt)
        plt.axhline(y=0, color='k')
        subp.set_title("d" + str(variable_names[row_no]) + "/dt",size=10)

    # Update plot
    plt.tight_layout()
    plt.gcf().canvas.draw()

# Run the main computation
def comp():
    if((to_open.split('/')[-1] == "" or to_open.split('/')[-1] == " ") and sel_var.get() == "Own Data"):
        tk.messagebox.showerror(title="Select File", message="You need to select a file to compute!")
        return None

    try:
        opt = od_inst(opt_widgets,"opt")
    except Exception:
        tk.messagebox.showerror(title="Invalid Option", message="You have input an invalid optimization variable, check the PySINDy documentation for valid options.")
        return None

    try:
        diff = od_inst(diff_widgets,"diff")
    except Exception:
        tk.messagebox.showerror(title="Invalid Option", message="You have input an invalid differentation variable, check the PySINDy documentation for valid options.")
        return None

    feat = feat_inst()

    data = read_file()
    variable_names = data[0][1:]
    
    contents = data # Separate the input file into data, time series and variable names
    del contents[0]
    time_series = [val[0] for val in contents]
    dt = float(time_series[1])-float(time_series[0])

    contents = [val[1:] for val in contents]
    contents = np.array([[float(val) for val in item] for item in contents])
    table_size = len(contents[0])

    model = ps.SINDy(differentiation_method=diff,optimizer=opt,feature_library=feat,feature_names=variable_names) # Instantiate the model with the input data
    model.fit(contents, t=dt)
    coefs = model.coefficients()
    feats = model.get_feature_names()

    show_output(table_size, coefs, feats, variable_names)

# GUI design

bgc = "lightgray" # GUI background colour

# Size Correction based on operating system
if platform == "darwin": # MacOS
    print("MacOS detected")
    min_w = 520
    max_w = 1200
    min_h = 550
    max_h = 680
    drop_w = 30
    fram_w = 62
    line_w = 61
    col_width = 160
    fig_w = 400
    fig_h = 450
    adv_size = "1050x610"
else:
    print(platform + " detected")
    min_w = 690
    max_w = 1400
    min_h = 610
    max_h =700
    drop_w = 30
    fram_w = 55
    line_w = 60
    col_width = 160
    fig_w = 720
    fig_h = 450
    adv_size = "1380x670"

# GUI window
window = tk.Tk()
window.title("Extracting Equations from Data")
window.minsize(min_w,min_h)
window.maxsize(max_w,max_h)
window.config(bg=bgc)

# Add Durham University logo to GUI
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

try:
    pic_url = "https://github.com/M-Vause/SEED2.0/blob/master/images/DurhamUniversityMasterLogo_RGB.png?raw=true"
    my_page = urlopen(pic_url)
    my_picture = io.BytesIO(my_page.read())
    pil_img = Image.open(my_picture)
    newsize = (167, 69) 
    pil_img = pil_img.resize(newsize)

    tk_img = ImageTk.PhotoImage(pil_img)
    label = tk.Label(window, image=tk_img, bg=bgc)
    label.grid(row=0,column=0,padx=5, pady=5,rowspan=2)
except Exception as err:
    print("No Internet Connection, Durham University Logo Not Printing")

# Add main label and the data dropdown label
main_label1 = tk.Label(window,text="Extracting Equations",font=("Times",30,"bold","underline"),padx=5,pady=10,bg=bgc)
main_label1.grid(row=0,column=1,columnspan=3,sticky="S")

main_label2 = tk.Label(window,text="from Data",font=("Times",30,"bold","underline"),padx=5,pady=10,bg=bgc)
main_label2.grid(row=1,column=1,columnspan=3,sticky="N")

select_label = tk.Label(window,text="Example/Own Data:",font=("Times",15,"bold"),pady=10,bg=bgc)
select_label.grid(row=2,column=0,sticky="E")

# Creating dropdown for data selection
sel_var = tk.StringVar(window)
temp_options = non_hidden("./data")
if "__pycache__" in temp_options:
    temp_options.remove("__pycache__")
ext = ".txt"
sel_options = [eg.split(ext, 1)[0] for eg in temp_options]
sel_options.sort()
sel_options.append("Own Data")
sel_var.set("data_Lorenz3d.csv")
temp_options.clear()

select_menu = tk.OptionMenu(window,sel_var,*sel_options,command=toggle_browser)
select_menu.config(width=drop_w,font=("Times",15),bg=bgc)
select_menu.grid(row=2,column=1,columnspan=3,sticky="nsew")

# All file browser widgets
file_button = tk.Button(window,text="Select File",font=("Times",15),width=15,highlightbackground=bgc,command=browse)
file_button.grid(row=3,column=0,sticky="E")

file_label = tk.Label(window,text=" ",font=("Times",15),pady=10,bg=bgc)
file_label.grid(row=3,column=1,columnspan=3,sticky="W")

toggle_browser("<command>")

# Optimization options
opt_label = tk.Label(window,text="Optimization Option:",font=("Times",15,"bold"),pady=10,bg=bgc)
opt_label.grid(row=5,column=0,sticky="E")

opt_var = tk.StringVar(window)
temp_options = non_hidden(pysindypath+"/optimizers")
if "__pycache__" in temp_options:
    temp_options.remove("__pycache__")
if "__init__.py" in temp_options:
    temp_options.remove("__init__.py")
if "base.py" in temp_options:
    temp_options.remove("base.py")
if "sindy_optimizer.py" in temp_options:
    temp_options.remove("sindy_optimizer.py")
#temp_options.append("Lasso")
ext = ".py"
opt_options = [eg.split(ext, 1)[0] for eg in temp_options]
opt_options.sort()
opt_var.set("stlsq")
temp_options.clear()

opt_menu = tk.OptionMenu(window,opt_var,*opt_options,command=get_opt)
opt_menu.config(width=drop_w,font=("Times",15),bg=bgc)
opt_menu.grid(row=5,column=1,columnspan=3,sticky="nsew")

# Differentiation options
diff_label = tk.Label(window,text="Differentiation Option:",font=("Times",15,"bold"),pady=10,bg=bgc)
diff_label.grid(row=4,column=0,sticky="E")

diff_var = tk.StringVar(window)
temp_options = non_hidden(pysindypath+"/differentiation")
if "__pycache__" in temp_options:
    temp_options.remove("__pycache__")
if "__init__.py" in temp_options:
    temp_options.remove("__init__.py")
if "base.py" in temp_options:
    temp_options.remove("base.py")
ext = ".py"
diff_options = [eg.split(ext, 1)[0] for eg in temp_options]
diff_options.sort()
#diff_options.append("pre-computed")
diff_var.set("finite_difference")
temp_options.clear()

diff_menu = tk.OptionMenu(window,diff_var,*diff_options,command=get_diff)
diff_menu.config(width=drop_w,font=("Times",15),bg=bgc)
diff_menu.grid(row=4,column=1,columnspan=3,sticky="nsew")

# Feature library options
feat_label = tk.Label(window,text="Feature Library Option:",font=("Times",15,"bold"),pady=10,bg=bgc)
feat_label.grid(row=6,column=0,sticky="E")

feat_var = tk.StringVar(window)
temp_options = non_hidden(pysindypath+"/feature_library")
if "__pycache__" in temp_options:
    temp_options.remove("__pycache__")
if "__init__.py" in temp_options:
    temp_options.remove("__init__.py")
if "custom_library.py" in temp_options:
    temp_options.remove("custom_library.py")
if "feature_library.py" in temp_options:
    temp_options.remove("feature_library.py")
ext = ".py"
feat_options = [eg.split(ext, 1)[0] for eg in temp_options]
feat_options.sort()
feat_var.set("polynomial_library")
temp_options.clear()

feat_menu = tk.OptionMenu(window,feat_var,*feat_options)
feat_menu.config(width=drop_w,font=("Times",15),bg=bgc)
feat_menu.grid(row=6,column=1,columnspan=3,sticky="nsew")

# Add frame for compute button
button_fram = tk.Frame(window,bg=bgc,bd=2,relief="sunken",pady=10,width=fram_w)

tut_button = tk.Button(button_fram,text="Tutorial",font=("Times",15,"bold"),width=15,highlightbackground=bgc,command=lambda : webbrowser.open("https://github.com/M-Vause/SEED2.0"))
tut_button.grid(row=0,column=0,columnspan=2,sticky="EW")

adv_button = tk.Button(button_fram,text="Show Advanced",font=("Times",15,"bold"),width=15,highlightbackground=bgc,command=advanced)
adv_button.grid(row=0,column=2,columnspan=2,sticky="EW")

blank_line1 = tk.Label(button_fram,text=" ",font=("Times",15),width=round(line_w/2),highlightbackground=bgc,bg=bgc)
blank_line1.grid(row=1,column=0,columnspan=2)

reset_button = tk.Button(button_fram,text="Reset to Defaults",font=("Times",15,"bold"),width=15,highlightbackground=bgc,command=reset)
reset_button.grid(row=1,column=2,columnspan=2,sticky="EW")

blank_line2 = tk.Label(button_fram,text=" ",font=("Times",15),width=line_w,highlightbackground=bgc,bg=bgc)
blank_line2.grid(row=2,column=0,columnspan=4)

comp_button = tk.Button(button_fram,text="Compute",font=("Times",15,"bold"),width=10,highlightbackground=bgc,command=comp)
comp_button.grid(row=3,column=0,columnspan=4,sticky="EW")

button_fram.grid(row=7,column=0,columnspan=4,padx=5,sticky="SEW")

# Frame for optimization option variable selection
opt_fram = tk.Frame(window,bd=2,bg=bgc,width=5)
get_opt("<command>")

# Frame for differentitation option variable selection
diff_fram = tk.Frame(window,bd=2,bg=bgc,width=5)
get_diff("<command>")

# Resize window
size = str(min_w) + "x" + str(min_h)
window.geometry(size)

# Enter mainloop
window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()
