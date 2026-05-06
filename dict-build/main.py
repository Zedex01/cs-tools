from itertools import product
import os, time, glob
from concurrent.futures import ProcessPoolExecutor
import sys #Allows for the use of argv
"""
template:
    dictbuild -n 2 -s 2 -w 2 -dr/-d 4 wordlist


    -n|-numbers | Max # of times a num can appear in a password
    -s|-sym,-symbols| Max # of symbols that can appear in a password
"""

"""=================================================================
	Settings
================================================================="""
#Limits:
WORDS = 2
NUMBERS = 2
SYMBOLS = 2

NUM_RANGE = 100

#Custom Words
prelist = []

OUT_DIR = "X:\\tmp\\"
"""=================================================================
	Main
================================================================="""

symbols = ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "_", "?", "<", ">", "~"]

numbers = [str(n) for n in range(0,NUM_RANGE)]

wordlist = []

patternlist = []

outlist = []

#Add Capitailized version of each word:
for word in prelist:
	wordlist.append(word)
	wordlist.append(word.capitalize())

mapping = {
	'W':[w.encode() for w in wordlist],
	'S':[s.encode() for s in symbols],
	'N':[n.encode() for n in numbers]
}

def CalcTotalPasswords():
	pass
	n_len = len(numbers)
	s_len = len(symbols)
	w_len = len(wordlist)

	pattern_totals = []

	# W, N, S
	for pattern in patternlist:
		pattern_total = 0

		#Get total number of instance of each type in pattern
		counts = [0,0,0] 
		lens = [len(wordlist), len(numbers), len(symbols)]

		for char in pattern:
			if char == 'W':
				counts[0] += 1
			if char == 'N':
				counts[1] += 1
			if char == 'S':
				counts[2] += 1

		for index, count in enumerate(counts):
			if count == 0:
				continue
			if pattern_total == 0:
				pattern_total = lens[index]**count
			else:
				pattern_total = pattern_total*lens[index]**count

		#print(f"Counts: {counts} | lens: {lens} | Pattern Total: {pattern_total} | Pattern: {pattern}")
		pattern_totals.append(pattern_total)


	total_passwords = sum(pattern_totals)
	print(f"Generating {total_passwords:_} passwords...")
	print(f"Dictionary will be ~{round(total_passwords/80000000, 0)} GB")

def generate(pattern):
	try:
		pools = [mapping[c] for c in pattern]
	except KeyError as e:
		raise ValueError(f"Invalid pattern character: {e}")

	for combo in product(*pools):
		yield ''.join(combo)

def GenPatterns():
	limits = {
	 'W': WORDS,
	 'N': NUMBERS,
	 'S': SYMBOLS
	}

	chars = list(limits.keys())

	def backtrack(pattern, counts):
	    # yield any non-empty pattern
	    if pattern:
	        yield pattern

	    for c in chars:
	        if counts[c] < limits[c]:
	            counts[c] += 1
	            yield from backtrack(pattern + c, counts)
	            counts[c] -= 1

	# initialize counts
	counts = {c: 0 for c in limits}
	yield from backtrack("", counts)

def ProcessPatterns(precomputed_chunk, worker_id):
	buffer = []
	BATCH_SIZE = 100_000
	start_time = time.time()
	#Each worker has its own file
	file_name = f"{OUT_DIR}Dict_{worker_id}.txt"

	with open(file_name, 'ab') as f:
		for pattern, pools in precomputed_chunk:
			print(f"[Worker {worker_id}] : {pattern}")
			for combo in product(*pools):
				#f.write("".join(combo) + '\n')
				#buffer.append("".join(combo) + '\n')
				buffer.append(b''.join(combo) + b'\n')

				if len(buffer) >= BATCH_SIZE:
					f.write(b''.join(buffer))
					buffer.clear()

		#FLush remaining
		if buffer:
			f.write(b''.join(buffer))


	duration = time.time() - start_time
	print(f"Worker {worker_id} finished its patterns in {duration}")

def chunked(lst, n):
	for i in range(0,len(lst), n):
		yield lst[i:i+n]

if __name__ == "__main__":
	print("Deleting old dicts...")
	#Delete old dicts
	files = glob.glob(f"{OUT_DIR}dict*")
	for f in files:
		os.remove(f)

	print("Generating Patterns...")
	for p in GenPatterns():
		patternlist.append(p)
	print(f"Generated {len(patternlist)} patterns.")
	
	print("Precompiling Passwords...")
	precomputed_patterns = [(p, [mapping[c] for c in p]) for p in patternlist]
	print("Passwords Precompiled")

	CalcTotalPasswords()

	if input("Would you like to start? [Y/n] ").capitalize() != "Y":
		print("Exiting...")
		exit()

	num_workers = os.cpu_count()
	chunk_size = max(1, len(precomputed_patterns) // num_workers)
	chunks = list(chunked(precomputed_patterns, chunk_size))
	
	with ProcessPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for i, chunk in enumerate(chunks):
			futures.append(executor.submit(ProcessPatterns, chunk, i))

		#Wait for all to finish
		for f in futures:
			f.result()

	print("All workers finished!, merging files...")
	start_copy = time.time()

	files = sorted(glob.glob(f"{OUT_DIR}dict_*.txt"))

	with open(f"{OUT_DIR}dict", "wb") as f_out:
	    for file in files:
	        print(f"Copying from file: {file}")
	        with open(file, 'rb') as f_in:
	            while chunk := f_in.read(10_000_000):  # 10 MB at a time
	                f_out.write(chunk)

	end_copy = time.time()
	copy_time = end_copy - start_copy
	print(f"Copy took {copy_time}")
	#Delete Temp files
	for file in files:
		os.remove(file)


