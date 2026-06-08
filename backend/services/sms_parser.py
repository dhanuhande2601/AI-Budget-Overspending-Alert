import re


AMOUNT_PATTERNS = [
    r'(?:INR|Rs\.?|₹)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)',
    r'([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*(?:INR|Rs\.?|₹)',
]

MERCHANT_PATTERNS = [
    r'\b(?:at|to|towards|for)\s+([A-Za-z0-9 .&_-]{2,60}?)(?:\s+on|\s+via|\s+using|\.|,|$)',
    r'\b(?:UPI|VPA)\s+([A-Za-z0-9 .@&_-]{2,60}?)(?:\s+on|\.|,|$)',
]

CATEGORY_KEYWORDS = [
    ('Food', ['swiggy', 'zomato', 'restaurant', 'cafe', 'food', 'pizza', 'hotel']),
    ('Transport', ['uber', 'ola', 'rapido', 'metro', 'fuel', 'petrol', 'diesel', 'parking']),
    ('Shopping', ['amazon', 'flipkart', 'myntra', 'shopping', 'store', 'mart', 'retail']),
    ('Bills', ['electricity', 'bill', 'recharge', 'broadband', 'wifi', 'mobile', 'postpaid']),
    ('Entertainment', ['movie', 'netflix', 'prime', 'spotify', 'bookmyshow', 'cinema']),
    ('Health', ['medical', 'pharmacy', 'hospital', 'clinic', 'medicine']),
]

PAYMENT_KEYWORDS = [
    ('UPI', ['upi', 'vpa', 'gpay', 'google pay', 'phonepe', 'paytm']),
    ('Card', ['card', 'debit card', 'credit card', 'pos']),
    ('Net Banking', ['netbanking', 'net banking', 'internet banking', 'imps', 'neft']),
    ('Wallet', ['wallet']),
]


def _clean_amount(value):
    return float(value.replace(',', ''))


def _first_match(patterns, text, flags=re.IGNORECASE):
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()

    return ''


def _detect_from_keywords(text, choices, default):
    lower_text = text.lower()

    for label, keywords in choices:
        if any(keyword in lower_text for keyword in keywords):
            return label

    return default


def parse_expense_sms(message):
    text = ' '.join((message or '').split())

    if not text:
        return {
            'is_expense': False,
            'error': 'SMS text is required'
        }

    lowered = text.lower()
    expense_words = ['debited', 'spent', 'paid', 'purchase', 'withdrawn', 'sent']

    if not any(word in lowered for word in expense_words):
        return {
            'is_expense': False,
            'error': 'This SMS does not look like an expense message'
        }

    amount_text = _first_match(AMOUNT_PATTERNS, text)

    if not amount_text:
        return {
            'is_expense': False,
            'error': 'Could not detect expense amount'
        }

    merchant = _first_match(MERCHANT_PATTERNS, text)
    title = merchant or 'SMS detected expense'
    category = _detect_from_keywords(text, CATEGORY_KEYWORDS, 'Other')
    payment_method = _detect_from_keywords(text, PAYMENT_KEYWORDS, 'SMS')

    return {
        'is_expense': True,
        'title': title[:200],
        'amount': _clean_amount(amount_text),
        'category': category,
        'payment_method': payment_method,
        'raw_sms': text,
    }
