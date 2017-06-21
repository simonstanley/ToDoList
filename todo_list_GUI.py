#!/usr/local/sci/bin/python2.7

"""
To-do list GUI. Create and manage to-do lists to help organise your work. 

Author: sstanley
Date:   24/7/2014

"""
from Tkinter import *
from tkFileDialog import asksaveasfilename, askopenfilename
from collections import OrderedDict
import datetime
import pickle
import inspect
import os
import copy

priority_dict = {1:"HIGH", 2:"Medium", 3:"Low"}

def new_dict():
    """
    Start new to-do dictionary.
    
    """
    todo_dict = {"todo_items" : {},
                 "history"    : {"completed"  : {},
                                 "removed"    : {}},
                 "current_id" : 1,
                 "order"      : None}
    return todo_dict

def open_dict(filepath):
    """
    Open existing to-do dictionary.
    
    """
    return pickle.load(open(filepath, "r"))

def create_structured_dict(todo_dict):
    """
    
    """
    structured_dict = {}
    todo_dict = OrderedDict(sorted(todo_dict.items(), 
                           key=lambda item_dict: len(item_dict[1]["parents"])))
    for key, val in todo_dict.items():
        if val['parents'] == []:
            structured_dict[key] = val
        else:
            this_dict = structured_dict
            for i, ref_key in enumerate(val['parents']):
                if i == 0:
                    this_dict = this_dict[ref_key]
                else:
                    this_dict = this_dict['todo_items'][ref_key]
            if this_dict.get('todo_items'):
                this_dict['todo_items'][key] = val
            else:
                this_dict['todo_items'] = {key : val}
                print
    return structured_dict

def error_window(err_message):
    """
    Display error message in new window.
    
    """
    err_window = Tk()
    err_window.title("Error")
    frame = Frame(err_window)
    frame.pack(padx=10, pady=10)   
    Label(frame, text='Error: '+str(err_message)).pack(pady=10)
        
    button_frame = Frame(frame)
    button_frame.pack()
    Button(button_frame, 
           text='Ok', 
           command=err_window.destroy).pack()
    err_window.mainloop()

