**BTP: Repository Analyzer**

**Completed Tasks**
1. Plotting the repository as a tree visually
2. Added the node data for File name, Directory Names
3. Added the data for number of commits
4. Highlighted files which gets updated recently and files which are not committed in long time [2 years]
5. Added the number of lines part for the files
6. Created the selective filter to get access to a certain directory inside parent directory
7. Created a filter to get only the files which have at least inputted threshold value of number of lines
8. Specifically removed the .directories as they are redundant to user
9. Added the functionality to redirect to file location on clicking on the nodes in SVG output.


**Changes from Last Iteration**
Change in Tree plotting library (GraphViz):
    Due to lack of support for ETE3 and ETE4 and complex dependencies.
    [e.g. Python3 doesnt support ETE3, Libraries installation mismatched in documentation and github repository, multiple installation errors (not resolvable from ETE github issues forum)]

# COLOR CODES:
BLUE - Most Vulnerable
SKYBLUE - Not committed since last 2 years
RED - Committed recently only (2 months)
