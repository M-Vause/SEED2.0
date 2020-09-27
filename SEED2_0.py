# Main SEED 2.0 Code
# Initially created by Michael Vause, 12/06/2020

# Import all required modules
try:
    import sys
    from sys import platform # Used to detect the operating system used by the user to change the dimensions of the GUI
    import tkinter as tk # tkinter is the GUI module used for this project
    from tkinter import ttk
    from tkinter import messagebox
    from tkinter import filedialog as fd
    import numpy as np
    import os
    import io
    from PIL import Image, ImageTk # Used for the addition of the Durham University logo to the GUI
    from urllib.request import urlopen # Used for the addition of the Durham University logo to the GUI
    import ssl # Needed for the Durham University logo to open properly
    import pysindy as ps
    import ast # ast is used to find the class name to use when instantiating the optimization and differentiation variable
    from scipy.signal import savgol_filter # Although unused in the code, this is needed for the smoothed finite difference differentiation option to work
    from scipy.integrate import odeint # used when generating the lorenz data for the "Generate Lorenz System" option
    import csv
    import webbrowser # Used for opening the GitHub page when the "Tutorial" button is pressed so the user can read the readme file
    from math import ceil
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import pandas as pd # Used when saving the output coefficient matrix to a .csv file
except ImportError as mod: # If the user didn't install the required modules beore trying to run SEED 2.0
    print("Install the required modules before starting:\n" + str(mod))
    messagebox.showerror(title="Module Import Error", message="Install the required modules before starting:\n" + str(mod))
    sys.exit()
except Exception as err: # Any other exception that should occur (nothing else should happen, hence generalising all other exceptions)
    print("Error while importing:\n" + str(err))
    sys.exit()

# Any global variables used throughout Seed 2.0

pysindypath = os.path.dirname(ps.__file__) # Find file path for pysindy module within the python files
hidden = False # Is the own data file browser button shown
to_open = " " # Variable storing the filepath for the own data file
adv = False # Is the advanced options panel shown
opt_widgets = [] # Storing information for the advanced optimization option widgets, structure of each item in list (the difference in structure for different types is important!): 
                        #if the variable is a boolean : [label widget with name of variable,option menu with True/False,type of variable (bool in this case),the input value of the widget on the GUI]
                        #for other variables : [label widget with name of variable,type of variable (e.g int or string),entry box widget with input value from GUI]
diff_widgets = [] # Storing information for the advanced differentiation option widgets, structure of each item in list (the difference in structure for different types is important!):
                        #for empty variables: [label widget with name of variable,string type,entry widget (empty by default)]
                        #if the variable is a boolean: [label widget with name of variable,option menu with True/False,type of variable (bool in this case),the input value of the widget on the GUI]
                        #for other variables: [label widget with name of variable,type of variable,entry box widget with input value from GUI]

                        #When the item is "type of variable", that means the type of the inbuilt variable in the actual optimization/differentiation class

# Any functions used throughout SEED 2.0

# Function to run on pressing the exit button when closing SEED 2.0
def on_closing():    
    if messagebox.askokcancel("Quit", "Are you sure you want to quit?"): # tkinter message box, returning True when "ok" is pressed
        window.destroy() # Destroy the window mainloop

# Take a file path and return all of the non hidden files in that path
def non_hidden(path):
    files = [file for file in os.listdir(path) if not file.startswith(".")]
    return files

# Show/hide the file browser button depending on whether or not own data is selected
def toggle_browser(command):
    global hidden
    global to_open
    filename = to_open.split('/')[-1] # Show filename portion of filepath
    sel_op = sel_var.get() # The option selected in the Example/Own Data dropdown

    if sel_op == "Own Data":
        if hidden: # Show browser widgets
            file_button.grid()
            file_label.configure(text="File Selected: " + filename)
            hidden = False
        else: # Keep the widgets shown
            pass
    else:# If own data not selected, hide everything
        if not hidden: # Hide browser widgets
            file_button.grid_remove()
            file_label.configure(text=" ")
            hidden = True
        else: # Keep the widgets hidden
            pass

# Show file browser - called when "Select File" button pressed
def browse():
    global to_open
    to_open = fd.askopenfilename(initialdir = "/", filetypes = (("CSV files", "*.csv"), ("all files", "*.*"))) # tkinter file browser window, returning filepath of selected file
    filename = to_open.split('/')[-1] # Name of selected file
    file_label.configure(text="File Selected: " + filename) # Update label to show selected file, saved globally so that the programme remembers the selected file

# Hide and show optimization/differentiation option variable selection
def advanced():
    global adv

    if(adv): # Hide advanced options
        size = str(min_w)+"x"+str(min_h)
        adv_button["text"] = "Show Advanced" # Set the button text
        adv = False
    elif(not adv): # Show advanced options
        size = adv_size
        adv_button["text"] = "Hide Advanced" # Set the button text
        adv = True
    
    window.geometry(size) # Set GUI window's size

# Get optimizer or differentiator selection class name
def get_od_class(selection):
    if(selection == "opt"):
        opt = str(opt_var.get()) # Get the optimization option selected
        fil = open(pysindypath+"/optimizers/"+opt+".py") # Open the optimization option file
    elif(selection == "diff"):
        diff = str(diff_var.get()) # Get the differentiation option selected
        fil = open(pysindypath+"/differentiation/"+diff+".py") # Open the differentiation option file selected

    # Read the file, return all of the names of the lasses in the file and return the class name for the option
    contents = fil.read()
    par = ast.parse(contents)
    classes = [node.name for node in ast.walk(par) if isinstance(node, ast.ClassDef)]
    return classes[0]

