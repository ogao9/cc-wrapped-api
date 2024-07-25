import re

def strip_patterns(string):
    '''
    Removes the following patterns from string
    pattern1: TST*_, SNACK*_
    pattern2: SQ_*
    '''
    pattern1 = r'^\w+\*\s'
    pattern2 = r'^\w+\s\*'
    stripped1 = re.sub(pattern1, '', string)
    stripped_string = re.sub(pattern2, '', stripped1)
    return stripped_string

def remove_characters(string):
    '''
    Removes all characters that come after the first non-alphabetical character that comes after the first space
    Ex:
    TARGET 00034157091 ANN ARBOR MI -> TARGET
    7-ELEVEN 34621 ANN ARBOR MI -> 7-ELEVEN
    '''
    # Find the index of the first space
    first_space_index = string.find(' ')
    
    # Find the index of the first non-alphabetical character after the first space
    match = re.search(r'[^a-zA-Z\s]', string[first_space_index:])
    non_alpha_index = match.start() if match else len(string) - first_space_index

    # Remove characters after the first non-alphabetical character
    cleaned_string = string[:first_space_index + non_alpha_index] if first_space_index != -1 else string
    
    return cleaned_string

def clean_df(df_in):
    """
    The big boy cleaning function
    """
    # rename columns
    df_in.rename(columns={'Trans. Date': 'Transaction Date'}, inplace=True)

    # take out payments
    df_in = df_in[df_in['Category'] != 'Payments and Credits']

    # convert column to numeric
    df_in['Amount'] = df_in['Amount'].astype(float)

    # remove leading and trailing whitespaces and punctiation
    df_in['Description'] = df_in['Description'].str.strip()  
    df_in['Description'] = df_in['Description'].str.replace(r'[^\w\s]', '')

    # remove everything that comes after a new line (ex: GOOGLE PAY)
    df_in['Description'] = df_in['Description'].str.split('\n').str[0]

    # apply regex functions
    df_in['Description'] = df_in['Description'].apply(strip_patterns)
    df_in['Description'] = df_in['Description'].apply(remove_characters)

    # strip the aftermath
    df_in['Description'] = df_in['Description'].str.strip()

    return df_in


# ---------- Tests -------------
def test_strip_patterns():
    # Test case 1: string with no pattern at the beginning
    string = "Hello, World!"
    expected_output = "Hello, World!"
    assert strip_patterns(string) == expected_output

    # Test case 2: string with a word followed by an asterisk at the beginning
    string = "apple* banana"
    expected_output = " banana"
    assert strip_patterns(string) == expected_output

    # Test case 3: string with multiple words and an asterisk at the beginning
    string = "apple* banana cherry"
    expected_output = " banana cherry"
    assert strip_patterns(string) == expected_output

    # Test case 4: string with only an asterisk at the beginning
    string = "*"
    expected_output = "*"
    assert strip_patterns(string) == expected_output

    # Test case 5: string with multiple words and no pattern at the beginning
    string = "This is a test"
    expected_output = "This is a test"
    assert strip_patterns(string) == expected_output

    print("All test cases pass")


def test_remove_characters():
    # Test case 1: String with no spaces
    string = "HelloWorld"
    expected_output = "HelloWorld"
    assert remove_characters(string) == expected_output

    # Test case 2: String with a space and non-alphabetical characters after the space
    string = "Hello World! How are you?"
    expected_output = "Hello World"
    print("actual output: ", remove_characters(string))
    assert remove_characters(string) == expected_output

    # Test case 3: String with a space but no non-alphabetical characters after the space
    string = "Hello World"
    expected_output = "Hello World"
    assert remove_characters(string) == expected_output

    # Test case 4: Empty string
    string = ""
    expected_output = ""
    assert remove_characters(string) == expected_output

    # Test case 5: String with only non-alphabetical characters
    string = "!@#$%^&*()"
    expected_output = "!@#$%^&*()"
    assert remove_characters(string) == expected_output

    print("All test cases pass")
