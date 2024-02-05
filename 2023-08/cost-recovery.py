import os
import csv
import pandas as pd
import pathlib
from pathlib import Path
import sys
import tabulate
from contextlib import redirect_stdout
from pyfiglet import Figlet
import typing



COST_PER_STARTUP = 1.28
COST_PER_COUNT = 0.64
COST_PER_SHUTDOWN = 9.4

# TYPE ALIAS FOR DATAFRAME
DataFrame = pd.DataFrame

# FUNCTIONS
def get_lab(file: Path) -> str:

    with open(file) as csv_file:
        csv_reader = csv.reader(csv_file)
        rows = list(csv_reader)
    # return(rows[9][0].split(';')[-1]) # USE ID FIELD
    return(rows[12][0].split(';')[-1]) # USE OPERATOR FIELD

def days_counter_used_by_each_lab(df: DataFrame) -> DataFrame:
	"""
	Returns a dataframe with:
	Rows = days
	Cols = lab IDs
	Values = 1.0 if used that day, 0.0 if not used
	"""

	df = df.copy()

	# drop totals row off
	df = df.iloc[:-1,:]
	for i, row in enumerate(df.index):
		for j, val in enumerate(df.loc[row]):
			if val > 0:
				df.loc[row][j] = 1

	for col in df:
		df.loc['Total days used:', col] = df[col].sum()

	return(df)

def costs_for_startup_and_shutdown(df: DataFrame) -> DataFrame:
	"""
	Returns a dataframe with:
	Rows = days
	Cols = lab IDs
	Values = Startup/shutdown cost calculated from the current cost split by the
	number of labs that used the counter that day.
	"""
	
	# copy df to avoid setting on slice error
	df = df.copy()

	# drop totals and counts per day rows / columns
	df = df.iloc[:-1,:]

	for i, row in enumerate(df.index):
		for col in df:
			if df.loc[row, col] > 0:
				df.loc[row, col] = (1 / df.iloc[i,:].astype(bool).sum()) * (COST_PER_STARTUP + COST_PER_SHUTDOWN)

	# add price totals for startup / shutdown
	for col in df:
		df.loc['Total', col] = df[col].sum()

	return(df)

def find_users(path: Path) -> set:
	"""
	Returns the set of labs that used the counter within the month
	"""
	files = list(path.rglob("*.CSV"))
	USE = [get_lab(sample) for sample in files]
	ALL_USERS = set(USE)
	return(ALL_USERS)

def parse_counts(path: Path, users: set[str], days: list[str]) -> DataFrame:
	"""
	Takes a path argument for the base directory of a month's log output from the
	Abbott Celldyn Emerald.
	A set of users from the path
	A list of days the counter was used

	Returns a dataframe with days as rows and labs as columns
	Data is the number of counts performed that day
	"""

	dic_list = []
	for day in days:
		files = list(Path(str(path)+"/"+day).rglob("*.CSV"))

		temp_dict = {}
		for lab in users:
			temp_dict[lab] = 0
			
		for sample in files:
			temp_dict[get_lab(sample)] += 1

		dic_list.append(temp_dict)


	df = pd.DataFrame(dic_list)

	# Set the index to days and name the index
	df = df.set_axis(days)
	df.index.name = "Day"

	# add total column
	for col in df:
		df.loc['Total', col] = df[col].sum()

	return(df)

def print_nice(df: DataFrame) -> None:
	"""
	Uses tabulate package to nicely format a dataframe
	"""

	out = df.to_markdown(index=True, tablefmt='pipe', colalign=['center']*len(df.columns))
	print(out)

def accept_default_values():
 	accept = input(f"Accept default values:\n Cost per count: ${COST_PER_COUNT}\n Cost per startup: ${COST_PER_STARTUP}\n Cost per shutdown: ${COST_PER_SHUTDOWN}\n(Y/N) ?\n")

 	if accept.lower() == 'y':
 		return
 	else:
 		change_default_values()

def change_default_values():

	global COST_PER_COUNT
	global COST_PER_STARTUP
	global COST_PER_SHUTDOWN

	COST_PER_COUNT = float(input("Enter the new value for the cost of ONE COUNT:"))
	COST_PER_STARTUP = float(input("Enter the new value for the cost of ONE STARTUP:"))
	COST_PER_SHUTDOWN = float(input("Enter the new value for the cost of ONE SHUTDOWN:"))
	return(COST_PER_COUNT, COST_PER_STARTUP, COST_PER_SHUTDOWN)
	


# MAIN

