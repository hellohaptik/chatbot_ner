from __future__ import absolute_import
import models.crf.constant as model_constant


def generate_city_output(crf_data):
    """
    This function takes a list of crf output as input and returns a json with proper tags of the entity

    for Example:
        bot_message = 'none'
        user_message = 'flights for delhi to goa'

        Then run_crf will give the following output:
            crf_data = [['none','O'], ['flights', 'O'], ['from', 'O'], ['delhi', 'FROM-B'], ['to', 'O'],
            ['goa', 'TO-B']]

        Calling generate_city_output with crf_output_list will extract required text and return a json in the
        following form:
            [[{'city': 'delhi', 'via': False, 'from': True, 'to': False, 'normal': False}], 
                                        [{'city': 'goa', 'via': False, 'from': False, 'to': True, 'normal': False}]]

    This functions iterates over the list and calls the check_label which will return a json list of tagged words.

    """
    list_json = []
    read_line = 0
    while read_line < (len(crf_data)):
        if crf_data[read_line][1] == model_constant.CITY_O:
            pass
        else:
            temp_list = check_label(reader_list=crf_data, reader_pointer=read_line,
                                    begin_label=model_constant.CITY_FROM_B, inner_label=model_constant.CITY_FROM_I,
                                    from_bool=True, to_bool=False, via_bool=False, normal_bool=False)
            if temp_list:
                list_json.append(temp_list)

            else:
                temp_list = check_label(reader_list=crf_data, reader_pointer=read_line,
                                        begin_label=model_constant.CITY_TO_B, inner_label=model_constant.CITY_TO_I,
                                        from_bool=False, to_bool=True, via_bool=False, normal_bool=False)
                if temp_list:
                    list_json.append(temp_list)

                else:
                    temp_list = check_label(reader_list=crf_data, reader_pointer=read_line,
                                            begin_label=model_constant.CITY_VIA_B,
                                            inner_label=model_constant.CITY_VIA_I, from_bool=False, to_bool=False,
                                            via_bool=True, normal_bool=False)
                    if temp_list:
                        list_json.append(temp_list)

                    else:
                        temp_list = check_label(reader_list=crf_data, reader_pointer=read_line,
                                                begin_label=model_constant.CITY_NORMAL_B,
                                                inner_label=model_constant.CITY_NORMAL_I, from_bool=False,
                                                to_bool=False, via_bool=False, normal_bool=True)

                        if temp_list:
                            list_json.append(temp_list)
        read_line += 1
    return list_json


def make_json(city_value, from_bool, to_bool, via_bool, normal_bool):
    """
    This function return json of the value found in function check_label

    for Example:
        Args:
            city_value = 'delhi'
            from_bool = True
            to_bool = False
            via_bool = False
            normal_bool = False

        then calling this function with ab ove parameters will give:
            {'city': 'delhi', 'via': False, 'from': True, 'to': False, 'normal': False}
    """
    python_dict = {
        model_constant.MODEL_CITY_VALUE: city_value,
        model_constant.MODEL_CITY_FROM: from_bool,
        model_constant.MODEL_CITY_TO: to_bool,
        model_constant.MODEL_CITY_VIA: via_bool,
        model_constant.MODEL_CITY_NORMAL: normal_bool
    }
    return python_dict


def check_label(reader_list, reader_pointer, begin_label, inner_label, from_bool, to_bool, via_bool, normal_bool):
    """
    this function checks if a particular word has been given a particular label

    for Example:
        Args:
            reader_list = list returned by run_crf
            reader_pointer = 3
            begin_label = CITY_FROM_B
            inner_label = CITY_FROM_I
            from_bool = True
            to_bool = False
            via_bool = False
            normal_bool = False

        When check_label is called with above parameters, it checks if the word has been given CITY_FROM_B label
        and its following words
        have CITY_FROM_I label. I so it returns the proper json.
        For above inputs it will return
        [{'city': 'delhi', 'via': False, 'from': True, 'to': False, 'normal': False}]
    """
    list_json = []
    if reader_list[reader_pointer][1].upper() == begin_label:
        entity_value = reader_list[reader_pointer][0]
        if reader_pointer == (len(reader_list) - 1):
            return make_json(city_value=entity_value, from_bool=from_bool, to_bool=to_bool, via_bool=via_bool,
                             normal_bool=normal_bool)
        else:
            check_pointer = reader_pointer + 1
            while check_pointer < (len(reader_list)):
                if reader_list[check_pointer][1].upper() != inner_label:
                    return make_json(city_value=entity_value, from_bool=from_bool, to_bool=to_bool, via_bool=via_bool,
                                     normal_bool=normal_bool)
                else:
                    entity_value = entity_value + ' ' + reader_list[check_pointer][0]
                    if check_pointer == (len(reader_list) - 1):
                        return make_json(city_value=entity_value, from_bool=from_bool, to_bool=to_bool,
                                         via_bool=via_bool, normal_bool=normal_bool)
                    check_pointer += 1
    return list_json
