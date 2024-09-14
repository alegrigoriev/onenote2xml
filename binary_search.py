# Searching the exact value
def Find(array, target, key=lambda k: k):
	bottom = 0
	top = len(array)

	# Do binary search. 'array' is sorted in ascending order
	while top != bottom:
		mid = (top + bottom) // 2
		# 'mid' always less than 'top'
		# 'mid' can be same as 'bottom'
		assert(mid < top)
		item = array[mid]
		item_value = key(item)

		if item_value == target:
			return item, mid
		elif item_value > target:
			top = mid
		elif bottom == mid:
			# We reached the end point
			break
		else:
			bottom = mid
		continue

	return None, None

# The lower bound of all items >= target
# which is the first item >= target.
def LowerBound(array, target, key=lambda k: k):
	bottom = 0
	top = len(array)
	top_item = None

	# Do binary search. 'array' is sorted in ascending order
	while top != bottom:
		mid = (top + bottom) // 2
		# 'mid' always less than 'top'
		# 'mid' can be same as 'bottom'
		assert(mid < top)
		item = array[mid]
		item_value = key(item)
		if item_value == target:
			return item, mid
		elif item_value > target:
			# target always less than top_item (if not None)
			top = mid
			top_item = item
		elif mid != bottom:
			# target always greater than bottom_item (if not None)
			bottom = mid
		else:
			break

		continue

	return top_item, top

# The upper bound of all items <= target
# which is the last item <= target.
# This is different from std::upper_bound, which returns the first item > target
def UpperBound(array, target, key=lambda k: k):
	bottom = -1
	top = len(array) -1

	# Do binary search. 'array' is sorted in ascending order
	bottom_item = None
	while top != bottom:
		mid = (top + bottom + 1) // 2
		# 'mid' always greater than 'bottom'
		# 'mid' can be same as 'top'
		assert(mid > bottom)
		item = array[mid]
		item_value = key(item)
		if item_value == target:
			return item, mid
		elif item_value < target:
			# target always greater than bottom_item (if not None)
			bottom = mid
			bottom_item = item
		elif mid != top:
			# top (and top_item) is always greater than target

			# target always greater than bottom_item (if not None)
			top = mid
		else:
			# We reached the end point
			break

		continue

	return bottom_item, bottom

def Test():
	import random
	# 1. make a random array of 200 elements
	for i in range(10000):
		size = random.randint(1, 100)
		array = random.sample(range(10,200), size)
		array.sort()
		target = random.randint(0, 210)

		exact, pos = Find(array, target)
		if pos is None:
			assert(target not in array)
		else:
			assert(exact == target)
			assert(array[pos] == exact)

		lower_bound, pos = LowerBound(array, target)
		if pos == len(array):
			assert(target not in array)
			assert(array[-1] < target)
			assert(lower_bound is None)
		else:
			assert(array[pos] == lower_bound)
			assert(lower_bound >= target)

		upper_bound, pos = UpperBound(array, target)
		if pos < 0:
			assert(array[0] > target)
			assert(upper_bound is None)
		else:
			assert(array[pos] <= target)
			assert(array[pos] == upper_bound)
			assert(pos +1 == len(array) or array[pos+1] > target)
		continue
	return
