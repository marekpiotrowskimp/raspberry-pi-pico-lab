import random

QUOTES = (
    ("Generous love, the glue that holds everything together in a healthy relationship, aims for shared happiness through the fulfillment of one's partner.", "Lama Ole Nydahl"),
    ("The understanding that truth is not neutral, but is instead blissful, is something only meditators and lovers trust.", "Lama Ole Nydahl"),
    ("Enlightenment is not only timeless but also more beautiful, truer, and more indestructible than anything separable or conditioned.", "Lama Ole Nydahl"),
    ("There is no greater happiness than the full development of mind!", "Lama Ole Nydahl"),
    ("If one understands that the only thing that remains timeless is the richness of one's own buddha nature, one can relax even with regard to death.", "Lama Ole Nydahl"),
    ("Just as what is in the jar, when broken, becomes one with the surroundings, death offers the opportunity to recognize the basic truth of all existence.", "Lama Ole Nydahl"),
    ("Like space, the essence of mind is unaffected by transition and death.", "Lama Ole Nydahl"),
    ("Buddha's advice helps beings by showing how one may consciously become a source of happiness and love.", "Lama Ole Nydahl"),
    ("A successful partnership thrives because of the willingness of both to place the well-being of the other above their own.", "Lama Ole Nydahl"),
    ("When the man makes the woman a queen and she treats him like a king, their noble style dissolves any limits for growth.", "Lama Ole Nydahl"),
    ("A generous relationship rarely knows dramas. One is happy when the partner is happy.", "Lama Ole Nydahl"),
    ("The taking love leads to feelings of attachment, jealousy and anger, while the giving love encompasses love, compassion and equanimity.", "Lama Ole Nydahl"),
    ("If we experience our power of awareness right here and now, then everything is free play and a gift.", "Lama Ole Nydahl"),
    ("Knowledge of inner processes in body and mind is as helpful for one's own preparation for death as it is for people who care for others who are dying.", "Lama Ole Nydahl"),
    ("The daily practice should include body, speech, and mind, so that the teachings slide from the head to the heart as fast as possible.", "Lama Ole Nydahl"),
    ("It is impossible to learn to meditate while dying. Therefore, it is a great help to become aware of the dreamlike state of all things during this life.", "Lama Ole Nydahl"),
    ("The essential art of dying consists of being easy-going and relaxed while at the same time staying mentally undistracted and one-pointed.", "Lama Ole Nydahl"),
    ("Around truly happy people it seems that the world is enriching itself and the good feelings that appear are more than what the lovers are contributing themselves.", "Lama Ole Nydahl"),
    ("The experiences of sharing love are much more honest and convincing than anything one could do for oneself.", "Lama Ole Nydahl"),
    ("If one is basically trusting, the Pure Land is near, and in death, perhaps one will enter something deeply known.", "Lama Ole Nydahl"),
    ("The highest truth is the highest joy, is the highest way of functioning.", "Lama Ole Nydahl"),
)

_last_quote_index = -1


def fetch_quote():
    """Return a random (text, author) tuple, never repeating the same quote twice in a row."""
    global _last_quote_index
    n = len(QUOTES)
    idx = random.randint(0, n - 2)
    if idx >= _last_quote_index:
        idx += 1
    _last_quote_index = idx
    return QUOTES[idx]