def main():
	print(
		"""
	   _____     _ _           _                   ______                          _     _ 
	  / ____|   | | |         | |                 |  ____|                        | |   | |
	 | |     ___| | |______ __| |_   _ _ __ ______| |__   _ __ ___   ___ _ __ __ _| | __| |
	 | |    / _ \ | |______/ _` | | | | '_ \______|  __| | '_ ` _ \ / _ \ '__/ _` | |/ _` |
	 | |___|  __/ | |     | (_| | |_| | | | |     | |____| | | | | |  __/ | | (_| | | (_| |
	  \_____\___|_|_|      \__,_|\__, |_| |_|     |______|_| |_| |_|\___|_|  \__,_|_|\__,_|
	   _____          _     _____ __/ |                                                    
	  / ____|        | |   |  __ \___/                                                     
	 | |     ___  ___| |_  | |__) |___  ___ _____   _____ _ __ _   _                       
	 | |    / _ \/ __| __| |  _  // _ \/ __/ _ \ \ / / _ \ '__| | | |                      
	 | |___| (_) \__ \ |_  | | \ \  __/ (_| (_) \ V /  __/ |  | |_| |                      
	  \_____\___/|___/\__| |_|  \_\___|\___\___/ \_/ \___|_|   \__, |                      
	                                                            __/ |                      
	                                                           |___/                       
	                                                           """
	                                                           )



	# set text rendering font
	f = Figlet(font='slant')

	# DATA FOR TESTING
	p = "/mnt/backedup/home/grahamM/temp/AB18/031121/010372/RESULTS/2023-08"
	q = "/mnt/backedup/home/grahamM/temp/AB18/031121/010372/RESULTS/2023-09"

	# to get script directory
	script_path = os.path.abspath(sys.argv[0])
	pwd = os.path.dirname(script_path)
	home = pathlib.Path(pwd)

	# to use test data
	# home=pathlib.Path(p)
	# days = os.listdir(home)
	days = [item for item in os.listdir(home) if os.path.isdir(item)]
	days = sorted(days)



	# Go through the whole month and find all the users
	ALL_USERS = find_users(home)


	# read in count data to dataframe from filepath (folder output from celldyn)
	df = parse_counts(home, ALL_USERS, days)

	# calculate how many days each lab used the counter on
	days_counter_was_used = days_counter_used_by_each_lab(df)

	# calculate startup and shutdown costs
	startup_and_shutdown_costs = costs_for_startup_and_shutdown(df)

	# calculate qc and bleach cleans
	cost_of_qc = (12*COST_PER_COUNT)/len(ALL_USERS)
	cost_of_bleach_cleans = (4*COST_PER_COUNT)/len(ALL_USERS)

	# ADD UP TOTAL COSTS

	total_cost = {}
	for lab in ALL_USERS:
		total_cost[lab] = (df.loc['Total', lab] * COST_PER_COUNT) + startup_and_shutdown_costs.loc['Total', lab]  + cost_of_qc + cost_of_bleach_cleans

		


	# OUTPUT
	print(f"This month the counter was used on the following days: {days}\n")
	print(f"This month the counter was used by: {ALL_USERS} labs.")


	print(f.renderText('counts'))
	print("Number of counts performed by each lab split by day.\n")
	print_nice(df)

	print(f"\nCost of counts per lab at {COST_PER_COUNT} each:")
	for lab in ALL_USERS:
		print(lab, str("$"+str(df.loc['Total', lab] * COST_PER_COUNT)))

	# DAYS USED BY EACH LAB
	print(f.renderText('use'))
	print("Summary of days the counter was used by each lab.")
	print("1.0 indicates samples were run that day. 0.0 indicates no use.\n")
	print_nice(days_counter_was_used)

	# STARTUP SHUTDOWN
	print("\n\n")
	print(f.renderText('startup /'))
	print(f.renderText('shutdown'))
	print("Breakdown of startup / shutdown costs per lab.\n")
	print_nice(startup_and_shutdown_costs)



	




	# COSTS
	print(f"\nThe number of days used aka the number of startups and shutdowns: {len(days)}")

	print("\nTotal QC counts performed: 12")
	print(f"Cost of QC counts per lab: {cost_of_qc}")
	print("\nTotal bleach cleans performed: 4")
	print(f"Cost of bleach cleans per lab: {cost_of_bleach_cleans}")
	print("\nNote these are not logged electronically and is assumed to be run once a week.")
	print("The QC consists of 3 standards (Low, Normal, High) which are each run once a week.")
	print("The cost of QC and bleach cleans are split evenly amongst all labs using the instrument.")

	print("\n\n")
	print(f.renderText('final costs'))
	for lab, money in total_cost.items():
		print(lab, str("$"+str(round(money,2))))






if __name__ == "__main__":

	# Run this before redirecting stdout

	# Accept default values:
	accept_default_values()


	with open('output.txt', 'w') as f:
		with redirect_stdout(f):
			main()



	
	






