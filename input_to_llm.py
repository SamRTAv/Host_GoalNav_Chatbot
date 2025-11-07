import json

# file_name = 'chat_history.jsonl'


def extract_chats(file_name):
    # Read the entire file into one string
    with open(file_name, 'r') as f:
        all_data_string = f.read()

    all_conversations = []
    decoder = json.JSONDecoder()
    position = 0

    # We must use a loop because the file contains
    # multiple JSON objects back-to-back.
    while position < len(all_data_string.strip()):
        # Skip any whitespace
        all_data_string = all_data_string[position:].lstrip()
        if not all_data_string:
            break # Reached end of file

        # Decode one object and find where it ends
        try:
            obj, position = decoder.raw_decode(all_data_string)
            all_conversations.append(obj)
        except json.JSONDecodeError:
            # Handle case where file might end with bad data
            break 

    # --- Now we can get the last three ---

    # Get the last three conversations
    last_three_convos = all_conversations[-3:]
    return last_three_convos

def extract_goalfocus(file_name):
       # Read the entire file into one string
    with open(file_name, 'r') as f:
        all_data_string = f.read()

    all_conversations = []
    decoder = json.JSONDecoder()
    position = 0

    # We must use a loop because the file contains
    # multiple JSON objects back-to-back.
    while position < len(all_data_string.strip()):
        # Skip any whitespace
        all_data_string = all_data_string[position:].lstrip()
        if not all_data_string:
            break # Reached end of file

        # Decode one object and find where it ends
        try:
            obj, position = decoder.raw_decode(all_data_string)
            all_conversations.append(obj)
        except json.JSONDecodeError:
            # Handle case where file might end with bad data
            break 

    # --- Now we can get the last three ---

    # Get the last three conversations
    last_three_convos = all_conversations[-1:]
    return last_three_convos


# print(last_three_convos)

# for i,convo in enumerate(last_three_convos):
#     print(convo)
    
# # Manually print them (as requested, no loop)
# print(f"Human: {last_three_convos[0][0]['human']}")
# print(f"AI: {last_three_convos[0][0]['ai']}")
# print("---")

# print(f"Human: {last_three_convos[1][0]['human']}")
# print(f"AI: {last_three_convos[1][0]['ai']}")
# print("---")

# print(f"Human: {last_three_convos[2][0]['human']}")
# print(f"AI: {last_three_convos[2][0]['ai']}")




