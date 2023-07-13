from __future__ import print_function
import webbrowser
import pathlib
import os
import sys
import argparse
import json
import git

parser = argparse.ArgumentParser()
parser.add_argument("--file-path", type=str, help="optional filename")
parser.add_argument('-d-', '--dir-names', type=str, action = 'append', help='optional filename')
parser.add_argument('--min-loc', type=int, help='optional filename')
args = parser.parse_args()
root_dir = args.file_path
dir_params = args.dir_names
min_thresh = args.min_loc


SPACE_PREFIX = "  "
DIR_PREFIX = "@"
FILE_PREFIX = "#"

class TreeNode:
    def __init__(self, data):
        self.data = data
        self.files_in_this = []
        self.dirs_in_this = []
        self.parent = None
        self.wanted = False
        self.rel_path = ""
        self.lines_of_code = 0
        self.main = False
        self.minloc = False

    def add_child(self, child_node, type, rel_path, lines=""):
        child_node.parent = self
        if type == "file":
            self.files_in_this.append(child_node)
            child_node.rel_path = rel_path
            child_node.lines_of_code = lines
        else:
            self.dirs_in_this.append(child_node)
            child_node.rel_path = rel_path
            child_node.lines_of_code = -1


class Pair:
    def __init__(self, _node, _childrenIndex):
        self.node = _node
        self.childrenIndex = _childrenIndex


currentRootIndex = 0
stack = []
postorderTraversal = []

max_loc = 0
max_commits = 0
mv_node = TreeNode

def get_commit_count_raw(filepath):
    repo = git.Repo(root_dir)
    commits = repo.iter_commits('--all', since="4.months.ago", paths=filepath)
    return len(list(commits))

def get_commit_count(filepath):
    repo = git.Repo(root_dir)
    commits = repo.iter_commits('--all', paths=filepath)
    return "~" + str(len(list(commits)))

def get_commit_count_prev(filepath):
    repo = git.Repo(root_dir)
    commitss = repo.iter_commits('--all', since="2.years.ago", paths=filepath)
    return "~" + str(len(list(commitss)))

def get_commit_count_latest(filepath):
    repo = git.Repo(root_dir)
    commitss = repo.iter_commits('--all', since="2.months.ago", paths=filepath)
    return "~" + str(len(list(commitss)))

def postorder(root_node):
    input_string = ""
    if len(root_node.dirs_in_this) == 0 and len(root_node.files_in_this) == 0:
        return input_string + "~1~1"
    
    if(len(root_node.files_in_this) != 0 or len(root_node.dirs_in_this) != 0):
        input_string += ': { "children": ['
       
    for i in range(len(root_node.dirs_in_this)):
        rel_path = str(root_node.dirs_in_this[i].rel_path)

        input_string += '{'
        input_string += '"' + str(root_node.dirs_in_this[i].data) + "~NA" + get_commit_count(rel_path)+ "~" + rel_path + '"'
        input_string += postorder(root_node.dirs_in_this[i])

        if(len(root_node.files_in_this) == 0 and i == len(root_node.dirs_in_this) - 1):
            input_string += "}"
        else:
            input_string += "}, "

    if(len(root_node.files_in_this) != 0):
        for i in range(len(root_node.files_in_this)):
            rel_path = str(root_node.files_in_this[i].rel_path)
            loc = str(root_node.files_in_this[i].lines_of_code)

            if(mv_node == root_node.files_in_this[i]):                
                input_string += '"' + str(root_node.files_in_this[i].data) + "~" + loc + get_commit_count(rel_path) + get_commit_count_prev(rel_path) + get_commit_count_latest(rel_path) + "~" + rel_path + "~MAX" + '"'
            else:
                input_string += '"' + str(root_node.files_in_this[i].data) + "~" + loc + get_commit_count(rel_path) + get_commit_count_prev(rel_path) + get_commit_count_latest(rel_path) + "~" + rel_path + '"'

            if i != len(root_node.files_in_this) - 1:
                input_string += ", "

    if(len(root_node.files_in_this) != 0 or len(root_node.dirs_in_this) != 0):
        input_string += ']}'

    return input_string

