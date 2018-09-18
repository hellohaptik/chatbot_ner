from constant import dates_dict, times_dict, datetime_dict, numbers_dict, \
    TAG_PREV, TAG_NEXT, separators, HINDI_TAGGED_DATE, HINDI_TAGGED_TIME


class HindiDateTimeTagger(object):
    """
    Class to tag date and time in message using predefined dict of date, time and datetime.
    """

    def __init__(self):
        """
        Initialise class parameters

        is_time (bool): to decide whether to append current word in time list or not
        is_date (bool): to decide whether to append current word in date list or not

        date (list): store list of tagged date
        time (list): store list of tagged time

        original_text_date (list): store list of original text for tagged date in date
        original_text_time (list): store list of original text for tagged time in time

        cur_date (list) : store list of tagged words for current processing date
        cur_time (list) : store list of tagged words for current processing time

        original_text_cur_date (list): store list of all words for current processing date
        original_text_cur_time (list): store list of all words for current processing time

        ref_next (list): list to store tagged words like numeric, numeral and words which corresponds to both
                         date and time and will be added whichever entity date and time comes next.

        ref_prev (list): list to store tagged words like numeric, numeral and words which corresponds to both
                         date and time and will be added whichever entity date and time comes before this.


        original_text_ref_next (list): list to store all words including numeric, numeral and words which corresponds
                                       to both date and time and will be added whichever entity date and time comes
                                       next.

        original_text_ref_prev (list): list to store all words including numeric, numeral and words which corresponds
                                       to both date and time and will be added whichever entity date and time comes
                                       before this.

        last_active_entity (int): to find which of entity (date or time) is active at current word

        """
        self.is_time = False
        self.is_date = False

        self.date = []
        self.time = []

        self.original_text_date = []
        self.original_text_time = []

        self.cur_date = []
        self.cur_time = []

        self.original_text_cur_date = []
        self.original_text_cur_time = []

        self.ref_next = []
        self.ref_prev = []

        self.original_text_ref_next = []
        self.original_text_ref_prev = []

        self.last_active_entity = None

    def _update(self, word, method=None):
        """
        Method to update current date and current time list for given word and method like adding to next entity
        or to prev entity.
        Args:
            word (str): word to be added to entity
            method (str): method 'next' or 'prev' to decide where to add this word for active entity
        Returns:
            None
        """
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
                self.last_active_entity = 1
            else:
                self.ref_prev.append(word)
                self.last_active_entity = 2

        elif word in numbers_dict:
            if numbers_dict[word][1] == 1:
                self.ref_next.append(word)
                self.last_active_entity = 1
            else:
                self.ref_prev.append(word)
                self.last_active_entity = 2

    @staticmethod
    def _last_index_in_list(word_list, word):
        """
        Method which will return the last index where the word is found in list
        Args:
            word_list (list): list of words
            word (str): word whose last index has to be find
        Returns:
            (int): last index of word in word_list
        """
        return max(loc for loc, val in enumerate(word_list) if val == word)

    def preprocess_original_text(self, tagged_text_list, original_text_list):
        """
        Method to remove extra words from original text for given entity which do not required to be included

        Args:
            tagged_text_list (list): list of tagged text for entity
            original_text_list (list): list of original text for entity

        Returns:
            preprocessed_original_text_list(list): list of preprocessed original text

        Examples:
              >> text = 'hey tum agle mahine ki 2 tarikh ko aa jana'
              >> tagged_text_list = ['agle mahine 2 tarikh']
              >> original_text_list = ['agle mahine ki 2 tarikh ko aa jana']

              >> preprocess_original_text(tagged_text_list, original_text_list)
              >> ['agle mahine ki 2 tarikh']

        """
        preprocessed_original_text_list = []
        for tag_text, original_text in zip(tagged_text_list, original_text_list):
            first_word_tag_text = tag_text.split()[0]
            last_word_tag_text = tag_text.split()[-1]
            first_word_index_original_text = original_text.split().index(first_word_tag_text)
            last_word_index_original_text = self._last_index_in_list(original_text.split(), last_word_tag_text)
            original_text = " ".join(original_text.split()[first_word_index_original_text:
                                                           last_word_index_original_text + 1])
            preprocessed_original_text_list.append(original_text)
        return preprocessed_original_text_list

    def _update_original_text(self, word, is_date, is_time, method=None):
        """
        Method to update all words in original_text_current date and original_text_current time list for given word
        and method depending on current active entity
        Args:
            word (str): word to be added to entity
            is_date (bool): true is current active entity is date else false
            is_time (bool): true is current active entity is time else false
            method (str): method 'next' or 'prev' to decide where to add this word for active entity
        Returns:
            None
        """
        if method == TAG_PREV:
            original_text_ref_prev = " ".join(self.original_text_ref_prev)
            if is_date:
                self.original_text_cur_date.append(original_text_ref_prev)
            elif is_time:
                self.original_text_cur_time.append(original_text_ref_prev)
            self.original_text_ref_prev = []

        if word in dates_dict:
            if method == TAG_NEXT:
                original_text_ref_next = " ".join(self.original_text_ref_next)
                self.original_text_cur_date.append(original_text_ref_next)
                self.original_text_ref_next = []
            if is_time:
                self.original_text_time.append(self.original_text_cur_time)
                self.original_text_cur_time = []
            self.original_text_cur_date.append(word)

        elif word in times_dict:
            if method == TAG_NEXT:
                original_text_ref_next = " ".join(self.original_text_ref_next)
                self.original_text_cur_time.append(original_text_ref_next)
                self.original_text_ref_next = []
            if is_date:
                self.original_text_date.append(self.original_text_cur_date)
                self.original_text_cur_date = []
            self.original_text_cur_time.append(word)

        elif word in datetime_dict:
            if datetime_dict[word][0] == 1:
                self.original_text_ref_next.append(word)
            else:
                self.original_text_ref_prev.append(word)

        elif word in numbers_dict:
            if numbers_dict[word][1] == 1:
                self.original_text_ref_next.append(word)
            else:
                self.original_text_ref_prev.append(word)

        else:
            if is_date:
                self.original_text_cur_date.append(word)
            elif is_time:
                self.original_text_cur_time.append(word)
            else:
                if self.last_active_entity == 1:
                    self.original_text_ref_next.append(word)
                elif self.last_active_entity == 2:
                    self.original_text_ref_prev.append(word)

    def get_datetime_tag_text(self, message):
        """
        Method to get date and time text detected from message
        Args:
            message (str): message
        Returns:
            (dict):
                HINDI_TAGGED_DATE (list): list containing list of tagged text and list of original text for date
                HINDI_TAGGED_TIME (list): list containing list of tagged text and list of original text for time
        """
        words = message.strip().split()
        for index, word in enumerate(words):
            if word in separators:
                if self.is_time and self.cur_time:
                    self.time.append(self.cur_time)
                    self.original_text_time.append(self.original_text_cur_time)
                if self.is_date and self.cur_date:
                    self.date.append(self.cur_date)
                    self.original_text_date.append(self.original_text_cur_date)

                self.is_date = False
                self.cur_date = []
                self.original_text_cur_date = []
                self.is_time = False
                self.cur_time = []
                self.original_text_cur_time = []

            is_date, is_time = self.is_date, self.is_time
            if not self.ref_next and not self.ref_prev:
                self._update(word)
                self._update_original_text(word, is_date, is_time)

            elif self.ref_prev:
                self._update(word, method=TAG_PREV)
                self._update_original_text(word, is_date, is_time, method=TAG_PREV)

            elif self.ref_next:
                self._update(word, method=TAG_NEXT)
                self._update_original_text(word, is_date, is_time, method=TAG_NEXT)

            if index == len(words) - 1:
                if self.ref_next:
                    ref_next = " ".join(self.ref_next)
                    original_text_ref_next = " ".join(self.original_text_ref_next)
                    if self.is_date:
                        self.cur_date.append(ref_next)
                        self.original_text_cur_date.append(original_text_ref_next)
                    elif self.is_time:
                        self.cur_time.append(ref_next)
                        self.original_text_cur_time.append(original_text_ref_next)

                if self.ref_prev:
                    ref_prev = " ".join(self.ref_prev)
                    original_text_ref_prev = " ".join(self.original_text_ref_prev)
                    if self.is_date:
                        self.cur_date.append(ref_prev)
                        self.original_text_cur_date.append(original_text_ref_prev)
                    elif self.is_time:
                        self.cur_time.append(ref_prev)
                        self.original_text_cur_time.append(original_text_ref_prev)

                if len(self.cur_date) != 0:
                    self.date.append(self.cur_date)
                    self.original_text_date.append(self.original_text_cur_date)

                if len(self.cur_time) != 0:
                    self.time.append(self.cur_time)
                    self.original_text_time.append(self.original_text_cur_time)

        self.date = [" ".join(x) for x in self.date]
        self.time = [" ".join(x) for x in self.time]

        self.original_text_date = [" ".join(x) for x in self.original_text_date]
        self.original_text_time = [" ".join(x) for x in self.original_text_time]

        self.original_text_date = self.preprocess_original_text(self.date, self.original_text_date)
        self.original_text_time = self.preprocess_original_text(self.time, self.original_text_time)

        return {HINDI_TAGGED_DATE: [self.date, self.original_text_date],
                HINDI_TAGGED_TIME: [self.time, self.original_text_time]}
