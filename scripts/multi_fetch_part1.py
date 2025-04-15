import os, requests, json
from datetime import datetime

ACCOUNT_ASSIGNMENTS = [
    ("Nillioneco", "TWITTER_BEARER_1"),
    ("buildonnillion", "TWITTER_BEARER_2"),
    ("Pindora_HQ", "TWITTER_BEARER_3")
]

FORCE_OVERWRITE = True

def get_user_id(username, headers):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.json()['data']['id']

def fetch_latest_tweet(user_id, headers):
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        "max_results": 1,
        "tweet.fields": "created_at,referenced_tweets,in_reply_to_user_id"
    }
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    data = res.json().get("data", [])

    print(f"🔍 Inspecting tweets for user {user_id} ({len(data)} returned):")

    for i, tweet in enumerate(data):
        is_reply = tweet.get("in_reply_to_user_id") is not None
        is_retweet = any(ref["type"] == "retweeted" for ref in tweet.get("referenced_tweets", [])) if "referenced_tweets" in tweet else False

        print(f"\nTweet {i+1}:")
        print(f"🆔 ID: {tweet['id']}")
        print(f"📅 Date: {tweet['created_at']}")
        print(f"📜 Text: {tweet['text']}")
        print(f"↪️ Is Reply? {'✅' if is_reply else '❌'}")
        print(f"🔁 Is Retweet? {'✅' if is_retweet else '❌'}")

        if not is_reply and not is_retweet:
            return {
                "id": tweet["id"],
                "link": f"https://twitter.com/i/web/status/{tweet['id']}",
                "date": tweet["created_at"][:10].replace("-", "")
            }

    return None

def read_existing_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def main():
    today = datetime.utcnow().strftime("%Y%m%d")
    output_path = f"public/community_feed/twitter_{today}.json"
    os.makedirs("public/community_feed", exist_ok=True)

    existing_tweets = read_existing_json(output_path)
    tweet_ids = {t['id'] for t in existing_tweets}

    new_tweets = []

    for username, token_key in ACCOUNT_ASSIGNMENTS:
        token = os.getenv(token_key)
        headers = {"Authorization": f"Bearer {token}"}

        try:
            user_id = get_user_id(username, headers)
            tweet = fetch_latest_tweet(user_id, headers)

            if tweet:
                if FORCE_OVERWRITE or tweet["id"] not in tweet_ids:
                    new_tweets.append(tweet)
                    print(f"\n✅ {username} → tweet_{tweet['id']}")
                else:
                    print(f"\n🔁 {username} → tweet already present: {tweet['id']}")
            else:
                print(f"\n⚠️ No valid tweet found for {username}")
        except Exception as e:
            print(f"\n❌ Error for {username}: {e}")

    combined = existing_tweets + new_tweets
    with open(output_path, "w") as f:
        json.dump(combined, f, indent=2)

    print(f"\n📦 Appended {len(new_tweets)} new tweets → {output_path}")

if __name__ == "__main__":
    main()
