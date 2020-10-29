import click
import sys
import csv
import os
import re
import time
import functools

USAGE = f"Usage: python {sys.argv[0]} [--help] | \
		[--mode|-m <compute|compare|plot>] \
		[--single|-s <absolute file_path> | -s <file_path> -s <file_path>...] \
		[--output|-o <absolute output_directory_path>] \
		[--input|-i <absolute input_directory_path>]"

OUTPUT_template = ["+V [V]",	"-V [V]",	"+J [mA/cm2]",	"-J [mA/cm2]",	"+P [W/cm2]",	"-P [W/cm2]"]
RESULT_template = ["Scan", "Power max", "Voc [V]","Jsc [mA/cm2]", "FF", "PCE (%)"]

# Initialize global variables 
SUMMARY = []

# Command line argument parser
@click.command()
# PROGRAM MODE OPTION [optional]
@click.option("--mode", "-m", type=click.Choice(['compute','compare', 'plot']),
			 help="Select program's mode", default='compute')
# TUPLE OF PROVIDED FILES [optional]
@click.option("--single", "-s", "files", help="""Explicitly select one or more
			 files to process. Select all file in current working directory
			 by default""", multiple=True, type=click.Path(exists=True))
# OUPUT DIRECTORY [optional]
@click.option("--output", "-o", "dir_out", help="Explicitly select output directory",
			  type=click.Path())
# INPUT DIRECTORY [optional]
@click.option("--input", "-i", "dir_in", help="Explicitly select input directory",
			  type=click.Path(exists=True))
def main(mode: str, files: tuple, dir_out: str, dir_in: str) -> None:
	'''Program's description'''
	if dir_in == None:
		# Set files input to the current working directory as default
		SOURCE_PATH = os.getcwd()
	else:
		SOURCE_PATH = dir_in

	if not files:
		# File name pattern
		pattern = r"^[^\.][\w,\s-]+\.ocw"
		# Select all files inside source directory which match required pattern
		files = [file for file in os.listdir(SOURCE_PATH) if re.match(pattern, file)]
		if not files:
			raise SystemExit("No files to process found in {}".format(SOURCE_PATH))
		# If all files are numbered, sort them by number within their name
		# If any of them is not numbered, pass
		if [file for file in files if re.search(r"\d", file) is None]:
			pass
		else:
			files.sort(key=lambda name: sort_by_number(name))

	if dir_out == None:
		# Create new directory in cwd named after the first file
		# Append "(attempt_counter)" to the directory name if another
		# directory with the same name already exists MAX 99 
		foldername = re.search(r"[\w\d,-]+(?=\.ocw)", files[0])[0]
		if (OUTPUT_PATH := check_dirname(os.getcwd(), foldername)) is None:
			raise SystemExit(f"Could not create folder on path: {dir_out}")
	else:
		OUTPUT_PATH = dir_out
	try:
		os.mkdir(OUTPUT_PATH)
		pass
	except OSError:
		raise SystemExit(f"Could not create folder on path: {dir_out}\n" \
						   "Make sure other folder with the same name doesn't already exist.")
	

	if mode == 'compute':
		MASK_AREA = click.prompt(
			"Enter mask-area value which will be applied to all files",
			 value_proc=check_maskarea)

	for file in progressBar(files, prefix = 'Progress:', suffix = 'Complete', length = 50):	
		if mode == 'compare' or mode == 'plot':
			raise SystemExit("This function is not yet supported\nI'm working on it!")

		scan = []
		output = []
		filename = re.search(r"[\w\d,-]+(?=\.ocw)", file)[0]
		source_file = f"{SOURCE_PATH}/{file}"
		output_file = f"{OUTPUT_PATH}/{filename}"

		# READ SOURCE
		if (source_file_length := read_file(source_file, scan)) == 0:
			click.echo(f"File {file} has no records")
			continue

		voltage = []
		_voltage = []
		density = []
		_density = []
		power = []
		_power = []
		m = int(source_file_length / 2)					# middle index of source file
		for i in range(m):
			voltage.append(calc_voltage(scan[i][0]))
			_voltage.append(calc_voltage(scan[i + m][0]))
			density.append(calc_density(scan[i][1], MASK_AREA))
			_density.append(calc_density(scan[i + m][1], MASK_AREA))
			power.append(calc_power(voltage[i], density[i]))
			_power.append(calc_power(_voltage[i], _density[i]))

		if mode == 'compute':
			# WRITE OUTPUT
			output = transpose([voltage, density, _voltage, _density, power, _power])
			write_csv_file(output, output_file, OUTPUT_template)

			# WRITE RESULTS
			results = [
				result_row("Forward", power, voltage, density),
				result_row("Reverse", _power, _voltage, _density)
			]
			write_csv_file(results, output_file + "-result", RESULT_template)
			
			for row in results:
				SUMMARY.append([filename] + row)

			if len(files) > 1:
				write_csv_file(SUMMARY, OUTPUT_PATH + "/SUMMARY", RESULT_template)

		time.sleep(0.01)


#### FUNCTIONS DEFINITIONS ####
def read_file(path, destination):
	row_counter = 0
	with open(path, 'r', newline='') as f:
		reader = csv.reader(f)
		for row in reader:		
			# Trim whitespace, separate values and store them in list 'd'
			d = ''.join(row).strip().split()
			# Each row can be only of length 2 => 2 values
			if len(d) != 2: 
				continue
			row_counter += 1
			# Cast each value pair to float and append as tuple to scan list
			destination.append( (float(d[0]), float(d[1])) )
	return row_counter

def write_csv_file(iterable, destination, header):
	with open(f"{destination}.csv", 'w', newline='') as f:
		writer = csv.writer(f)
		writer.writerow(header)			
		writer.writerows(iterable)
	return

def calc_voltage(V):
	return V * -1

def calc_density(A, MA):
	return (A / MA) * 1000

def calc_power(V, J):
	return V * J

def number_sign(n):
	if n > 0:
		return True
	elif n < 0:
		return False
	return None

def cod(ls):
	'''
	Change of direction

	Returns the first index of number from a list before a 
	sign turns negative or the first index after it turns 
	positive depending on initial sign
	'''
	index = -1
	init_sign = number_sign(ls[0])

	for i, n in enumerate(ls):
		if number_sign(n) is not init_sign:
			if init_sign:
				index = i - 1
			else:
				index = i
			break
	return index

def sort_by_number(el):
	m = re.match(r"\D+(?P<number>\d+)\D", el)
	return int(m.group('number'))

def check_dirname(path, name):
	local_paths = os.listdir(path)
	root = name
	counter = 0
	while(name in local_paths):
		counter += 1
		name = f"{root}({counter})"
		if counter == 100:
			return None
	return f"{path}\\{name}"

def transpose(list):
	list_T = []

	for i in range(len(list[0])):
		row = []
		for j in range(len(list)):
			row.append(list[j][i])
		list_T.append(row)

	return list_T

def result_row(text, power, voltage, density):
	pm = max(power)
	jsc = density[cod(voltage)]
	voc = voltage[cod(density)]
	ff = pm / (voc * jsc)
	pce = voc * jsc * ff / 100.0
	return [text, pm, voc, jsc, ff, pce]

def check_maskarea(value):
	try:
		value = float(value)
	except:
		raise click.BadParameter("Mask-area is not of type float.", param=value)
	if value == 0:
		raise click.BadParameter("Mask-area can not be equal to 0.", param=value)
	return value

# Source https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console/34325723#34325723
def progressBar(iterable, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)
    # Progress Bar Printing Function
    def printProgressBar (iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()

if __name__ == '__main__':
	main()