class Todo_list(Frame):
    """
    Class for to-do list GUI.
    
    """
    def __init__(self, window):
        self.window = window
        # Set width and height of window. 
        width  = 730
        height = 700
        self.window.geometry("%sx%s" % (width, height))
        self.window.title("To-do list")
        # Get filepath of this script, this is where the to-do list data will 
        # be saved.
        self.filepath  = os.path.dirname(
                         os.path.abspath(
                         inspect.getfile(inspect.currentframe()))) + \
                         "/main_list.todo"
        self.todo_dict = self.get_todo_dict()
        # Set the specified order of list if given.
        self.order = self.todo_dict["order"]
        now        = datetime.datetime.now()
        self.today = datetime.datetime(now.year, now.month, now.day)
        
        # Menu bar
        menubar  = Menu(self.window)
        
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.new_file)
        filemenu.add_command(label="Open", command=self.open_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.window.destroy)
        menubar.add_cascade(label="File", menu=filemenu)
        
        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label="Clear All", command=self.check_clear_all)
        menubar.add_cascade(label="Edit", menu=editmenu)
        
        ordermenu = Menu(menubar, tearoff=0)
        ordermenu.add_command(label="By priority", 
                              command=lambda: self.re_order_list('priority'))
        ordermenu.add_command(label="By due date", 
                              command=lambda: self.re_order_list('due_date'))
        ordermenu.add_command(label="By start date", 
                              command=lambda: self.re_order_list('start_date'))
        ordermenu.add_command(label="By name", 
                              command=lambda: self.re_order_list('header'))
        menubar.add_cascade(label="Order", menu=ordermenu)
        
        histmenu = Menu(menubar, tearoff=0)
        histmenu.add_command(label="Completed tasks", 
                             command=self.show_completed)
        histmenu.add_command(label="Removed tasks", 
                             command=self.show_removed)
        menubar.add_cascade(label="History", menu=histmenu)
        self.window.config(menu=menubar)
        
        # Left side of window, the to-do list.        
        self.todo_frame = Frame(self.window)
        self.todo_frame.pack(side=LEFT, padx=20, pady=10, anchor=N)                
        Label(self.todo_frame, 
              text='To-Do List', 
              font=("",20)).grid(row=0, column=0, padx=40)
        Button(self.todo_frame, 
               text='Add', 
               command=lambda: 
                       self.manage_todo(self.item_id)).grid(row=0, column=2)
        self.todo_list_frame = Frame(self.todo_frame)
        self.todo_list_frame.grid(row=1, column=0, pady=10, sticky=W)
                
        # Right side of window, details of selected to-do task.
        self.info_header = Frame(self.window)
        self.info_header.pack(padx=10, pady=10, anchor=NW)
        Label(self.info_header, text='Details', 
              font=("",18)).grid(row=0, column=0, padx=40)
        Button(self.info_header, 
               text='Edit', 
               command=self.edit_todo).grid(row=0, column=1, padx=3)
        Button(self.info_header, 
               text='Remove',
               command=self.remove_todo).grid(row=0, column=2, padx=3)
        Button(self.info_header, 
               text='Done',
               command=self.done_todo).grid(row=0, column=3, padx=3)
        
        # Header.
        self.header_frame = Frame(self.window)
        self.header_frame.pack(padx=10, pady=10, anchor=NW)
        # Priority and dates.
        self.dates_frame = Frame(self.window)
        self.dates_frame.pack(padx=10, anchor=NW)
        # Description.
        self.description_frame = Frame(self.window)
        self.description_frame.pack(padx=10, pady=10, anchor=NW)

        # Value to group radio buttons together.
        self.var = IntVar()
        # Get current to-do task ID.
        self.item_id = self.todo_dict["current_id"]
        self.add_saved_todo_items()

    def get_todo_dict(self):
        """
        Load saved to-do if available, otherwise start new list.
        
        """
        try:
            todo_dict = open_dict(self.filepath)
        except IOError:
            todo_dict = new_dict()
        return todo_dict

    def sort_by_dates(self, item_dict):
        """
        Function to sort dictionary by dates, returns year 5000 if date is 
        'None' making it bottom of list (unless a task is set beyond this 
        year!).
        
        """
        if item_dict[self.order] == 'None':
            return datetime.datetime(5000, 1, 1)
        else:
            return datetime.datetime.strptime(item_dict[self.order], 
                                              '%d-%m-%Y')

    def order_dictionary(self, this_dict):
        """
        Re-order the dictionary if order specified.
        
        
        """
        if self.order:
            if self.order in ["header", "priority"]:
                this_dict = OrderedDict(sorted(this_dict.items(), 
                            key=lambda item_dict: item_dict[1][self.order]))
            elif self.order in ["due_date", "start_date"]:
                this_dict = OrderedDict(sorted(this_dict.items(), 
                            key=lambda item_dict: 
                                self.sort_by_dates(item_dict[1])))
        return this_dict
        

    def add_saved_todo_items(self):
        """
        Add all saved to-do items to the to-do list.
        
        """        
        # Remove current list.
        for todo_item in self.todo_list_frame.winfo_children():
            todo_item.destroy()
        
        # Only re structure dictionary for display purposes. self.todo_dict 
        # must remain unchanged.
        todo_dict = copy.deepcopy(self.todo_dict["todo_items"])
        try:
            todo_dict = create_structured_dict(todo_dict)
        except KeyError:
            return
        
        todo_dict = self.order_dictionary(todo_dict)
            
        def add_all_tasks(this_id, this_dict, spacing):
            self.add_item_to_list(this_dict["header"], this_id, spacing)
            if this_dict.get('todo_items'):
                sub_dict = self.order_dictionary(this_dict.get('todo_items'))
                for item_id, item_dict in sub_dict.items():
                    add_all_tasks(item_id, item_dict, spacing=spacing+15)
        
        for item_id, item_dict in todo_dict.items():
            add_all_tasks(item_id, item_dict, spacing=0)
            
    
    def add_item_to_list(self, head, item_id, spacing):
        """
        Append to-do task to to-do list in window.
        
        """
        if spacing != 0:
            font = ("",10)
        else:
            font = ("",12)
        Radiobutton(self.todo_list_frame, 
                    text=head,
                    font=font,
                    variable=self.var, 
                    value=item_id,
                    command=self.show_info).grid(sticky=W, padx=spacing)

    def edit_todo(self):
        """
        Retrieve information of current to-do and run manage_todo.
        
        """
        item_id = self.var.get()
        head = self.todo_dict["todo_items"][item_id]["header"]
        date = self.todo_dict["todo_items"][item_id]["due_date"]
        priority = self.todo_dict["todo_items"][item_id]["priority"]
        description = self.todo_dict["todo_items"][item_id]["info"]
        parents = self.todo_dict["todo_items"][item_id]["parents"]
        self.manage_todo(item_id, set_head=head, set_date=date, 
                         set_priority=priority, set_description=description,
                         parent_item_ids=parents, new_item=False)

    def manage_todo(self, item_id, set_head=None, set_date=None, 
                     set_priority=None, set_description=None, 
                     parent_item_ids=[], title="To-Do Task", new_item=True):
        """
        Open a window to enter information on a new to do item.
        
        """
        width = 30
        todo_window = Tk()
        todo_window.title(title)
        item_frame = Frame(todo_window)
        item_frame.pack(padx=10, pady=10)
        
        Label(item_frame,
              text="To-Do").grid(row=0, 
                                 column=0, 
                                 pady=5, 
                                 sticky=W)
        head = Entry(item_frame, width=width)
        head.grid(row=0, column=1)
        if set_head:
            head.insert(0, set_head)
        
        # Due Date
        if set_date:
            if set_date == 'None':
                set_date = None
            else:
                set_date = datetime.datetime.strptime(set_date, '%d-%m-%Y')
        
        Label(item_frame, 
              text="Due Date").grid(row=1, 
                                    column=0, 
                                    pady=5, 
                                    sticky=W)
        
        date = Frame(item_frame)
        date.grid(row=1, column=1, sticky=W)
        
        day = Entry(date, width=2)
        day.grid(row=0, column=0)
        Label(date, text='Day').grid(row=0, column=1, sticky=W)
        if set_date:
            day.insert(0, set_date.day)
        
        month = Entry(date, width=2)
        month.grid(row=0, column=2)
        Label(date, text='Month').grid(row=0, column=3, sticky=W)
        if set_date:
            month.insert(0, set_date.month)
            
        year = Entry(date, width=4)
        year.grid(row=0, column=4)
        Label(date, text='Year').grid(row=0, column=5, sticky=W)
        if set_date:
            year.insert(0, set_date.year)
        
        # Priority
        priority_var = IntVar()
        Label(item_frame,
              text="Priority").grid(row=2, column=0, pady=5, sticky=W)
        prority_frame = Frame(item_frame)
        prority_frame.grid(row=2, column=1, sticky=W)
        
        low = Radiobutton(prority_frame, text='Low', variable=priority_var, 
                          value=3, command=lambda: priority_var.set(3))
        low.grid(row=0, column=0, sticky=W)
        med = Radiobutton(prority_frame, text='Medium', variable=priority_var, 
                          value=2, command=lambda: priority_var.set(2))
        med.grid(row=0, column=1, sticky=W)
        high = Radiobutton(prority_frame, text='High', variable=priority_var, 
                           value=1, command=lambda: priority_var.set(1))
        high.grid(row=0, column=2, sticky=W)
        if set_priority:
            priority_dict = {3:low, 2:med, 1:high}
            priority_dict[set_priority].invoke()
        else:
            med.invoke()
                
        # Description
        Label(item_frame, 
              text="Comments").grid(row=3, 
                                    column=0, 
                                    pady=5, 
                                    sticky=NW)
        description = Text(item_frame, width=width+4, height=10)
        description.grid(row=3, column=1, sticky=W)
        if set_description:
            description.insert("0.0", set_description)
        
        Button(item_frame,
               text="Sub-Task",
               command=lambda: self.add_sub_task(item_id, parent_item_ids,
                                                 head.get())).grid(row=4, 
                                                                   column=0, 
                                                                   stick=W)
               
        button_frame = Frame(item_frame)
        button_frame.grid(row=4, column=1, pady=5, stick=E)
        
        Button(button_frame, 
               text='Cancel', 
               command=lambda: self.close_window(todo_window)).pack(side=RIGHT)
        Button(button_frame, 
               text='Ok', 
               command=lambda: self.save_entry(
                       todo_window,
                       item_id,
                       head.get(), 
                       day.get(),
                       month.get(),
                       year.get(),
                       priority_var.get(),
                       description.get("0.0",END),
                       parent_item_ids=parent_item_ids,
                       new_item=new_item)).pack(side=RIGHT)
        todo_window.mainloop()

    def add_sub_task(self, parent_item_id, parents_of_parent, name):
        """
        
        """
        self.item_id += 1
        self.todo_dict["current_id"] = self.item_id
        title = name + " - Sub Task"
        all_parents = parents_of_parent + [parent_item_id]
        self.manage_todo(self.item_id, parent_item_ids=all_parents,
                         title=title)

    def remove_info(self):
        """
        Removes all information currently showing.
        
        """        
        # Remove previous information.
        for head in self.header_frame.winfo_children():
            head.destroy()
        for date in self.dates_frame.winfo_children():
            date.destroy()
        for descript in self.description_frame.winfo_children():
            descript.destroy()
        
    def show_info(self):
        """
        Show the information of the current to-do item.
        
        """
        item_id = self.var.get()
        self.remove_info()
                    
        # To-do header.
        Label(self.header_frame, 
              text=self.todo_dict["todo_items"][item_id]["header"],
              font=("",17)).pack(side=LEFT)
              
        # Priority.
        Label(self.dates_frame, 
              text=priority_dict[self.todo_dict["todo_items"]
                                 [item_id]["priority"]]+" priority",
              font=("",10)).grid(row=0, column=0, sticky=W)

        # To-do dates.
        due_date = self.todo_dict["todo_items"][item_id]["due_date"]
        if due_date == 'None':
            due_warning = ""
        else:
            date_diff = datetime.datetime.strptime(due_date, '%d-%m-%Y') - \
                        self.today
            if date_diff.days == 0:
                due_warning = "  (Due today)"
            elif date_diff.days < 0:
                if date_diff.days == -1:
                    due_warning = "  (1 day overdue)"
                else:
                    due_warning = "  (%s days overdue)" % (date_diff.days*-1)
            elif date_diff.days <= 5:
                if date_diff.days == 1:
                    due_warning = "  (1 day remaining)"
                else:
                    due_warning = "  (%s days remaining)" % date_diff.days
            else:
                due_warning = ""
        Label(self.dates_frame, 
              text="Due Date",
              font=("",12)).grid(row=1, column=0, pady=5, sticky=W)
        Label(self.dates_frame, 
              text=self.todo_dict["todo_items"][item_id]["due_date"] + due_warning,
              font=("",12)).grid(row=1, column=1, padx=10, sticky=W)
        Label(self.dates_frame, 
              text="Started",
              font=("",10)).grid(row=2, column=0, sticky=W)
        Label(self.dates_frame, 
              text=self.todo_dict["todo_items"][item_id]["start_date"],
              font=("",10)).grid(row=2, column=1, padx=10, sticky=W)

        # To-do description.
        if self.todo_dict["todo_items"][item_id]["info"].strip():
            Label(self.description_frame, 
                  text="Comments:", 
                  font=("",10)).pack(anchor=W)
        Label(self.description_frame, wraplength=350, justify=LEFT,
              text=self.todo_dict["todo_items"][item_id]["info"],
              font=("",10)).pack(anchor=W)
        
    def update_saved_dict(self):
        """
        Save the latest to-do list.
        
        """
        pickle.dump(self.todo_dict, open(self.filepath, "w"))
    
    def get_all_associated_tasks(self):
        """
        
        """
        item_id = self.var.get()
        item_ids = [item_id]
        for this_id, val in self.todo_dict['todo_items'].items():
            if item_id in val['parents']:
                item_ids.append(this_id)
        return item_ids

    def check_done_sub_tasks(self, item_ids):
        """
        Display message checking the user wants to clear all.
        
        """
        self.check_window = Tk()
        self.check_window.title("Uncompleted tasks")
        
        message_frame = Frame(self.check_window)
        message_frame.pack(padx=5, pady=10)
        button_frame = Frame(self.check_window)
        button_frame.pack(pady=5, ipadx=3)
        
        Label(message_frame, text="This task contains uncompleted sub tasks."\
              "\nPress 'Ok' to complete this task and all uncompleted sub "\
              "tasks.").pack()
        Button(button_frame, text="Ok", 
               command=lambda: 
               self.confirm_completion(item_ids)).pack(side=LEFT)
        Button(button_frame, text="Cancel", 
               command=self.check_window.destroy).pack(side=RIGHT)
    
    def confirm_completion(self, item_ids):
        """
        
        """
        self.move_to_history(item_ids, "completed")
        self.check_window.destroy()
    
    def move_to_history(self, item_ids, where):
        """
        Delete item from to-do list and place in history dictionary.
        
        """
        for item_id in item_ids:
            this_todo = self.todo_dict["todo_items"][item_id]
            this_todo["date_"+where] = self.today.strftime('%d-%m-%Y')
            self.todo_dict["history"][where][item_id] = this_todo
            del self.todo_dict["todo_items"][item_id]
        self.add_saved_todo_items()
        self.remove_info()
        self.update_saved_dict()
    
    def done_todo(self):
        """
        Put todo item in completed dictionary.
        
        """
        item_ids = self.get_all_associated_tasks()
        if len(item_ids) > 1:
            self.check_done_sub_tasks(item_ids)
        else:
            self.move_to_history(item_ids, "completed")
    
    def remove_todo(self):
        """
        Put todo item in removed dictionary.
        
        """
        item_ids = self.get_all_associated_tasks()
        self.move_to_history(item_ids, "removed")
    
    def save_entry(self, this_window, item_id, head, day, month, year, priority, 
                    description, parent_item_ids=[], new_item=True):
        """
        Gather information from form and update database.
        
        """
        if not head:
            error_window('No to-do task specified.')
            return
                    
        if day and month and year:
            due_date = datetime.datetime(int(year), int(month), int(day))
            if due_date < self.today:
                error_window('The due date comes before today.')
                return
            due_date = due_date.strftime('%d-%m-%Y')
            
        # Fill in missing date values with default behaviour. 
        elif day or month or year:
            if not year:
                year = self.today.year
            if not month and not day:
                month = 1
                day = 1
            elif not month:
                month = self.today.month
            elif not day:
                day = 1
            due_date = datetime.datetime(int(year), int(month), int(day))
            if due_date < self.today:
                error_window('The due date comes before today.')
                return
            due_date = due_date.strftime('%d-%m-%Y')
            
        else:
            due_date = 'None'
        today = self.today.strftime('%d-%m-%Y')
        
        if new_item:
            self.todo_dict["todo_items"][item_id] = {
                                         "header"     : head,
                                         "priority"   : priority,
                                         "info"       : str(description),
                                         "start_date" : today,
                                         "due_date"   : due_date,
                                         "parents"    : parent_item_ids}
            # Add one to ID ready for next entry.
            self.item_id += 1
            self.todo_dict["current_id"] = self.item_id
            self.update_saved_dict()
            self.add_saved_todo_items()
        else:
            self.todo_dict["todo_items"][item_id]["header"] = head
            self.todo_dict["todo_items"][item_id]["priority"] = priority
            self.todo_dict["todo_items"][item_id]["info"] = str(description)
            self.todo_dict["todo_items"][item_id]["due_date"] = due_date
            self.update_saved_dict()
            self.add_saved_todo_items()
            self.show_info()
        this_window.destroy()
    
    def close_window(self, this_window):
        """
        Close to-do item window without taking information.
        
        """
        this_window.destroy()
    
    def new_file(self):
        """
        Start a new to-do list.
        
        """
        filepath = asksaveasfilename(defaultextension=".todo",
                                     initialdir=os.path.dirname(
                                                os.path.abspath(
                                                inspect.getfile(
                                                inspect.currentframe()))),
                                     filetypes=[("to-do files", "*.todo")])
        if filepath:
            self.filepath  = filepath
            self.todo_dict = new_dict()
            self.update_saved_dict()
            self.item_id   = self.todo_dict["current_id"]
            self.add_saved_todo_items()
            self.remove_info()
        
    def open_file(self):
        """
        Open an existing to-do list.
        
        """
        filepath = askopenfilename(filetypes=[("to-do files", "*.todo")],
                                   initialdir=os.path.dirname(
                                              os.path.abspath(
                                              inspect.getfile(
                                              inspect.currentframe()))))
        if filepath:
            self.filepath  = filepath
            self.todo_dict = open_dict(self.filepath)
            self.item_id   = self.todo_dict["current_id"]
            self.add_saved_todo_items()
            self.remove_info()

    def re_order_list(self, order):
        """
        Reorder to-do list.
        
        """
        self.order = order
        self.todo_dict['order'] = self.order
        self.add_saved_todo_items()
        self.update_saved_dict()

    def check_clear_all(self):
        """
        Display message checking the user wants to clear all.
        
        """
        self.check_window = Tk()
        self.check_window.title("Clear all")
        
        message_frame = Frame(self.check_window)
        message_frame.pack(padx=5, pady=10)
        button_frame = Frame(self.check_window)
        button_frame.pack(pady=5, ipadx=3)
        
        Label(message_frame, text="Clearing all removes all your to-do tasks"\
              " and your history permanently.\nAre you sure you would like to"\
              " clear all?").pack()
        Button(button_frame, text="Yes", 
               command=self.clear_todo_dict).pack(side=LEFT)
        Button(button_frame, text="No", 
               command=self.check_window.destroy).pack(side=RIGHT)

    def clear_todo_dict(self):
        """
        Clear to-do list, including history.
        
        """
        self.todo_dict = new_dict()
        self.update_saved_dict()
        self.item_id = self.todo_dict["current_id"]
        self.add_saved_todo_items()
        self.remove_info()
        self.check_window.destroy()
    
    def show_history(self, hist_type):
        """
        Open new window with past to-do items displayed, either removed items
        or completed items.
        
        """
        hist_window = Tk()
        hist_window.title('History - ' + hist_type.title())
        
        item_frame = Frame(hist_window)
        item_frame.pack(padx=10, pady=10)
        
        Label(item_frame, text="To-Do Item", 
              font=("",14)).grid(row=0, column=0, sticky=W)
        Frame(item_frame).grid(row=0, column=1, padx=10)
        Label(item_frame, text=hist_type.title(), 
              font=("",14)).grid(row=0, column=2, sticky=W)
        
        hist_dict = self.todo_dict["history"][hist_type]
        if hist_dict.values():
            for i, item_dict in enumerate(hist_dict.values()):
                Label(item_frame, 
                      text=item_dict["header"],
                      font=("",12)).grid(row=i+1, column=0, sticky=W)
                Label(item_frame, 
                      text=item_dict["date_"+hist_type]).grid(row=i+1, 
                                                              column=2, 
                                                              sticky=W)
        else:
            Label(item_frame, text="None").grid(sticky=W)
        
        button_frame = Frame(item_frame)
        button_frame.grid(column=2, pady=5, stick=E)
        Button(button_frame, 
               text='Ok', 
               command=lambda: self.close_window(hist_window)).pack(side=RIGHT)
        hist_window.mainloop()
    
    def show_removed(self):
        """
        Show removed items.
        
        """
        self.show_history("removed")

    def show_completed(self):
        """
        Show completed items.
        
        """
        self.show_history("completed")

if __name__ == '__main__':
    
    window = Tk()
    Todo_list(window)
    window.mainloop()
    