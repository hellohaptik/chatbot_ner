from constant import dates_dict, times_dict, datetime_dict, numbers_dict, \
	TAG_PREV, TAG_NEXT, separators, HINDI_TAGGED_DATE, HINDI_TAGGED_TIME


class DateTimeTagger(object):
	"""
	Class to tag date and time in message using predefined dict of date, time and datetime references
	"""
	def __init__(self):
		self.is_time = False
		self.is_date = False

		self.date = []
		self.time = []

		self.cur_date = []
		self.cur_time = []
		self.ref_next = []
		self.ref_prev = []

	def _update(self, word, method=None):
		if method == TAG_PREV:
			ref_prev = " ".join(self.ref_prev)
			if self.is_date:
				self.cur_date.append(ref_prev)
			elif self.is_time:
				self.cur_time.append(ref_prev)
			self.ref_prev = []

		if word in dates_dict:
			if method == TAG_NEXT:
				ref_next = " ".join(self.ref_next)
				self.cur_date.append(ref_next)
				self.ref_next = []
			if self.is_time:
				self.is_time = False
				self.time.append(self.cur_time)
				self.cur_time = []
			self.cur_date.append(word)
			self.is_date = True

		elif word in times_dict:
			if method == TAG_NEXT:
				ref_next = " ".join(self.ref_next)
				self.cur_time.append(ref_next)
				self.ref_next = []
			if self.is_date:
				self.is_date = False
				self.date.append(self.cur_date)
				self.cur_date = []
			self.cur_time.append(word)
			self.is_time = True

		elif word in datetime_dict:
			if datetime_dict[word][0] == 1:
				self.ref_next.append(word)
			else:
				self.ref_prev.append(word)
		elif word in numbers_dict:
			if numbers_dict[word][1] == 1:
				self.ref_next.append(word)
			else:
				self.ref_prev.append(word)

	def get_date_time(self, message):
		words = message.strip().split()
		for index, word in enumerate(words):
			if word in separators:
				if self.is_time and self.cur_time:
					self.time.append(self.cur_time)
				if self.is_date and self.cur_date:
					self.date.append(self.cur_date)

				self.is_date = False
				self.cur_date = []
				self.is_time = False
				self.cur_time = []

			if not self.ref_next and not self.ref_prev:
				self._update(word)

			elif self.ref_prev:
				self._update(word, method=TAG_PREV)

			elif self.ref_next:
				self._update(word, method=TAG_NEXT)

			if index == len(words) - 1:
				if self.ref_next:
					ref_next = " ".join(self.ref_next)
					if self.is_date:
						self.cur_date.append(ref_next)
					elif self.is_time:
						self.cur_time.append(ref_next)
					self.ref_next = []
				if self.ref_prev:
					ref_prev = " ".join(self.ref_prev)
					if self.is_date:
						self.cur_date.append(ref_prev)
					elif self.is_time:
						self.cur_time.append(ref_prev)
					self.ref_prev = []
				if len(self.cur_date) != 0:
					self.date.append(self.cur_date)
				if len(self.cur_time) != 0:
					self.time.append(self.cur_time)

		return {HINDI_TAGGED_DATE: self.date, HINDI_TAGGED_TIME: self.time}


# d = DateTimeTagger()

# message = 'agle mangalvar'

# print d.get_date_time(message)
