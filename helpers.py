import csv
import re
import os
import click
import matplotlib.pyplot as plt

def get_ufp(user_paths):
    ufp = []
    if user_paths:
        for f in user_paths:
            if os.path.exists(f):
                ufp.append(f)
            else:
                raise SystemExit(f"File at {f} could not be found.")
    return ufp

def get_abs_path_out(user_path):
    if user_path == None:
        # Prompt for a foldername and create new directory, if there's name collision, append numeric value
        foldername = click.prompt('Enter name of your output directory')
        ABS_PATH_OUT = check_dirname(os.getcwd(), foldername)
        if ABS_PATH_OUT is None:
            raise SystemExit(f"Could not create folder on path: {user_path}")
        return ABS_PATH_OUT
    else:
        return os.path.abspath(user_path)

def get_abs_path_in(user_path):
    if user_path == None:
    # Set files input to the current working directory as default
        return os.getcwd()
    else:
        return os.path.abspath(user_path)

def extract_filename(path, extension):
	pattern = re.compile(f"([^<>:;,?\"*|\\\/]+)\.{extension}$")
	result = pattern.search(path)
	return result.group(1)

def get_files_at(path, with_extension):
	# Select all files inside source directory which match required pattern
	filename_pattern = re.compile(f".{with_extension}$")
	files = [file for file in os.listdir(path) if filename_pattern.search(file)]
	if not files:
		raise SystemExit(f"No files to process found at {path}")
	return files

def make_dir_at(path):
	# Create directory
	try:
		os.mkdir(path)
		pass
	except OSError:
		raise SystemExit(f"Could not create folder at path: {path}\n" \
						"Make sure other folder with the same name doesn't already exist.") 

def finish(path):
	click.echo(f"Your files can be found at path {path}")

def read_imp_file(path):
	data = []
	with open(path, 'rb') as reader:
		# decode and skip first 6 lines
		text = reader.read().decode(errors='replace').split('\r\n')[6:-1]
		for line in text:
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

def read_jvc_file(path):
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

def check_dirname(path, name=''):
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