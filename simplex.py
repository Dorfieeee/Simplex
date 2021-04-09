import time
import sys

def build():
	"""Installs all required dependencies from PyPI to run Simplex"""
	import subprocess
	from os import listdir, getcwd
	from os.path import isfile, join
	onlyfiles = [f for f in listdir(getcwd()) if isfile(join(getcwd(), f))]

	if not 'requirements.txt' in onlyfiles:
		raise SystemExit('File including depencencies not found. You will have to install them manually.')

	subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

	print('All dependencies installed successfully.\nYou can run Simplex now!')

if sys.argv[1] == 'build':
	build()
	sys.exit(0)

from helpers import *
import click
@click.group()
# TUPLE OF PROVIDED FILES PATHS [optional]
@click.option("--file", "-f", "_user_file_paths", help="""Provide one or more
			 files(filenames) to process. Select all files in current working directory
			 by default""", multiple=True, type=click.Path(exists=True))
# OUPUT DIRECTORY [optional]
@click.option("--output", "-o", "_user_path_out", help="Provide output directory path")
# INPUT DIRECTORY [optional]
@click.option("--input", "-i", "_user_path_in", help="Provide input directory path(must exist)",
			  type=click.Path(exists=True))
@click.option("--reversed", "-r", "_reversed", is_flag=True, help="Reversed order of scan, reversed"
				+ " scan followed with forward scan. (jvc mode related)")
@click.pass_context
def cli(ctx, _user_path_out, _user_path_in, _user_file_paths, _reversed):
	# ensure that ctx.obj exists and is a dict (in case `cli()` is called
	# by means other than the `if` block below)
	ctx.ensure_object(dict)
	if ctx.invoked_subcommand != 'build':
		ctx.obj['abs_path_in'] = get_abs_path_in(_user_path_in)
		ctx.obj['abs_path_out'] = get_abs_path_out(_user_path_out)
		ctx.obj['user_file_paths'] = get_ufp(_user_file_paths)
		ctx.obj['reversed'] = _reversed

@cli.command()
@click.pass_context
def jvc(ctx):
	"""Current–voltage characteristic + graphs"""
	extension = "ocw"
	jvc_template_out = ["+V [V]", "+J [mA/cm2]", "-V [V]", "-J [mA/cm2]", "+P [W/cm2]", "-P [W/cm2]"]
	jvc_result_template = ["Scan", "Power max", "Voc [V]","Jsc [mA/cm2]", "FF", "PCE (%)"]
	jvc_summary = []			
	jvc_mask_area = click.prompt(
		"Enter mask-area value which will be applied to all provided files.",
			value_proc=check_maskarea)		
	file_paths = ctx.obj['user_file_paths'] or get_files_at(ctx.obj['abs_path_in'], extension)
	make_dir_at(ctx.obj['abs_path_out'])

	for file in progressBar(file_paths, prefix = 'Progress:', suffix = 'Complete', length = 50):				
		filename = extract_filename(file, extension)
		if ctx.obj['user_file_paths']:
			file_path_in = file
		else:
			file_path_in = f"{ctx.obj['abs_path_in']}/{file}"

		file_path_out = f"{ctx.obj['abs_path_out']}/{filename}"

		# READ SOURCE
		scan, file_lenght = read_jvc_file(file_path_in)
		if file_lenght == 0:
			click.echo(f"File {file} has no records")
			continue

		voltage = []
		_voltage = []
		density = []
		_density = []
		power = []
		_power = []

		middle_index = int(file_lenght / 2)		# middle index of source file

		# LOGIC for reversed order of data in source file
		if not ctx.obj['reversed']:
			f_index = 0
			r_index = middle_index
		else:
			f_index = middle_index
			r_index = 0

		for i in range(middle_index):
			voltage.append(calc_voltage(scan[i + f_index][0]))
			_voltage.append(calc_voltage(scan[i + r_index][0]))
			density.append(calc_density(scan[i + f_index][1], jvc_mask_area))
			_density.append(calc_density(scan[i + r_index][1], jvc_mask_area))
			power.append(calc_power(voltage[i], density[i]))
			_power.append(calc_power(_voltage[i], _density[i]))

		# WRITE OUTPUT
		output = transpose([voltage, density, _voltage, _density, power, _power])
		write_csv_file(output, file_path_out, jvc_template_out)

		# WRITE RESULTS
		results = [
			result_row("Forward", power, voltage, density),
			result_row("Reverse", _power, _voltage, _density)
		]
		write_csv_file(results, file_path_out + "-result", jvc_result_template)
		
		for row in results:
			jvc_summary.append([filename] + row)

		if len(file_paths) > 1:
			write_csv_file(jvc_summary, ctx.obj['abs_path_out'] + "/jvc_summary", jvc_result_template)
	
		draw_graph(filename, file_path_out, density, voltage, _density, _voltage)

		time.sleep(0.01)

	finish(ctx.obj['abs_path_out'])

@cli.command()
@click.pass_context
def imp(ctx):
	"""Impedance"""
	extension = "P00"
	file_paths = ctx.obj['user_file_paths'] or get_files_at(ctx.obj['abs_path_in'], extension)
	make_dir_at(ctx.obj['abs_path_out'])

	for file in progressBar(file_paths, prefix = 'Progress:', suffix = 'Complete', length = 50):						
		filename = extract_filename(file, extension)
		file_path_in = f"{ctx.obj['abs_path_in']}/{file}"
		file_path_out = f"{ctx.obj['abs_path_out']}/{filename}"

		# read source
		data = read_imp_file(file_path_in)
		if not data:
			click.echo(f"File {file} has no records to process.")
			continue

		data = format_imp_data(data)

		# write source
		write_imp_file(data, file_path_out)

		time.sleep(0.01)

	finish(ctx.obj['abs_path_out'])

if __name__ == '__main__':
	cli(obj={})