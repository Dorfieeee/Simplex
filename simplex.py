import csv
import os
import re
import time

import click
import matplotlib.pyplot as plt

# Command line argument parser
@click.command(options_metavar="mode <file> <input> <output>")
# PROGRAM MODE OPTION [optional]
@click.option("--mode", "-m", type=click.Choice(['gvc', 'imp']), required=True,
			 help="Select program's mode [gvc - gv curve; imp - impedance]")
# TUPLE OF PROVIDED FILES [optional]
@click.option("--file", "-f", "files", help="""Provide one or more
			 files(filenames) to process. Select all files in current working directory
			 by default""", multiple=True, type=click.Path(exists=True))
# OUPUT DIRECTORY [optional]
@click.option("--output", "-o", "dir_out", help="Provide output directory path",
			  type=click.Path(exists=True))
# INPUT DIRECTORY [optional]
@click.option("--input", "-i", "dir_in", help="Provide input directory path",
			  type=click.Path(exists=True))
@click.option("--reversed", "-r", is_flag=True, help="Reversed order of scan, reversed"
				+ " scan followed with forward scan. (gvc mode related)")
def main(mode, files, dir_out, dir_in, reversed) -> None:

	if dir_in == None:
	# Set files input to the current working directory as default
		SOURCE_PATH = os.getcwd()
	else:
		SOURCE_PATH = dir_in	

	if dir_out == None:
	# Prompt for a foldername and create new directory, if there's name collision, append numeric value
		foldername = click.prompt('Enter name of your output directory')
		OUTPUT_PATH = check_dirname(os.getcwd(), foldername)
		if OUTPUT_PATH is None:
			raise SystemExit(f"Could not create folder on path: {dir_out}")
	else:
		OUTPUT_PATH = dir_out


	if mode == "gvc":
		OUTPUT_template = ["+V [V]", "-V [V]", "+J [mA/cm2]", "-J [mA/cm2]", "+P [W/cm2]", "-P [W/cm2]"]
		RESULT_template = ["Scan", "Power max", "Voc [V]","Jsc [mA/cm2]", "FF", "PCE (%)"]
		# Initialize global variables 
		SUMMARY = []			
		MASK_AREA = click.prompt(
			"Enter mask-area value which will be applied to all files",
				value_proc=check_maskarea)
		extension = "ocw"
		filename_pattern = re.compile(f".{extension}$")
		
	if mode == "imp":
		extension = "P00"
		filename_pattern = re.compile(f".{extension}$")

	# If user does not provide file path/s, select all files in current directory by default
	if not files:
		# Select all files inside source directory which match required pattern
		files = [file for file in os.listdir(SOURCE_PATH) if filename_pattern.search(file)]
		if not files:
			raise SystemExit(f"No files to process found in {SOURCE_PATH}")
		# If all files are numbered, sort them by number within their name
		# If any of them is not numbered, pass
		# if [file for file in files if re.search(r"\d", file) is None]:
		# 	pass
		# else:
		# 	files.sort(key=lambda name: sort_by_number(name))
	
	# Create directory
	try:
		os.mkdir(OUTPUT_PATH)
		pass
	except OSError:
		raise SystemExit(f"Could not create folder on path: {dir_out}\n" \
						"Make sure other folder with the same name doesn't already exist.") 

#--------------------------------------------------------------------------------------
	if mode == "gvc":
		for file in progressBar(files, prefix = 'Progress:', suffix = 'Complete', length = 50):				
			filename = re.search(rf".+(?=\.{extension})", file)[0]
			source_file = f"{SOURCE_PATH}/{file}"
			output_file = f"{OUTPUT_PATH}/{filename}"

			# READ SOURCE
			scan, source_file_length = read_gvc_file(source_file)
			if source_file_length == 0:
				click.echo(f"File {file} has no records")
				continue

			voltage = []
			_voltage = []
			density = []
			_density = []
			power = []
			_power = []

			middle_index = int(source_file_length / 2)		# middle index of source file

			# LOGIC for reversed order of data in source file
			if not reversed:
				f_index = 0
				r_index = middle_index
			else:
				f_index = middle_index
				r_index = 0

			for i in range(middle_index):
				voltage.append(calc_voltage(scan[i + f_index][0]))
				_voltage.append(calc_voltage(scan[i + r_index][0]))
				density.append(calc_density(scan[i + f_index][1], MASK_AREA))
				_density.append(calc_density(scan[i + r_index][1], MASK_AREA))
				power.append(calc_power(voltage[i], density[i]))
				_power.append(calc_power(_voltage[i], _density[i]))

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
		
			draw_graph(filename, output_file, density, voltage, _density, _voltage)

			time.sleep(0.01)

		finish()

	if mode == "imp":
		for file in progressBar(files, prefix = 'Progress:', suffix = 'Complete', length = 50):						
			filename = re.search(rf".+(?=\.{extension})", file)[0]
			source_file = f"{SOURCE_PATH}/{file}"
			output_file = f"{OUTPUT_PATH}/{filename}"

			# read source
			data = read_imp_file(source_file)
			if not data:
				click.echo(f"File {file} has no records to process.")
				continue

			data = format_imp_data(data)

			# write source
			write_imp_file(data, output_file)

			time.sleep(0.01)

		finish()
#--------------------------------------------------------------------------------------

#### FUNCTIONS DEFINITIONS ####
def finish():
	click.echo("Done! :)")

def read_imp_file(path):
	data = []
	with open(path, 'r', newline='') as reader:
		for line in reader.readlines()[6:]: # skip first 6 lines
			line = ''.join(line).strip().split()
			data.append( [float(val) for val in line] )
	return data

def write_imp_file(data, path):
	with open(f"{path}.txt", 'w', newline='') as writer:
		for value in data:
			writer.write('\t'.join(value) + '\n')

def format_imp_data(data):
	# data => | f/Hz | Z'/Ohm | -Z''/Ohm | time/s | Edc/V | Idc/A |
	nums = [[lst[0], lst[1], lst[2] * -1] for lst in data]
	return [[str(n) for n in lst] for lst in nums]

def plot_filter(d, v, _d, _v):
	for i in range(len(d)):
		if d[i] > 0 and v[i] > 0:
			_d.append(d[i])
			_v.append(v[i])

def read_gvc_file(path):
	scan = []
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
			scan.append( [float(value) for value in d] )
	return scan, row_counter

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
	last_with_name = sorted([fname for fname in local_paths if re.match(rf"^{name}", fname)], reverse=True)
	if not last_with_name:
		return f"{path}\\{name}"
	last_with_name = last_with_name[0]
	number_pattern = re.compile("\((\d+)\)$")
	number = number_pattern.search(last_with_name) # returns Match object
	if not number:
		return f"{path}\\{name}(1)"
	number = int(number.group(1)) + 1
	return f"{path}\\{name}({number})"

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

def draw_graph(title, destination, density, voltage, _density, _voltage):
	d = []
	v = []
	_d = []
	_v = []

	plot_filter(density, voltage, d, v)
	plot_filter(_density, _voltage, _d, _v)

	plt.figure() # open new window

	plt.plot(v, d, color='black', label="Forward scan")
	plt.plot(_v, _d, color='red', label="Reverse scan")

	plt.title(title)

	plt.ylabel('Current Density (mA/cm2)')
	plt.xlabel('Voltage (V)')

	plt.legend()

	plt.ylim(ymin=0)
	plt.xlim(xmin=0)

	plt.savefig(destination)

	plt.close() # close current window

if __name__ == '__main__':
	main()