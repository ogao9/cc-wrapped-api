import re
import pandas as pd

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
    TARGET 00034157091 ANN ARBOR MI -> TARGET
    7-ELEVEN 34621 ANN ARBOR MI -> 7-ELEVEN
    '''
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
    df_in.rename(columns={'Trans. Date': 'Transaction Date'}, inplace=True)

    # Take out payments
    df_in = df_in[df_in['Category'] != 'Payments and Credits']

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


def get_analysis(df):
    '''
    Data format returned:
    {
        "top_categories": object,
        "days_of_week_spend": array[7 objects],
        "num_places_spent": int,
        "top_freq_places": object,
        "top_date_and_amt": array[2],
        "top_spend_places": object
    }
    '''
    df = clean_df(df)
    res = {}

    # 1. Top Spend categories by percentage money spent
    total_spent = df['Amount'].sum()
    category_spent = df.groupby('Category')['Amount'].sum()

    # Calculate the percentage of total money spent for each category
    category_percentage = (category_spent / total_spent) * 100

    top_categories = category_percentage.sort_values(ascending=False).reset_index().values.tolist()
    res['top_categories'] = top_categories
    
    # 2. Days of the week spent the most
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='%m/%d/%Y')
    day_spent = df.groupby(df['Transaction Date'].dt.day_name())['Amount'].sum()
    
    # Sort day_spent by the day of the week starting on Monday
    day_spent = day_spent.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    day_spent = day_spent.round(2)
    day_spent_list = [{'day': key, 'amount': value} for key, value in day_spent.items()]
    
    res["days_of_week_spend"] = day_spent_list

    # 3. Number of different places spent 
    res["num_places_spent"] = df["Description"].nunique()

    # 4. Top 5 Places visited by frequency
    res["top_freq_places"] = df["Description"].value_counts()[:5].reset_index().values.tolist()

    # 5. Day spent the most and corresponding amount
    date_spent = df.groupby('Transaction Date')['Amount'].sum()
    date_with_most_spent = date_spent.idxmax()
    amount_spent = date_spent[date_with_most_spent]
    
    res["top_date_and_amt"] = [date_with_most_spent, amount_spent]

    # 6. Top 5 places visited by money spent
    top_description = df.groupby('Description')['Amount'].sum().nlargest(5).reset_index().values.tolist()
    res["top_spend_places"] = top_description
    
    return res
