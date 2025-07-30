import copy

def remove_empty_fields(data_dict):
    for key, value in list(data_dict.items()):
        if isinstance(value, (list, dict, str)) and not value:
            del data_dict[key]
    return data_dict

def compress_full_data(full_data):
    compact_list = []
    last_data = {}
    
    for message in full_data:
        # Make a deep copy of the current message to modify it
        compact_message = copy.deepcopy(message)
        # For every key in the current message, remove it if its value is unchanged
        for key, value in message.items():
            if key in last_data and last_data[key] == value:
                compact_message.pop(key, None)
        # Remove any keys with empty values
        compact_message = remove_empty_fields(compact_message)
        compact_list.append(compact_message)
        # Update last_data to be the current full message
        last_data = message
    return compact_list
