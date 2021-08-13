# importing libraries and packages
import pandas as pd
from cleantext import clean
import snscrape.modules.twitter as sntwitter
import itertools
from tqdm import tqdm


def text_preprocessing(text):

    preprocessed_text = clean(text,
        fix_unicode=True,               # fix various unicode errors
        to_ascii=True,                  # transliterate to closest ASCII representation
        lower=True,                     # lowercase text
        no_punct=True,                 # remove punctuations
        replace_with_punct="",          # instead of removing punctuations you may replace them
    )

    return preprocessed_text



def get_relevant_user_tweets(username, since, until, min_likes, tweet_limit):

    """
    This will extract all the tweets which is not a reply or a quoted tweet. It also skips all the tweets having a media content and 
    searches for only those tweets having more than the min_likes specified in the argument. Tweet limit can be specified to extract limited
    tweets for faster processing.
    username: [str]
    since: [str]
    until: [str]
    min_likes: [int]
    limit: [int]
    output: [DataFrame]

    """
    
    # Creating list to append tweet data     
    tweets_list1 = []

    # Using TwitterSearchScraper to scrape data and append tweets to list
    for tweet in sntwitter.TwitterSearchScraper(f'from:{username} since:{since} until:{until}').get_items(): #declare a username 
        if (tweet.inReplyToTweetId is None) & (tweet.likeCount > min_likes) & (tweet.media is None) & (tweet.quotedTweet is None):
            print(len(tweets_list1), end=', ')
            if len(tweets_list1) >= tweet_limit:
                break   
            tweets_list1.append([tweet.url, tweet.date, tweet.content, tweet.user.username]) #declare the attributes to be returned
    
    tweets_df = pd.DataFrame(tweets_list1, columns=['org_url', 'Datetime', 'Text', 'Username'])

    return tweets_df



def get_similar_tweets(df, tweet_date):

    """
    This will try to find a similar tweet with respect to the user's tweet from the entire twitter database. 
    To reduce time, this will only extract one similar tweet found before the user's tweet date.
    df: [DataFrame]
    tweet_date: [list]
    Output: [DataFrame]

    """
    
    user_url = []
    copied_url = []
    user_tweet = []
    copied_tweet = []
    user_tweet_date = []
    copied_tweet_date = []
    # Creating list to append tweet data to

    for j, k, l, m in tqdm(zip(list(df['Text']), tweet_date, list(df['org_url']), list(df['processed_body'])), total=len(tweet_date)):
        
        try:
            scraped_tweets = sntwitter.TwitterSearchScraper(f"{m} since:2007-01-01 until:{k}").get_items()
            sliced_scraped_tweets = itertools.islice(scraped_tweets, 1)
            tweets_df3 = pd.DataFrame(sliced_scraped_tweets)
            if len(tweets_df3) > 0:
                tweets_df3 = tweets_df3[['url', 'date', 'content']]
                copied_url.append(tweets_df3['url'][tweets_df3.shape[0] - 1])
                user_tweet.append(j)
                user_url.append(l)
                user_tweet_date.append(k)
                copied_tweet_date.append(tweets_df3['date'][tweets_df3.shape[0] - 1])
                copied_tweet.append(tweets_df3['content'][tweets_df3.shape[0] - 1])

        except:
            continue                
            
    copied_df = pd.DataFrame({'user_url': user_url, 'user_tweet_date': user_tweet_date, 'user_tweet': user_tweet, 'copied_url': copied_url, 'copied_tweet_date': copied_tweet_date, 'copied_tweet': copied_tweet})
    copied_df['user_tweet_date'] = pd.to_datetime(copied_df['user_tweet_date']).dt.date
    copied_df['copied_tweet_date'] = pd.to_datetime(copied_df['copied_tweet_date']).dt.date
    return copied_df




def find_copied_tweets(username, since='2021-01-01', until='2021-08-01', min_likes = 0, tweet_limit = 500):

    """
    This will extract the most recent copied tweet from twitter's database.
    username: [str]
    since: [str]
    until: [str]
    Output: [DataFrame]
    """

    print("\n\n--Getting user's tweets--")

    tweets_df1 = get_relevant_user_tweets(username, since, until, min_likes, tweet_limit)

    tweets_df1['processed_body'] = tweets_df1['Text'].apply(lambda x: text_preprocessing(x))
    tweets_df1['processed_body'] = tweets_df1['processed_body'].str.replace(r"\n", " ", regex = True)

    a = list(tweets_df1['Datetime'].dt.date)
    all_date = [str(i) for i in a]

    print("\n\n--Finding Similar Tweets--")
    copied_df_1 = get_similar_tweets(tweets_df1, all_date)
    

    return copied_df_1

print("-- Enter Username --")

username = input()

if username.startswith('@'):
    username = username[1:]

print("\n\n-- Enter From Date (yyyy-mm-dd) --")

since = input()

print("\n\n-- Enter to Date (yyyy-mm-dd) --")

until = input()

print("\n\n-- Enter minimum likes --")

min_likes = int(input())

print("\n\n-- Enter Tweet Limit --")
tweet_limit = int(input())


copied_df_1 = find_copied_tweets(f'{username}', since, until, min_likes, tweet_limit)

copied_df_1.to_excel(f"{username}_copied_tweets.xlsx", index = False)