# Get optimization option variables and update on advanced option panel
def get_opt(command):
    class_name = get_od_class("opt")
    opt_inst = eval("ps."+class_name+"()") # Instantiate the optimization option
    opt_params = opt_inst.get_params() # Get the inbuilt parameters and values from the instance (inbuilt function to the optimizer class - *Not the same for the differentiation options*)

    disp_opt_select(opt_params)

# Display the optimization option variables on advanced option panel
def disp_opt_select(opt_params):
    global opt_fram
    global opt_widgets
    opt_widgets = []
    opt_fram.destroy() # Remove all current widgets in advanced option panel to repopulate with new selection variables

    opt_fram = tk.Frame(window,bd=2,bg=bgc,width=5) # Rebuild the optimization option frame

    ofram_label = tk.Label(opt_fram,text="Optimization Option Variables",font=("Times",18,"bold"),pady=10,bg=bgc)
    ofram_label.grid(row=0,column=0,sticky="W")

    var_list = list(opt_params)
    for x in range(len(var_list)): # Create a widget for all inbuilt parameters 
        var_label = tk.Label(opt_fram,text=var_list[x],font=("Times",15,"bold"),pady=10,bg=bgc) # Label widget for all inbuilt parameters containing the parameter name
        var_label.grid(row=x+1,column=0,sticky="E")

        if str(opt_params[var_list[x]]) == "True" or str(opt_params[var_list[x]]) == "False": # Create dropdown with True/False option for boolean variables
            ovar_x = tk.StringVar(opt_fram) # The value of the inbuilt parameter
            ovar_options = ["True", "False"] # The dropdown has the options True or False
            ovar_x.set(str(opt_params[var_list[x]])) # Set the dropdown selection to the default value of the parameter

            opt_widgets.append([var_label,tk.OptionMenu(opt_fram,ovar_x,*ovar_options),type(opt_params[var_list[x]]),ovar_x])
            opt_widgets[x][1].config(width=drop_w,font=("Times",15),bg=bgc) # Format the dropdown widget
        else: # For any other variable input type, create an entry box and enter default value
            opt_widgets.append([var_label,type(opt_params[var_list[x]]),tk.Entry(opt_fram,font=("Times",15),highlightbackground=bgc,width=drop_w)])
            opt_widgets[x][2].insert(0, str(opt_params[var_list[x]])) # Instert the default parameter value to the entry widget

        opt_widgets[x][5-len(opt_widgets[x])].grid(row=x+1,column=1) # Put the newly created widget on the frame

    opt_fram.grid(row=4,column=4,rowspan=len(var_list),padx=5,sticky="W") # Display the optimization option frame on the GUI

# Get differentiation option variables and update on advanced option panel
def get_diff(command):
    diff_param_def = []
    class_name = get_od_class("diff")

    diff_params = list(eval("ps."+class_name+".__init__.__code__.co_varnames")) # Instantiate the differentiation option class and get inbuilt parameter names
    if "self" in diff_params:
        diff_params.remove("self") # Remove self from the list of parameters

    temp_params = eval("ps."+class_name+".__init__.__defaults__") # Get differentiation option inbuilt parameter default values
    diff_param_def[:] = [(("func "+thing.__name__) if(callable(thing)) else thing) for thing in temp_params] # If the input type for a deafult value is a function, enter func at the start

    disp_diff_select(diff_params, diff_param_def)

# Display the differentiation option variables on GUI
def disp_diff_select(diff_params, diff_param_def):
    global diff_fram
    global diff_widgets
    diff_widgets = []
    diff_fram.destroy() # Remove all current widgets in advanced option panel to repopulate with new selection variables

    diff_fram = tk.Frame(window,bd=2,bg=bgc,width=5) # Rebuild the differentiation option frame

    dfram_label = tk.Label(diff_fram,text="Differentiation Option Variables",font=("Times",18,"bold"),pady=10,bg=bgc)
    dfram_label.grid(row=0,column=0,sticky="W")

    for x in range(len(diff_params)): # Create a widget for all inbuilt parameters
        var_label = tk.Label(diff_fram,text=diff_params[x],font=("Times",15,"bold"),pady=10,bg=bgc) # Label widget for all inbuilt parameters containing the parameter name
        var_label.grid(row=x+1,column=0,sticky="E")

        if(x+1>len(diff_param_def)): # If there's an empty variable, create an empty entry box
            diff_widgets.append([var_label,type(""),tk.Entry(diff_fram,font=("Times",15),highlightbackground=bgc,width=drop_w)])
        elif str(diff_param_def[x]) == "True" or str(diff_param_def[x]) == "False": # Create dropdown for boolean variables
            dvar_x = tk.StringVar(diff_fram) # The value of the inbuilt parameter
            dvar_options = ["True", "False"] # The dropdown has the options True or False
            dvar_x.set(str(diff_param_def[x])) # Set the dropdown selection to the default value of the parameter

            diff_widgets.append([var_label,tk.OptionMenu(diff_fram,dvar_x,*dvar_options),type(diff_param_def[x]),dvar_x])
            diff_widgets[x][1].config(width=drop_w,font=("Times",15),bg=bgc) # Format the dropdown widget
        else: # Create an entry box for any other variables and enter deafualt value
            diff_widgets.append([var_label,type(diff_param_def[x]),tk.Entry(diff_fram,font=("Times",15),highlightbackground=bgc,width=drop_w)])
            diff_widgets[x][2].insert(0, diff_param_def[x]) # Instert the default parameter value to the entry widget

        diff_widgets[x][5-len(diff_widgets[x])].grid(row=x+1,column=1) # Put the newly created widget on the frame

    for y in range(len(diff_params)+1,4): # Fill in the rest of the frame with blank lines, the frame is 5 lines long (including the title)
        blank = tk.Label(diff_fram,text=" ",font=("Times",15,"bold"),pady=10,bg=bgc)
        blank.grid(row=y,column=0)
    
    diff_fram.grid(row=0,column=4,rowspan=4,padx=5,sticky="W") # Display the differentiation option frame on the GUI