def postorder_filter(root_node):
    input_string = ""
    wanted_files = 0
    wanted_dirs = 0

    for i in range(len(root_node.dirs_in_this)):
        if (root_node.dirs_in_this[i].wanted):
            wanted_dirs += 1
    
    for i in range(len(root_node.files_in_this)):
        if (root_node.files_in_this[i].wanted):
            wanted_files+= 1

    if len(root_node.dirs_in_this) == 0 and len(root_node.files_in_this) == 0:
        return input_string + "~1~1"
    
    if(wanted_files != 0 or wanted_dirs != 0):
        input_string += ': { "children": ['
       
    wanted_files = 0
    wanted_dirs = 0

    for i in range(len(root_node.dirs_in_this)):
        if (root_node.dirs_in_this[i].wanted):
            wanted_dirs += 1
    
    for i in range(len(root_node.files_in_this)):
        if (root_node.files_in_this[i].wanted):
            wanted_files+= 1

    w_i =0 

    for i in range(len(root_node.dirs_in_this)):
        if (root_node.dirs_in_this[i].wanted):
            rel_path = str(root_node.dirs_in_this[i].rel_path)

            input_string += '{'
            input_string += '"' + str(root_node.dirs_in_this[i].data) + "~NA" + get_commit_count(rel_path)+ "~" + rel_path + '"'
            input_string += postorder_filter(root_node.dirs_in_this[i])

            if(wanted_files == 0 and w_i == wanted_dirs - 1):
                input_string += "}"
            else:
                input_string += "}, "
            
            w_i += 1

    w_i =0
    for i in range(len(root_node.files_in_this)):
        if (root_node.files_in_this[i].wanted):
            rel_path = str(root_node.files_in_this[i].rel_path)
            loc = str(root_node.files_in_this[i].lines_of_code)

            if(mv_node == root_node.files_in_this[i]):                
                input_string += '"' + str(root_node.files_in_this[i].data) + "~" + loc + get_commit_count(rel_path) + get_commit_count_prev(rel_path) + get_commit_count_latest(rel_path) + "~" + rel_path + "~MAX" + '"'
            else:
                input_string += '"' + str(root_node.files_in_this[i].data) + "~" + loc + get_commit_count(rel_path) + get_commit_count_prev(rel_path) + get_commit_count_latest(rel_path) + "~" + rel_path + '"'

            if w_i != wanted_files - 1:
                input_string += ", "
            
            w_i += 1

    if(len(root_node.files_in_this) != 0 or len(root_node.dirs_in_this) != 0):
        input_string += ']}'

    return input_string

def postorder_threshold(root_node):
    input_string = ""
    if len(root_node.dirs_in_this) == 0 and len(root_node.files_in_this) == 0:
        return input_string + "~1~1"
    
    if(len(root_node.files_in_this) != 0 or len(root_node.dirs_in_this) != 0):
        input_string += ': { "children": ['
       
    for i in range(len(root_node.dirs_in_this)):
        if (root_node.dirs_in_this[i].minloc):
            rel_path = str(root_node.dirs_in_this[i].rel_path)

            input_string += '{'
            input_string += '"' + str(root_node.dirs_in_this[i].data) + "~NA" + get_commit_count(rel_path) + "~" + rel_path + '"'
            input_string += postorder_threshold(root_node.dirs_in_this[i])

            if(len(root_node.files_in_this) == 0 and i == len(root_node.dirs_in_this) - 1):
                input_string += "}"
            else:
                input_string += "}, "

    for i in range(len(root_node.files_in_this)):
        if (root_node.files_in_this[i].minloc):
            rel_path = str(root_node.files_in_this[i].rel_path)
            loc = str(root_node.files_in_this[i].lines_of_code)

            if(mv_node == root_node.files_in_this[i]):                
                input_string += '"' + str(root_node.files_in_this[i].data) + "~" + loc + get_commit_count(rel_path) + get_commit_count_prev(rel_path) + get_commit_count_latest(rel_path) + "~" + rel_path + "~MAX" + '"'
            else:
                input_string += '"' + str(root_node.files_in_this[i].data) + "~" + loc + get_commit_count(rel_path) + get_commit_count_prev(rel_path) + get_commit_count_latest(rel_path) + "~" + rel_path + '"'

            if i != len(root_node.files_in_this) - 1:
                input_string += ", "

    if(len(root_node.files_in_this) != 0 or len(root_node.dirs_in_this) != 0):
        input_string += ']}'

    return input_string


def dfs_filter(node, inp):
    if node.data in inp:
        node.wanted = True

        def dfs_in(node):
            node.wanted = True
   
            for i in range(len(node.files_in_this)):
                dfs_in(node.files_in_this[i])
            for i in range(len(node.dirs_in_this)):
                dfs_in(node.dirs_in_this[i])

        dfs_in(node)
        return True
    for i in range(len(node.files_in_this)):
        wanted = dfs_filter(node.files_in_this[i], inp)
        if wanted:
            node.wanted = True
    for i in range(len(node.dirs_in_this)):
        wanted = dfs_filter(node.dirs_in_this[i], inp)
        if wanted:
            node.wanted = True
    if node.wanted:
        return True
    return False

