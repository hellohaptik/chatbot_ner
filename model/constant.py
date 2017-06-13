import re
# which type of messages to keep
RES = [0,18,19,24]

# names of the columns to keep from chat data
KEEP_COLS = ["coll_id", "conv_no", "direction", "msg_type", "body"]

# pattern to remove emojis from chat data
EMOJI_PATTERN = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)

# name of json field for text inside message
TEXT = 'text'

# Direction of message
MESSAGE_DIRECTION = ["True", "False"]

# name of columns to keep while making conversations of coll_id, outbound, inbound from chats data
KEEP_CONV = ["coll_id", "outbound_msg", "inbound_msg"]

# name of columns in step4
STEP4_COLS = ["coll_id", "outbound_msg", "inbound_msg", "detected_city", "original_city", "arrival_city", "departure_city", "original_city_advance", "length_json"]
STEP7_COLS_arrival = ["coll_id", "outbound_msg", "inbound_msg", "detected_city", "original_city", "arrival_city","original_city_advance"]
STEP7_COLS_departure = ["coll_id", "outbound_msg", "inbound_msg", "detected_city", "original_city", "departure_city","original_city_advance"]
STEP7_COLS_arrival_departure = ["coll_id", "outbound_msg", "inbound_msg", "detected_city", "original_city", "arrival_city", "departure_city", "original_city_advance"]
# data column name in json
DATA = 'data'

# noise to be removed from text messages
NOISE_LIST = [".", "-", "--", "!", ".."]

# extra column after applying regex
REGEX_EDITED = ''