# Instantiate the differentiator or optimizer
def od_inst(widget_list, selection):
    class_name = get_od_class(selection)

    instance = "ps."+class_name+"(" # Text string to instantiate after looping through populating with parameter values
    count = 0

    for widget in widget_list: # Form executable line in a string
        value = None # Input value from GUI
        try: # For option menu widgets
            value = widget[3].get()
        except Exception: # For entry widgets
            value = widget[2].get()

        if(str(widget[-2]) == "<class 'str'>" and not value.startswith("func")): # For inbuilt parameters that are functions, func must be added before the name (savgol_filter)
            value = "\"" + value + "\""
        elif(str(widget[-2]) == "<class 'str'>" and value.startswith("func")):
            value = value.split(' ', 1)[1]

        var_name = widget[0].cget("text") # Name of the inbuilt parameter, stored in the label widgets on the GUI

        if(not value == "\"\""): # Entry widgets for parameters with no inbuilt value store the value as ""
            instance = instance + var_name + "=" + value
            if(count+1<len(widget_list)):
                instance = instance + ","
        
        count += 1

    instance = instance + ")"

    inst = eval(instance) # Instantiate the line
    return inst

# Get feature library selection class name
def get_feat_class():
    feat = str(feat_var.get()) # Get the selected feature library option
    fil = open(pysindypath+"/feature_library/"+feat+".py") # Open the selected option's code file

    # Read the code file and return the name of the feature library class (Not the same as the name of the file)
    contents = fil.read()
    par = ast.parse(contents)
    classes = [node.name for node in ast.walk(par) if isinstance(node, ast.ClassDef)]
    return classes[0]

# Instantiate the feature library
def feat_inst():
    class_name = get_feat_class() # Get the class name of the selected feature library
    instance = "ps."+class_name+"()" # Instantiate the selected feature library
    inst = eval(instance)
    return inst # Return the instance

# Reset opt and diff advanced options to default values
def reset():
    get_opt("<command>")
    get_diff("<command>")

# Read selected file (from "Example/Own Data" dropdown) and return an array containing its data
def read_file():
    if(sel_var.get() == "Own Data"):
        to_read = to_open      
    else:
        to_read = "./data/" + sel_var.get()

    with open(to_read, newline='') as csvfile:
        data = list(csv.reader(csvfile))  

    return(data)

# Create output window - containing coefficient value table, ouput equations and model score
def show_output(table_size, coefs, feats, variable_names, window_name, score):
    out_window = tk.Tk() # The new window
    out_window.title("Model Output: " + str(window_name))
    out_window.config(bg=bgc)

    # Create all output widgets
    tv = create_table(out_window, table_size, variable_names) # Create the empty coefficient table
    create_eq_box(out_window, coefs, feats, variable_names) # Create and populate the equation box
    pop_table(tv, coefs, feats)    # Populate the coefficient table

    score_label = tk.Label(out_window,text="Model Score: "+str(score),font=("Times",15),bg=bgc) # Create and display the ouput model score
    score_label.grid(row=7,column=0,sticky="W")

    return out_window

# Create output table
def create_table(out_window, table_size, variable_names):
    # Create frame for output values title & treeview table
    fig1_fram = tk.Frame(out_window,bd=2,bg=bgc,width=5)

    fig1_label = tk.Label(fig1_fram,text="Coefficient Values",font=("Times",18,"bold"),pady=10,bg=bgc)
    fig1_label.grid(row=0,column=0,sticky="W")

    # Scrollbars to activate when the table is too large for the frame
    y_scroll = tk.Scrollbar(fig1_fram)
    y_scroll.grid(row=1,column=1,rowspan=4,sticky="nsew")
    x_scroll = tk.Scrollbar(fig1_fram,orient=tk.HORIZONTAL)
    x_scroll.grid(row=2,column=0,columnspan=1,sticky="nsew")

    tv = ttk.Treeview(fig1_fram, xscrollcommand = x_scroll.set, yscrollcommand = y_scroll.set) # The table to contain the output coefficients
    tv = resize_table(table_size, tv, fig1_fram, x_scroll, y_scroll, variable_names) # Make table the correct size (in terms of number of columns) for the output model

    fig1_fram.grid(row=0,column=0,rowspan=3,columnspan=3,padx=5,sticky="NW") # Add the empty table to the output window

    return tv # Return the table object so that it can be populated with the output coefficients