def dfs_thres(node, inp):
    if node.lines_of_code >= inp:
        node.minloc = True
        def dfs_in(node):
            node.minloc = True

            for i in range(len(node.files_in_this)):
                dfs_in(node.files_in_this[i])
            for i in range(len(node.dirs_in_this)):
                dfs_in(node.dirs_in_this[i])

        dfs_in(node)
        return True
    for i in range(len(node.files_in_this)):
        minloc = dfs_thres(node.files_in_this[i], inp)
        if minloc:
            node.minloc = True
    for i in range(len(node.dirs_in_this)):
        minloc = dfs_thres(node.dirs_in_this[i], inp)
        if minloc:
            node.minloc = True
    if node.minloc:
        return True
    return False


def add_body(root):
    dir_iter = root.iterdir()
    dirs_path = []
    files_path = []
    count = 0
    root_node = TreeNode(f"{root.name}{os.sep}")

    connector = DIR_PREFIX
    for item in dir_iter:
        if item.is_file():
            files_path.append(item)

        elif item.is_dir():
            if(str(item.name)[0] != '.'):
                dirs_path.append(item)

    global max_loc
    global max_commits
    global mv_node

    for i in range(len(files_path)):
        connector = FILE_PREFIX
        inp = f"{files_path[i].name}"

        with open(files_path[i], "rb") as fp:
            for count, line in enumerate(fp):
                pass

        num_lines = count+1

        if num_lines >= max_loc:
            max_loc = num_lines

        files = TreeNode(inp)
        files.parent = root_node
        rel_path = str(files_path[i])
        root_node.add_child(files, "file", rel_path, num_lines)

        # calling function everytime and not storing values as there can be n types of commit related data
        num_commits = get_commit_count_raw(rel_path)

        if(num_commits > max_commits):
            mv_node = files
            max_commits = num_commits
            max_loc = num_lines
        elif(num_commits == max_commits):
            if(num_lines > max_loc):
                mv_node = files
                max_loc = num_lines

    for i in range(len(dirs_path)):
        connector = DIR_PREFIX
        inp = dirs_path[i].name
        dirs = add_body(dirs_path[i])
        rel_path = str(dirs_path[i])
        if(len(rel_path.replace(root_dir, "").split(".")) <= 1):
            dirs.parent = root_node
            root_node.add_child(dirs, "dir", rel_path)

    return root_node

# make tree function
def tree_make(root):
    return add_body(root)


