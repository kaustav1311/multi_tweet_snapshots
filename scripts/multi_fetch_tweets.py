import os, requests, json
from datetime import datetime

# List of all 9 accounts (add more later)
ACCOUNTS = [
    "Nillioneco",
    "buildonnillion",
    "Pindora_HQ",
    "soar_chain",
    "HealthBlocks",
    "SkillfulAI",
    "FulcraDynamics",
    "MonadicDNA",
    "StadiumScience_"
]

# Rotate 3 keys for every 3 accounts
BEARER_KEYS = [
    os.getenv("TWITTER_BEARER_1"),
    os.getenv("TWITTER_BEARER_2"),
    os.getenv("TWITTER_BEARER_3")
]

headers_list = [
    {"Authorization": f"Bearer {token}"} for token in BEARER_KEYS
]

def get_user_id(username, headers):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.json()['data']['id']

def fetch_latest_tweet(user_id, headers):
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        "max_results": 10,
        "tweet.fields": "created_at,referenced_tweets,in_reply_to_user_id",
    }
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    data = res.json().get("data", [])

    # Find first valid tweet (no reply, no retweet)
    for tweet in data:
        is_reply = tweet.get("in_reply_to_user_id") is not None
        is_retweet = any(ref["type"] == "retweeted" for ref in tweet.get("referenced_tweets", [])) if "referenced_tweets" in tweet else False
        if not is_reply and not is_retweet:
            return {
                "id": tweet["id"],
                "link": f"https://twitter.com/i/web/status/{tweet['id']}",
                "date": tweet["created_at"][:10].replace("-", "")  # YYYYMMDD
            }
    return None

def main():
    today = datetime.utcnow().strftime("%Y%m%d")
    output_path = f"public/community_feed/twitter_{today}.json"
    os.makedirs("public/community_feed", exist_ok=True)

    tweets = []

    for i, username in enumerate(ACCOUNTS):
        if "placeholder" in username:
            continue

        key_index = i // 3  # Use key 0 for 0–2, key 1 for 3–5, etc.
        headers = headers_list[key_index]

        try:
            user_id = get_user_id(username, headers)
            tweet = fetch_latest_tweet(user_id, headers)
            if tweet:
                tweets.append(tweet)
                print(f"✅ {username} → tweet_{tweet['id']}")
            else:
                print(f"⚠️ {username} has no valid tweet")
        except Exception as e:
            print(f"❌ Error fetching from {username}: {str(e)}")

    # Save combined JSON
    with open(output_path, "w") as f:
        json.dump(tweets, f, indent=2)
    print(f"📦 Saved {len(tweets)} tweets → {output_path}")

if __name__ == "__main__":
    main()