# Create scrollable box for output equations
def create_eq_box(out_window, coefs, feats, variable_names):
    # Create frame for a scrollable box for the output equations
    fig3_fram = tk.Frame(out_window,bd=2,bg=bgc)

    fig3_label = tk.Label(fig3_fram,text="Output Equations",font=("Times",18,"bold"),pady=10,bg=bgc)  
    fig3_label.grid(row=0,column=0,sticky="NW")

    # Scrollbars to activate when the equations are too large for the text box 
    x_scroll = tk.Scrollbar(fig3_fram,orient="horizontal")
    x_scroll.grid(row=2,column=0,sticky="nsew")
    y_scroll = tk.Scrollbar(fig3_fram)
    y_scroll.grid(row=1,column=3,rowspan=3,sticky="nsew")

    eq_text = tk.Text(fig3_fram,wrap="none",xscrollcommand=x_scroll.set,yscrollcommand=y_scroll.set,font=("Times",15),height=10,pady=10,bg=bgc)
    eq_text.grid(row=1,column=0)

    eqn_num = len(coefs) # Number of equations to display in the text box

    for num in range(eqn_num): # Form each of the equations to print to the text box
        eqn = coefs[num] # Coefficient values for the output equation
        eqn = [round(float(item),3) for item in eqn] # Round each coefficient value to 3.d.p.
        out = "d" + str(variable_names[num]) + "/dt = " # String used to built the output equation
        for val in range(len(feats)):
            coef = eqn[val]
            desc = feats[val]
            if(coef != 0):
                if(float(coef) < 0): # If the next coefficient value is negative, don't add a "+" before it (e.g. x + -5y -> x -5y )
                    out = out.rstrip("+ ") # Remove the previous "+" sign
                    out = out + " "

                out = out + str(coef) + " " # Add the next coefficient and descriptor to equation
                if(desc == "1"): # Don't add the descriptor if it is equal to 1 (e.g. 0.364 1 + 7x -> 0.364 + 7x )
                    out = out + "+ "
                else: # Add the descriptor if it is not equal to 1
                    out = out + str(desc) + " + "

        out = out.rstrip("+ ") # Remove the trailing "+" sign after generating the equation
        out = out + "    \n \n" # Add a blank line after each equaiton for readability
        eq_text.insert("end", out) # Insert the newly generated equation to the end of the output equation text box

    eq_text.config(state="disabled") # Disable the ability for the user to edit the output equations
    x_scroll.config(command=eq_text.xview) # Add scrolling functionality to the scrollbars (link the x&y scrolling functions to each scrollbar respectively)
    y_scroll.config(command=eq_text.yview)

    fig3_fram.grid(row=3,column=0,rowspan=4,columnspan=3,padx=5,sticky="NW") # Display the output equation text box

# Resize the output table
def resize_table(cols, tv, fig1_fram, x_scroll, y_scroll, variable_names):
    tv = ttk.Treeview(fig1_fram, xscrollcommand = x_scroll.set, yscrollcommand = y_scroll.set) # Create the treeview table

    # Create the correct number of columns (not including the descrptor column) to populate in the table depending on the number of variables in the system (cols contains this number)
    tv['columns'] = ('col1',) # The first system variable
    if(cols > 1): # More system variables if the number is greater than 1
        for x in range(2, cols+1):
            name = 'col' + str(x)
            tv['columns'] = tv['columns']+(name,)

    tv.heading("#0", text='Descriptor', anchor='w') # This is the heading for the descriptor column

    # The descriptor column in the table is set to the width of the table so that the scrolling functionality can work. It's a bit strange, but it's the only way I could get it to work.
    if(cols<3): # If there are fewer than 3 system variables, the width is set so that the table is smaller than 4 columns
        tv.column("#0", anchor="w", width=(cols+1)*col_width, minwidth=col_width, stretch=True) 
    else: # If there are more system variables, the width is only set to (4* the width of one column) so that more columns pushes the overall size outside of the viewable area
        tv.column("#0", anchor="w", width=4*col_width, minwidth=col_width, stretch=True)

    for x in range(cols): # Set the heading of each column
        head = 'd' + str(variable_names[x]) + "/dt"
        column = 'col' + str(x+1)
        tv.heading(column,text=head)
        tv.column(column, anchor='center', width=0, minwidth=col_width, stretch=True) # Format each column

    tv.grid(row=1,column=0,columnspan=1) # Add the table to the frame

    # Add scrolling functionality to the scrollbars (link the x&y scrolling functions to each scrollbar respectively)
    y_scroll.config(command = tv.yview)
    x_scroll.config(command = tv.xview)

    fig1_fram.grid() # Display the frame on the GUI
    return tv # Return the new table to pass to further functions

# Populate the output table with coefficients
def pop_table(tv, coefs, feats):
    for item in range(len(coefs[0])): # "coefs" is a list of lists, each list containing the coefficient values for each output equation
        new_val = [] # The values for each ROW of the output table
        for col in range(len(coefs)):
            new_val.append(str(coefs[col,item])) # Adding values to the ROW, one at a time
        tv.insert('', 'end', text=str(feats[item]), values=new_val) # Add the row of values to the output table

# Lorenz system for generation - This is taken from the PySINDy feature overview file
def lorenz(z, t):
    return [
        10 * (z[1] - z[0]),
        z[0] * (28 - z[2]) - z[1],
        z[0] * z[1] - (8 / 3) * z[2]
    ]

# Pop up window for Lorenz generation
def lorenz_gen():
    dt,t_min,t_max,conds = show_lorenz() # Shows the Lorenz system generation popup window, returning the input values. By default the values are the same as the data generated in the PySINDy feature overview file
    
    # Convert the returned system values to the correct types
    dt = float(dt) # The time step of the data readings
    t_min = float(t_min) # The start time of the data readings
    t_max = float(t_max) # The end time of the data readings
    conds = list(conds.split(",")) # The initial conditions of the data - a.k.a the first data point

    time_series = np.arange(t_min, t_max, dt) # Using the start and end times, and the time step, the time series can be created
    contents = odeint(lorenz, conds, time_series) # Generate the data for the user defined Lorenz system
    points_no = ceil((t_max-t_min)/dt) # Find the number of generated data points
    return contents, dt, points_no, time_series

