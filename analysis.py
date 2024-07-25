import re
import json
import pandas as pd
from titlecase import titlecase
pd.options.mode.chained_assignment = None

def format_number(n):
    """Format number to show two decimal places if it has a decimal part, otherwise show as an integer."""
    if n % 1 == 0:
        return f"{n:.0f}"
    else:
        return f"{n:.2f}"

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
    
    # capitalize the first letter of each word
    df_in['Description'] = df_in['Description'].apply(titlecase)

    # apply regex functions
    df_in['Description'] = df_in['Description'].apply(strip_patterns)
    df_in['Description'] = df_in['Description'].apply(remove_characters)

    # strip the aftermath
    df_in['Description'] = df_in['Description'].str.strip()

    return df_in

def get_spend_by_category(df):
    total_spent = df['Amount'].sum()
    category_spent = df.groupby('Category')['Amount'].sum()

    # Calculate the percentage of total money spent for each category
    category_percentage = ((category_spent / total_spent) * 100).round(0).astype(int)
    category_percentage.sort_values(ascending=False, inplace=True)

    top_categories = category_percentage.reset_index().values.tolist()
    
    # only keep the top 4 categories and then combine the rest into "Other"
    if len(top_categories) > 4:
        other_percentage = sum(category_percentage[4:])
        top_categories = top_categories[:4]
        top_categories.append(['Other', other_percentage])
        
    return top_categories

def get_day_spent_data(df):
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='%m/%d/%Y')
    day_spent = df.groupby(df['Transaction Date'].dt.day_name())['Amount'].sum()
    
    # Sort day_spent by the day of the week starting on Monday
    day_spent = day_spent.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    day_spent = day_spent.round(2)
    day_spent_list = [{'day': key, 'amount': value} for key, value in day_spent.items()]
    
    return day_spent_list

def get_date_with_most_spent(df):
    date_spent = df.groupby('Transaction Date')['Amount'].sum()
    date_with_most_spent = date_spent.idxmax()
    amount_spent = date_spent[date_with_most_spent]
    
    date_with_most_spent = date_with_most_spent.strftime('%B %d, %Y')
    return [date_with_most_spent, f"${format_number(amount_spent)}"]

def get_top_spend_places(df):
    top_description = df.groupby('Description')['Amount'].sum().nlargest(5).reset_index().values.tolist()
    for i in range(len(top_description)):
        top_description[i][1] = f"${format_number(top_description[i][1])}"
        
    return top_description

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
    
    # 0. Intro screen
    first_date = pd.to_datetime(df['Transaction Date']).min().strftime('%B %d, %Y')
    last_date = pd.to_datetime(df['Transaction Date']).max().strftime('%B %d, %Y')
    res["intro"] = f"Here's how you spent from {first_date} to {last_date}."

    # 1. Top Spend categories by percentage money spent
    res['top_categories'] = get_spend_by_category(df)
    
    # 2. Days of the week spent the most
    res["days_of_week_spend"] = get_day_spent_data(df)

    # 3. Number of different places spent 
    res["num_places_spent"] = df["Description"].nunique()

    # 4. Top 5 Places visited by frequency
    res["top_freq_places"] = df["Description"].value_counts()[:5].reset_index().values.tolist()

    # 5. Day spent the most and corresponding amount
    res["top_date_and_amt"] = get_date_with_most_spent(df)

    # 6. Top 5 places visited by money spent
    res["top_spend_places"] = get_top_spend_places(df)
    
    return res


if __name__ == '__main__':
    df = pd.read_csv('sample_data.csv')
    res = get_analysis(df)
    
    print(json.dumps(res, indent=4))