#JSON to DOT format 
def DOT_conversion(json_array):    
    data = json.loads(json_array)

    edges = []

    def get_edges(treedict, parent=None):
        name = next(iter(treedict.keys()))
        if parent is not None:
            edges.append((parent, name))
        for item in treedict[name]["children"]:
            if isinstance(item, dict):
                get_edges(item, parent=name)
            else:
                edges.append((name, item))

    get_edges(data)

    # Dump edge list in Graphviz DOT format
    with open("input.txt", "w") as f:
        add_text = "strict digraph tree {"
        for row in edges:
            first = row[0]
            second = row[1]

            first_attr = first.split("~")
            second_attr = second.split("~")

            first_attr[0] = first_attr[0].replace("/","")
            first_attr[0] = first_attr[0].replace(".","#")
            first_attr[0] = first_attr[0].replace("-","")
            first_attr[0] = first_attr[0].replace(" ","")

            second_attr[0] = second_attr[0].replace("/","")
            second_attr[0] = second_attr[0].replace(".","#")
            second_attr[0] = second_attr[0].replace("-","")
            second_attr[0] = second_attr[0].replace(" ","")

            add_text += """rankdir=LR;
            {0} [style=rounded]""".format(first_attr[0])

            location_pref = root_dir + "/"

            # COLOR CODES:
            # BLUE - Most Vulnerable
            # SKYBLUE - Not committed since last 2 years
            # RED - Committed recently only (2 months)

            if(len(first_attr) > 6 and first_attr[6] == 'MAX'):
                add_text += """
                        [label=<
                        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" ALIGN="CENTER" BGCOLOR="blue" HREF="{}">
                    """.format(first_attr[-2])

                add_text += """<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="24.0" FACE="ambrosia">{0}</FONT></TD></TR>
                        <TR><TD ALIGN="CENTER">#Lines : {1}</TD></TR>
                        <TR><TD ALIGN="CENTER">#Commits : {2}</TD></TR>
                        </TABLE>>];

                """.format(*first_attr)

            elif(len(first_attr) > 5 and first_attr[3] == '0'):
                add_text += """
                        [label=<
                        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" ALIGN="CENTER" BGCOLOR="skyblue3" HREF="{}">
                    """.format(first_attr[-1])
                
                add_text += """<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="24.0" FACE="ambrosia">{0}</FONT></TD></TR>
                        <TR><TD ALIGN="CENTER">#Lines : {1}</TD></TR>
                        <TR><TD ALIGN="CENTER">#Commits : {2}</TD></TR>
                        </TABLE>>];

                """.format(*first_attr)

            elif(len(first_attr) > 5 and first_attr[4] != '0'):
                add_text += """
                        [label=<
                        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" ALIGN="CENTER" BGCOLOR="red" HREF="{}">
                    """.format(first_attr[-1])
                
                add_text += """<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="24.0" FACE="ambrosia">{0}</FONT></TD></TR>
                        <TR><TD ALIGN="CENTER">#Lines : {1}</TD></TR>
                        <TR><TD ALIGN="CENTER">#Commits : {2}</TD></TR>
                        </TABLE>>];

                """.format(*first_attr)

            else:
                add_text += """
                        [label=<
                        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" ALIGN="CENTER" HREF="{}">
                    """.format(first_attr[-1])
                
                add_text += """<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="24.0" FACE="ambrosia">{0}</FONT></TD></TR>
                        <TR><TD ALIGN="CENTER">#Lines : {1}</TD></TR>
                        <TR><TD ALIGN="CENTER">#Commits : {2}</TD></TR>
                        </TABLE>>];

                """.format(*first_attr)

            add_text += """{0} [style=rounded]""".format(second_attr[0])



            if(len(second_attr) > 6 and second_attr[6] == 'MAX'):
                add_text += """
                        [label=<
                        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" ALIGN="CENTER" BGCOLOR="blue" HREF="{}">
                    """.format(second_attr[-2])
                
                add_text += """<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="24.0" FACE="ambrosia">{0}</FONT></TD></TR>
                        <TR><TD ALIGN="CENTER">#Lines : {1}</TD></TR>
                        <TR><TD ALIGN="CENTER">#Commits : {2}</TD></TR>
                        </TABLE>>];

                """.format(*second_attr)

            elif(len(second_attr) > 5 and second_attr[3] == '0'):
                add_text += """
                        [label=<
                        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" ALIGN="CENTER" BGCOLOR="skyblue3" HREF="{}">
                    """.format(second_attr[-1])
                
                add_text += """<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="24.0" FACE="ambrosia">{0}</FONT></TD></TR>
                        <TR><TD ALIGN="CENTER">#Lines : {1}</TD></TR>
                        <TR><TD ALIGN="CENTER">#Commits : {2}</TD></TR>
                        </TABLE>>];

                """.format(*second_attr)

            elif(len(second_attr) > 5 and second_attr[4] != '0'):
                add_text += """
                        [label=<
                        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" ALIGN="CENTER" BGCOLOR="red" HREF="{}">
                    """.format(second_attr[-1])
                
                add_text += """<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="24.0" FACE="ambrosia">{0}</FONT></TD></TR>
                        <TR><TD ALIGN="CENTER">#Lines : {1}</TD></TR>
                        <TR><TD ALIGN="CENTER">#Commits : {2}</TD></TR>
                        </TABLE>>];

                """.format(*second_attr)

            else:
                add_text += """
                        [label=<
                        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" ALIGN="CENTER" HREF="{}">
                    """.format(second_attr[-1])
                
                add_text += """<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="24.0" FACE="ambrosia">{0}</FONT></TD></TR>
                        <TR><TD ALIGN="CENTER">#Lines : {1}</TD></TR>
                        <TR><TD ALIGN="CENTER">#Commits : {2}</TD></TR>
                        </TABLE>>];

                """.format(*second_attr)


            add_text += """
            {0} -> {1};
            """.format(first_attr[0], second_attr[0])
            
        add_text += "}"
        print(add_text, file=f)
        f.close()

#Main function
if __name__ == "__main__":

    root_node = tree_make(pathlib.Path(root_dir))
    # print(root_dir)

    # Doing DFS for filtering
    # Converting the repo tree as a sJSON string

    if dir_params:
        dfs_filter(root_node, dir_params)
        input_string = "{"
        input_string += '"' + str(root_node.data) + "~NA~NA~" + root_dir + '"'
        input_string += postorder_filter(root_node)
        input_string += "}"

    elif min_thresh:
        dfs_thres(root_node, min_thresh)
        input_string = "{"
        input_string += '"' + str(root_node.data) + "~NA~NA~" + root_dir + '"'
        input_string += postorder_threshold(root_node)
        input_string += "}"

    else:
        input_string = "{"
        input_string += '"' + str(root_node.data) + "~NA~NA~" + root_dir + '"'
        input_string += postorder(root_node)
        input_string += "}"

    # print(input_string)
    DOT_conversion(input_string)

    #output the DOT string to SVG
    os.system("dot -Tsvg input.txt > output.svg")

    #open the SVG in browser
    filename = 'file:///'+os.getcwd()+'/' + 'output.svg'
    webbrowser.open_new_tab(filename)