# Create Lorenz generation window
def show_lorenz():
    lorenz_window = tk.Tk() # Create the Lorenz generation popup window
    lorenz_window.title("Lorenz Data Generation")
    lorenz_window.config(bg=bgc)

    # Create widgets for dt input
    dt_label = tk.Label(lorenz_window,text="dt",font=("Times",15,"bold"),bg=bgc)
    dt_label.grid(row=0,column=0,sticky="E")
    dt_entry = tk.Entry(lorenz_window,font=("Times",15),highlightbackground=bgc,width=10)
    dt_entry.grid(row=0,column=1,columnspan=2,sticky="EW")
    dt_entry.insert(0,"0.002")
    
    # Create widgets for start and end times
    time_label = tk.Label(lorenz_window,text="Times",font=("Times",15,"bold"),bg=bgc)
    time_label.grid(row=1,column=0,sticky="E")
    time_entry1 = tk.Entry(lorenz_window,font=("Times",15),highlightbackground=bgc,width=5)
    time_entry1.grid(row=1,column=1)
    time_entry1.insert(0,"0")
    time_entry2 = tk.Entry(lorenz_window,font=("Times",15),highlightbackground=bgc,width=5)
    time_entry2.grid(row=1,column=2)
    time_entry2.insert(0,"10")

    # Create widgets for the initial conditions
    conds_label = tk.Label(lorenz_window,text="Initial Conditions x,y,z",font=("Times",15,"bold"),bg=bgc)
    conds_label.grid(row=2,column=0,sticky="E")
    conds_entry = tk.Entry(lorenz_window,font=("Times",15),highlightbackground=bgc,width=10)
    conds_entry.grid(row=2,column=1,columnspan=2,sticky="EW")
    conds_entry.insert(0,"-8,8,27")

    # Create widgets to display the number of generated points
    number = ceil((float(time_entry2.get())-float(time_entry1.get()))/float(dt_entry.get()))
    points_label = tk.Label(lorenz_window,text="Number of Points: " + str(number),font=("Times",15,"bold"),bg=bgc)
    points_label.grid(row=3,column=0,columnspan=2,sticky="W")

    # Create the button that continues onto generating the system from the input conditions
    cont_button = tk.Button(lorenz_window,text="Continue",font=("Times",15),width=10,highlightbackground=bgc,command=lambda: lorenz_window.quit())
    cont_button.grid(row=3,column=2,sticky="EW")

    # Bind any key press (within the popup window) with updating the number of generated points
    lorenz_window.bind('<Key>', lambda event: update_number(event, dt_entry, time_entry1, time_entry2, points_label))
    lorenz_window.mainloop()

    # Before destroying the popup window, grab the input conditions
    dt = dt_entry.get()
    t_min = time_entry1.get()
    t_max = time_entry2.get()
    conds = conds_entry.get()

    lorenz_window.destroy() # Destroy the window

    return dt, t_min, t_max, conds

# Update number of points display on generate Lorenz window
def update_number(event, dt_entry, time_entry1, time_entry2, points_label):
    try: 
        number = (float(time_entry2.get())-float(time_entry1.get()))/float(dt_entry.get()) # Calculate the number of points based on the input values
        points_label.configure(text = "Number of Points: " + str(ceil(number)))
    except ZeroDivisionError: # If one of the numbers is equal to 0
        points_label.configure(text = "Number of Points: ")
    except ValueError: # If one of the input values are non numeric
        points_label.configure(text = "Number of Points: ")
    except Exception as e: # Any other exception. This shouldn't happen
        print("Error!\n" + str(e))

# Display the figure with the original data vs obtained model
def show_plots(contents, sim_data, coefs, feats, time_series, variable_names, window_name):
    # Create plot window
    plot_window = tk.Tk()
    plot_window.title("Model Plots: " + str(window_name))
    plot_window.maxsize(fig_w, fig_h)

    # This is here so that resizing the window doesn't resize the plot
    plot_window.rowconfigure(1, weight=1)
    plot_window.columnconfigure(1, weight=1)

    # Create the frame for the plot and scrollbars
    canvas_frame = tk.Frame(plot_window)
    canvas_frame.grid(column=1, row=1, sticky=tk.constants.NSEW)
    canvas_frame.rowconfigure(1, weight=1)
    canvas_frame.columnconfigure(1, weight=1)

    # Create a figure with the correct number of subplots
    fig, axs = plt.subplots(contents.shape[1], 2, sharex=False, sharey=False, figsize=(11, 2*len(variable_names)))

    # Plot the data on the subplots
    for i in range(contents.shape[1]): # For every row of subplots
        if(len(variable_names) == 1): # This is needed to enable the plotting of one dimensional systems
            dim = (1)
        else:
            dim = (i, 1)

        # Plot the input data and the forward simulated data obtained after creating the model
        axs[dim].plot(time_series, contents[:, i], 'k', label='input data')
        axs[dim].plot(time_series, sim_data[:, i], 'r--', label='model simulation')
        if(i == 0):
            axs[dim].legend()
        axs[dim].set(xlabel='t', ylabel=variable_names[i].format(i))

        # Loop through the coefficient matrix to extract the non zero values
        coef_plt = [] # List of non zero coefficients (coefficient values)
        desc_plt = [] # List of descriptors for the non zero variables
        row = coefs[i]
        for item in range(len(coefs[0])):
            val = row[item]
            des = feats[item]
            if val != 0:
                coef_plt.append(val)
                desc_plt.append(des)

        if(len(variable_names) == 1): # This is needed to enable the plotting of one dimensional systems
            dim = (0)
        else:
            dim = (i, 0)

        # Plot the non zero coefficient values as a bar plot
        axs[dim].bar(desc_plt,coef_plt)
        axs[dim].axhline(y=0, color='k')
        axs[dim].set_title("d" + str(variable_names[i]) + "/dt",size=10)

        # If the number of output coefficients is greater than 6, change the font size to 8
        if len(coef_plt) > 6:
            size = 8
        else:
            size = 10
        plot_label = axs[dim].get_xticklabels() # Get all of the font label objects for the subplot
        [each_label.set_fontsize(size) for each_label in plot_label] # Set the font size of the specific subplot

    fig.subplots_adjust(hspace=0.3) # Add vertical space in between each row of subplots so they don't overlap
    fig.tight_layout() # Remove excess whitespace from the top and bottom of the figure

    # set up a canvas with scrollbars
    canvas = tk.Canvas(canvas_frame)
    canvas.grid(row=1, column=1, sticky=tk.constants.NSEW)

    xScrollbar = tk.Scrollbar(canvas_frame, orient=tk.constants.HORIZONTAL)
    yScrollbar = tk.Scrollbar(canvas_frame)

    xScrollbar.grid(row=2, column=1, sticky=tk.constants.EW)
    yScrollbar.grid(row=1, column=2, sticky=tk.constants.NS)

    # Add the commands to allow scrolling
    canvas.config(xscrollcommand=xScrollbar.set)
    xScrollbar.config(command=canvas.xview)
    canvas.config(yscrollcommand=yScrollbar.set)
    yScrollbar.config(command=canvas.yview)

    # Plug the figure into the canvas
    figAgg = FigureCanvasTkAgg(fig, canvas)
    mplCanvas = figAgg.get_tk_widget()

    # Connect figure with scrolling region
    cwid = canvas.create_window(0, 0, window=mplCanvas, anchor=tk.constants.NW)
    canvas.config(scrollregion=canvas.bbox(tk.constants.ALL),width=fig_w,height=fig_h)

    # Add in the toolbar to the output window
    toolbar_frame = tk.Frame(plot_window)
    toolbar = NavigationToolbar2Tk(figAgg, toolbar_frame)
    toolbar.children['!button5'].config(command=lambda: save_output(fig, coefs, feats, variable_names))
    toolbar_frame.grid(row=0, column=1)

    return plot_window

