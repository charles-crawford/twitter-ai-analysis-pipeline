CREATE TABLE tweets_sentiments_entities AS
SELECT tweets.id_str, tweets.created_at, tweets.text, tweets.location, tweets.user, 
tweets.day, tweets.month, tweets.year, tweets.followers_count, tweets.favorite_count, tweets.retweet_count, 
tweet_entities.value, tweet_entities.score, tweet_entities.entity,
tweet_sentiments.sentiment, tweet_sentiments.confidence, tweet_sentiments.positive, tweet_sentiments.negative, tweet_sentiments.neutral
FROM tweets LEFT JOIN tweet_entities ON tweets.id_str = tweet_entities.id_str
LEFT JOIN tweet_sentiments ON tweets.id_str = tweet_sentiments.id_str
WHERE tweets.location IS NOT NULL 
AND tweet_entities.value IS NOT NULL 
AND tweet_sentiments.sentiment IS NOT NULL