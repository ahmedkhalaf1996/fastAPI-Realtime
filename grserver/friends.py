# friends.py in grserver directory
from typing import List

async def get_user_friends(user_id: str) -> List[str]:
    friends_map = {
        "1": ["2", "3", "4", "5"],
        "2": ["1", "3", "4", "5"],
        "3": ["1", "2"],
        "4": ["1", "2", "5"],
        "5": ["1", "2", "3", "4"]
    }

    return friends_map.get(user_id, [])