# Save the output figure & coefficient matrix to file
def save_output(fig, coefs, feats, variable_names):
    save_filepath = fd.asksaveasfilename() # The file browser popup that return the filepath the user would like to save to

    # Exit the saving code if the user cancels the save or doesn't give the file a name
    if(save_filepath == ""):
        return None

    fig.savefig(save_filepath) # Save the figure as a .png

    total = np.append([feats], coefs, axis=0) # Adds the descriptors to the output coefficient matrix
    total = np.transpose(total) # Obtain the transpose of the total matrix to output as expected

    head = [("d "+variable_names[i]+"/dt") for i in range(len(variable_names))] # The derivative of each system variable
    head.insert(0,'') # Add a blank value to the start so that the columns of the coefficent matrix line up with the correct derivative

    pd.DataFrame(total).to_csv(save_filepath + ".csv", header=head, index=None) # Use pandas to save the matrix to a .csv file with the same filepath as above

# Run the main computation
def comp():
    window_name = sel_var.get() # Obtain the name of the data file to use as the output window name

    # Stop the computation if "Own Data" is selected and no file has been selected
    if((to_open.split('/')[-1] == "" or to_open.split('/')[-1] == " ") and sel_var.get() == "Own Data"):
        messagebox.showerror(title="Select File", message="You need to select a file to compute!")
        return None

    # Try to instantiate the optimizer with the advanced variables. Stop the computation if an invalid variable is input (will throw an error when instantiating)
    try:
        opt = od_inst(opt_widgets,"opt")
    except Exception:
        messagebox.showerror(title="Invalid Option", message="You have input an invalid optimization variable, check the PySINDy documentation for valid options.\n\nExiting the computation.")
        return None

    # Try to instantiate the differentiator with the advanced variables. Stop the computation if an invalid variable is input (will throw an error when instantiating)
    try:
        diff = od_inst(diff_widgets,"diff")
    except Exception:
        messagebox.showerror(title="Invalid Option", message="You have input an invalid differentation variable, check the PySINDy documentation for valid options.\n\nExiting the computation.")
        return None

    # Instatiate the feature library
    feat = feat_inst()

    # If "Generate Lorenz System" is selected, show the Lorenz popup window and generate with the input conditions. Stop the computation if an invalid condition is input
    if(window_name == "Generate Lorenz System"):
        try:
            contents, dt, points_no, time_series = lorenz_gen()
            window_name = window_name + ", Number of points: " + str(points_no)
        except Exception:
            messagebox.showerror(title="Invalid Condition", message="You have input an invalid condition. \n\nExiting the data generation.")
            return None

        variable_names = ["x","y","z"] # Default system variable names if "Generate Lorenz System" is selected
    elif(window_name.endswith(".csv") or ((window_name == "Own Data") and to_open.endswith(".csv"))):
        data = read_file() # Obtain the data in the selected .csv file. This is a list of lists
        contents = data
    
        # Separate the input file into data points, time series and variable names
        variable_names = contents[0][1:] # Obtain the system variable names from the data
        del contents[0] # Remove the system variable names from the data matrix
        time_series = [val[0] for val in contents] # From the first column of the data file, obtain the time series data for the data
        dt = float(time_series[1])-float(time_series[0]) # From the time series data, obtain dt

        contents = [val[1:] for val in contents] # Remove the time series data from the data matrix
        contents = np.array([[float(val) for val in item] for item in contents]) # Turn the list of lists into a numpy array as this is what the PySINDy model expects as an input
    else: # If the selected file isn't a .csv file, stop the computation
        messagebox.showerror(title="Invalid File Type", message="The selected file needs to be a .csv file in the correct format. Read to tutorial for more information.\n\nExiting the computation.")
        return None

    model = ps.SINDy(optimizer=opt,differentiation_method=diff,feature_library=feat,feature_names=variable_names) # Instantiate the model with the previously obtained instances and variable names
    model.fit(contents, t=dt) # Fit the input data to the model
    coefs = model.coefficients() # Obtain the coefficient matrix from the obtained model
    feats = model.get_feature_names() # Get the feature names from the obtained model

    time_series = np.array([float(val) for val in time_series]) # Create a numpy array with the time series data stored as floats
    
    score = model.score(contents, t=time_series) # Obtain the model score for the system

    conds = np.array([float(val) for val in contents[0]]) # Convert the system's initial conditions into a numpy array of float values as this is what is expected by the model.simulate() function
    sim_data = model.simulate(conds,time_series) # Create the forward simulated data. This uses the original initial conditions evolved with the model output equations to obtain new data
    plot_window = show_plots(contents, sim_data, coefs, feats, time_series, variable_names, window_name) # Show the output plots

    table_size = len(contents[0]) # Obtain the number of system variables, used to define the number of columns in the output table
    out_window = show_output(table_size, coefs, feats, variable_names, window_name, score) # Show the output coefficient and equation window

    out_window.mainloop()
    plot_window.mainloop()

