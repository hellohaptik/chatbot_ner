from __future__ import absolute_import
import models.crf.constant as model_constant


def generate_date_output(crf_data):
    """
    This function takes a list of crf output as input and returns a json with proper tags of the entity

    Attributes:
        crf_data : this this the output given from the crf model

    for Example:
        bot_message = 'none' # This marks the message sent by the bot 
        user_message = 'flights from 27th december and arriving on 31st january' # This marks the message sent by
                                                                                   the user

        Then run_crf will give the following output:
            crf_data = [['none','O'], ['flights', 'O'], ['from', 'O'], ['27th', 'FROM-B'], ['december', 'FROM-I'], 
            ['to', 'O'], ['31st', 'TO-B'], ['january', 'TO-I']]

        Calling generate_date_output with crf_output_list will extract required text and return a json in the
        following form:
            [[{'date': '27th', 'via': False, 'from': True, 'to': False, 'normal': False}], 
                                        [{'date': '27th', 'via': False, 'from': False, 'to': True, 'normal': False}]]

    This functions iterates over the list and calls the check_label which will return a json list of tagged words.

    """
    list_json = []
    read_line = 0
    while read_line < (len(crf_data)):
        if crf_data[read_line][1] == model_constant.DATE_O:
            pass
        else:
            temp_list = check_label(reader_list=crf_data, reader_pointer=read_line,
                                    begin_label=model_constant.DATE_FROM_B, inner_label=model_constant.DATE_FROM_I,
                                    from_bool=True, to_bool=False, start_bool=False, end_bool=False, normal_bool=False)
            if temp_list:
                list_json.append(temp_list)

            else:
                temp_list = check_label(reader_list=crf_data, reader_pointer=read_line,
                                        begin_label=model_constant.DATE_TO_B, inner_label=model_constant.DATE_TO_I,
                                        from_bool=False, to_bool=True, start_bool=False, end_bool=False,
                                        normal_bool=False)
                if temp_list:
                    list_json.append(temp_list)

                else:
                    temp_list = check_label(reader_list=crf_data, reader_pointer=read_line,
                                            begin_label=model_constant.DATE_START_B,
                                            inner_label=model_constant.DATE_START_I, from_bool=False, to_bool=False,
                                            start_bool=True, end_bool=False, normal_bool=False)
                    if temp_list:
                        list_json.append(temp_list)

                    else:
                        temp_list = check_label(reader_list=crf_data, reader_pointer=read_line,
                                                begin_label=model_constant.DATE_END_B,
                                                inner_label=model_constant.DATE_END_I, from_bool=False, to_bool=False,
                                                start_bool=False, end_bool=True, normal_bool=False)
                        if temp_list:
                            list_json.append(temp_list)

                        else:
                            temp_list = check_label(reader_list=crf_data, reader_pointer=read_line,
                                                    begin_label=model_constant.DATE_NORMAL_B,
                                                    inner_label=model_constant.DATE_NORMAL_I, from_bool=False,
                                                    to_bool=False, start_bool=False, end_bool=False, normal_bool=True)

                            if temp_list:
                                list_json.append(temp_list)
        read_line += 1
    return list_json


def make_json(date_value, from_bool, to_bool, start_bool, end_bool, normal_bool):
    """
    This function return json of the value found in function check_label
    
    Args:
            date_value : value of the date
            from_bool : Boolean value marking the from flag 
            to_bool : Boolean value marking the to flag
            start_bool : Boolean value marking the start_range flag
            end_bool : Boolean value marking the end_range flag
            normal_bool : Boolean value marking the normal flag

    for Example:
        date_value = '27th december'
        from_bool = True
        to_bool = False
        start_bool = False
        end_bool = False
        normal_bool = False

        then calling this function with ab ove parameters will give:
            {'date': ''27th december', 'via': False, 'from': True, 'to': False, 'normal': False}
    """
    python_dict = {
        model_constant.MODEL_DATE_VALUE: date_value,
        model_constant.MODEL_DATE_FROM: from_bool,
        model_constant.MODEL_DATE_TO: to_bool,
        model_constant.MODEL_START_DATE_RANGE: start_bool,
        model_constant.MODEL_END_DATE_RANGE: end_bool,
        model_constant.MODEL_DATE_NORMAL: normal_bool
    }
    return python_dict


def check_label(reader_list, reader_pointer, begin_label, inner_label, from_bool, to_bool, start_bool, end_bool,
                normal_bool):
    """
    this function checks if a particular word has been given a particular label

    Args:
            reader_list : list returned by run_crf
            reader_pointer : the pointer to keep track of the reader
            begin_label : Starting label
            inner_label : Inner label
            from_bool : Boolean value to mark the from flag
            to_bool : Boolean value to mark to flag
            start_bool : Boolean value to mark the start_range flag
            end_bool : Boolean value to mark the end_range flag
            normal_bool : Boolean value to mark the normal flag
    
    for Example:
        begin_label = DATE_FROM_B
        inner_label = DATE_FROM_I
        from_bool = True
        to_bool = False
        start_bool = False
        end_bool = False
        normal_bool = False

        When check_label is called with above parameters, it checks if the word has been given DATE_FROM_B label
        and its following words
        have DATE_FROM_I label. I so it returns the proper json.
        For above inputs it will return
        [{'date': ''27th december', 'via': False, 'from': True, 'to': False, 'normal': False}]
    """
    list_json = []
    if reader_list[reader_pointer][1].upper() == begin_label:
        entity_value = reader_list[reader_pointer][0]
        if reader_pointer == (len(reader_list) - 1):
            return make_json(date_value=entity_value, from_bool=from_bool, to_bool=to_bool, start_bool=start_bool,
                             end_bool=end_bool, normal_bool=normal_bool)
        else:
            check_pointer = reader_pointer + 1
            while check_pointer < (len(reader_list)):
                if reader_list[check_pointer][1].upper() != inner_label:
                    return make_json(date_value=entity_value, from_bool=from_bool, to_bool=to_bool,
                                     start_bool=start_bool, end_bool=end_bool, normal_bool=normal_bool)
                else:
                    entity_value = entity_value + ' ' + reader_list[check_pointer][0]
                    if check_pointer == (len(reader_list) - 1):
                        return make_json(date_value=entity_value, from_bool=from_bool, to_bool=to_bool,
                                         start_bool=start_bool, end_bool=end_bool, normal_bool=normal_bool)
                    check_pointer += 1
    return list_json
