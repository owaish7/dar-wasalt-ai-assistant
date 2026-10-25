"""Small, explicit routing for common non-answer turns; no inference required."""
import re

SCOPE = {
    'en': 'I can help with Dar Global and Wasalt properties, projects and services covered by the sources. Please ask about one of those topics.',
    'ar': 'يمكنني مساعدتك في عقارات ومشاريع وخدمات دار جلوبال ووصلت التي تغطيها المصادر. تفضل بالسؤال عن أحد هذه المواضيع.',
}
CLARIFY = {
    'en': 'Which project or property do you mean? Please share its name and location, or a listing link.',
    'ar': 'أي مشروع أو عقار تقصد؟ يرجى ذكر اسمه وموقعه أو إرسال رابط الإعلان.',
}


def route_message(body):
    text = body.message.strip()
    if (re.search(r'\b(?:inventory|available units)\b', text, re.I) and re.search(r'\b(?:live|now|current|today)\b', text, re.I)) or re.search(r'الوحدات المتاحة.*(?:حالياً|حاليا|اللحظة)', text):
        return (('I only have dated source snapshots, so I cannot confirm live inventory or the number of units available right now.' if body.language == 'en' else
                 'لدي لقطات مؤرخة من المصادر فقط، لذلك لا أستطيع تأكيد المخزون المباشر أو عدد الوحدات المتاحة الآن.'), 'insufficient_evidence')
    # Narrow task patterns avoid rejecting legitimate property questions by keyword alone.
    off_topic = r'\b(?:write|generate|debug)\b.{0,35}\b(?:python|javascript|code|poem|essay)\b|\b(?:recipe|football score|weather forecast|capital of france)\b|اكتب.{0,25}(?:قصيدة|كود)|وصفة طبخ|نتيجة المباراة'
    if re.search(off_topic, text, re.I):
        return SCOPE[body.language], 'out_of_scope'
    previous = [m.content for m in body.history if m.role == 'user']
    context = ' '.join(previous[-2:] + [text])
    if re.search(r'\btrump\b|ترامب', text, re.I) and not re.search(
        r'dubai|jeddah|qatar|simaisma|oman|aida|maldives|riyadh|rayana|دبي|جدة|قطر|سميسمة|عمان|عايدة|مالديف|الرياض|رايانا', context, re.I
    ) and not re.search(r'\ball\b|compare|comparison|جميع|كل|قارن|مقارنة', text, re.I):
        return (('Which Trump-branded project and location do you mean?' if body.language == 'en' else
                 'أي مشروع يحمل علامة ترامب تقصد، وفي أي موقع؟'), 'clarification')
    vague = r'(?:what(?:\s+is|\s+are|\x27s)?\s+(?:the\s+)?(?:price|prices|location|amenities|completion date)|how much(?:\s+is\s+it)?|tell me more|where is it|ما السعر|كم السعر|كم سعره|أين يقع|اين يقع|ما المرافق)\s*[?؟.!]*'
    if not previous and re.fullmatch(vague, text, re.I):
        return CLARIFY[body.language], 'clarification'
    return None