# GUI design

bgc = "lightgray" # GUI background colour

# Size Correction based on operating system
if platform == "darwin": # MacOS
    print("MacOS detected")
    min_w = 520 # Minimum main window width
    max_w = 1200 # Maximum main window width
    min_h = 590 # Minimum main window height
    max_h = 680 # Maximum main window height
    drop_w = 30 # Width of the dropdown widgets on the main window
    fram_w = 62 # Width of the frames on the main window (for the button frame)
    line_w = 61 # Width of the blank lines on the button frame
    col_width = 160 # Width of the columns in the output table
    fig_w = 1115 # Width of the output figure
    fig_h = 645 # height of the output figure
    adv_size = "1050x610" # Size of the window when the advanced options are shown
else:
    print(platform + " detected")
    min_w = 690
    max_w = 1500
    min_h = 650
    max_h =800
    drop_w = 30
    fram_w = 55
    line_w = 60
    col_width = 200
    fig_w = 1115
    fig_h = 645
    adv_size = "1380x700"

# Create the main GUI window
window = tk.Tk()
window.title("Extracting Equations from Data")
window.minsize(min_w,min_h)
window.maxsize(max_w,max_h)
window.config(bg=bgc)

# Add Durham University logo to GUI
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)): # This is needed to validate the server identity for the pictuer URL
    ssl._create_default_https_context = ssl._create_unverified_context

try:
    pic_url = "https://github.com/M-Vause/SEED2.0/blob/master/images/DurhamUniversityMasterLogo_RGB.png?raw=true" # URL for the Durham University logo
    my_page = urlopen(pic_url)
    my_picture = io.BytesIO(my_page.read())
    pil_img = Image.open(my_picture)
    newsize = (167, 69) # The size of the logo on the GUI
    pil_img = pil_img.resize(newsize)

    tk_img = ImageTk.PhotoImage(pil_img)
    label = tk.Label(window, image=tk_img, bg=bgc) # Add the image to a label widget to display on the GUI
    label.grid(row=0,column=0,padx=5, pady=5,rowspan=2)
except Exception: # If anything goes wrong, don't display the logo, probably internet connection error
    print("Durham University Logo Not Printing")

# Add main title to the GUI
main_label1 = tk.Label(window,text="Extracting Equations",font=("Times",30,"bold","underline"),padx=5,pady=10,bg=bgc)
main_label1.grid(row=0,column=1,columnspan=3,sticky="S")

main_label2 = tk.Label(window,text="from Data",font=("Times",30,"bold","underline"),padx=5,pady=10,bg=bgc)
main_label2.grid(row=1,column=1,columnspan=3,sticky="N")

# Creating the label and dropdown for data selection
select_label = tk.Label(window,text="Example/Own Data:",font=("Times",15,"bold"),pady=10,bg=bgc)
select_label.grid(row=2,column=0,sticky="E")

sel_var = tk.StringVar(window) # Variable storing the selected value in the dropdown
sel_options = non_hidden("./data")
if "__pycache__" in sel_options: # Remove "__pycache__" from the options to display in the dropdown
    sel_options.remove("__pycache__")
sel_options.sort()
sel_options.append("Generate Lorenz System") # Add this option to the dropdown options
sel_options.append("Own Data") # Add this option to the dropdown options
sel_var.set("data_Lorenz3d.csv") # Set the deafualt selected value for the data dropdown

    # Create, configure and display the data selection dropdown on the GUI
select_menu = tk.OptionMenu(window,sel_var,*sel_options,command=toggle_browser)
select_menu.config(width=drop_w,font=("Times",15),bg=bgc)
select_menu.grid(row=2,column=1,columnspan=3,sticky="nsew")

# All file browser widgets
file_button = tk.Button(window,text="Select File",font=("Times",15),width=15,highlightbackground=bgc,command=browse)
file_button.grid(row=3,column=0,sticky="E")

file_label = tk.Label(window,text=" ",font=("Times",15),pady=10,bg=bgc)
file_label.grid(row=3,column=1,columnspan=3,sticky="W")

toggle_browser("<command>") # Called to initially hide the browser widgets as "data_Lorenz3d.csv" is selected by default

# All optimization option widgets
opt_label = tk.Label(window,text="Optimization Option:",font=("Times",15,"bold"),pady=10,bg=bgc)
opt_label.grid(row=5,column=0,sticky="E")

opt_var = tk.StringVar(window) # Variable storing the selected value in the dropdown
temp_options = non_hidden(pysindypath+"/optimizers") # Get a list of the optimizer file names from the PySINDy source files
    # Remove the files that aren't optimizer options
if "__pycache__" in temp_options:
    temp_options.remove("__pycache__")
if "__init__.py" in temp_options:
    temp_options.remove("__init__.py")
if "base.py" in temp_options:
    temp_options.remove("base.py")
if "sindy_optimizer.py" in temp_options:
    temp_options.remove("sindy_optimizer.py")
#temp_options.append("Lasso") # This would be where more options are added if required, e.g. the Lasso method
ext = ".py"
opt_options = [eg.split(ext, 1)[0] for eg in temp_options] # Remove the extension from all of the remaining options
opt_options.sort()
opt_var.set("stlsq") # Set the default value for the optimization option
temp_options.clear()

    # Create, configure and display the optimization option dropdown on the GUI
opt_menu = tk.OptionMenu(window,opt_var,*opt_options,command=get_opt)
opt_menu.config(width=drop_w,font=("Times",15),bg=bgc)
opt_menu.grid(row=5,column=1,columnspan=3,sticky="nsew")

# All differentiation option widgets
diff_label = tk.Label(window,text="Differentiation Option:",font=("Times",15,"bold"),pady=10,bg=bgc)
diff_label.grid(row=4,column=0,sticky="E")

diff_var = tk.StringVar(window) # Variable storing the selected value in the dropdown
temp_options = non_hidden(pysindypath+"/differentiation") # Get a list of the differentiator file names from the PySINDy source files
    # Remove the files that aren't differentiator options
if "__pycache__" in temp_options:
    temp_options.remove("__pycache__")
if "__init__.py" in temp_options:
    temp_options.remove("__init__.py")
if "base.py" in temp_options:
    temp_options.remove("base.py")
if "sindy_derivative.py" in temp_options: # This came in a PySINDy update at the end of the project, support for this options needs to be added
    temp_options.remove("sindy_derivative.py")
ext = ".py"
diff_options = [eg.split(ext, 1)[0] for eg in temp_options] # Remove the extension from all of the remaining options
diff_options.sort()
#diff_options.append("pre-computed") # This would be where more options are added if required, e.g. pre-computed derivatives
diff_var.set("finite_difference") # Set the default value for the differentiation option
temp_options.clear()

    # Create, configure and display the differentiation option dropdown on the GUI
diff_menu = tk.OptionMenu(window,diff_var,*diff_options,command=get_diff)
diff_menu.config(width=drop_w,font=("Times",15),bg=bgc)
diff_menu.grid(row=4,column=1,columnspan=3,sticky="nsew")

# All feature library widgets
feat_label = tk.Label(window,text="Feature Library Option:",font=("Times",15,"bold"),pady=10,bg=bgc)
feat_label.grid(row=6,column=0,sticky="E")

feat_var = tk.StringVar(window) # Variable storing the selected value in the dropdown
temp_options = non_hidden(pysindypath+"/feature_library") # Get a list of the feature library file names from the PySINDy source files
    # Remove the files that aren't feature library options
if "__pycache__" in temp_options:
    temp_options.remove("__pycache__")
if "__init__.py" in temp_options:
    temp_options.remove("__init__.py")
if "custom_library.py" in temp_options:
    temp_options.remove("custom_library.py")
if "feature_library.py" in temp_options:
    temp_options.remove("feature_library.py")
ext = ".py"
feat_options = [eg.split(ext, 1)[0] for eg in temp_options] # Remove the extension from all of the remaining options
feat_options.sort()
feat_var.set("polynomial_library") # Set the default value for the differentiation option
temp_options.clear()

    # Create, configure and display the feature library option dropdown on the GUI
feat_menu = tk.OptionMenu(window,feat_var,*feat_options)
feat_menu.config(width=drop_w,font=("Times",15),bg=bgc)
feat_menu.grid(row=6,column=1,columnspan=3,sticky="nsew")

# Add frame for all buttons on the GUI
button_fram = tk.Frame(window,bg=bgc,bd=2,relief="sunken",pady=10,width=fram_w)

    # Tutorial button
tut_button = tk.Button(button_fram,text="Tutorial",font=("Times",15,"bold"),width=15,highlightbackground=bgc,command=lambda : webbrowser.open("https://github.com/M-Vause/SEED2.0"))
tut_button.grid(row=0,column=0,columnspan=2,sticky="EW")

    # Show advanced options button
adv_button = tk.Button(button_fram,text="Show Advanced",font=("Times",15,"bold"),width=15,highlightbackground=bgc,command=advanced)
adv_button.grid(row=0,column=2,columnspan=2,sticky="EW")

    # Blank line in the frame
blank_line1 = tk.Label(button_fram,text=" ",font=("Times",15),width=round(line_w/2),highlightbackground=bgc,bg=bgc)
blank_line1.grid(row=1,column=0,columnspan=2)

    # Reset advanced options button
reset_button = tk.Button(button_fram,text="Reset to Defaults",font=("Times",15,"bold"),width=15,highlightbackground=bgc,command=reset)
reset_button.grid(row=1,column=2,columnspan=2,sticky="EW")

    # Blank line in the frame
blank_line2 = tk.Label(button_fram,text=" ",font=("Times",15),width=line_w,highlightbackground=bgc,bg=bgc)
blank_line2.grid(row=2,column=0,columnspan=4)

    # Compute button
comp_button = tk.Button(button_fram,text="Compute",font=("Times",15,"bold"),width=10,highlightbackground=bgc,command=comp)
comp_button.grid(row=3,column=0,columnspan=4,sticky="EW")

button_fram.grid(row=7,column=0,columnspan=4,padx=5,sticky="SEW") # Display the frame on the GUI - ,rowspan=4

# Frame for optimization option variable selection (advanced options)
opt_fram = tk.Frame(window,bd=2,bg=bgc,width=5)
get_opt("<command>")

# Frame for differentitation option variable selection (advanced options)
diff_fram = tk.Frame(window,bd=2,bg=bgc,width=5)
get_diff("<command>")

# Resize the main GUI window
size = str(min_w) + "x" + str(min_h)
window.geometry(size)

# Enter mainloop
window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()