"""Generate fictional fixtures, never substitute these for collected evidence."""
import hashlib
import json
from pathlib import Path


def main():
    records = [
        ("dar", "en", "https://darglobal.co.uk/", "FICTIONAL · Dar Global example", "Fictional demonstration only, not real Dar Global information. In this test scenario Dar Global develops the invented Cedar Bay project in the imaginary city of Noor. Cedar Bay offers fictional waterfront villas, a community garden and walking trails. The made-up completion date is 2030. This fixture contains no real prices or available inventory."),
        ("dar", "ar", "https://darglobal.co.uk/ar", "خيالي · مثال دار جلوبال", "عرض خيالي فقط، وليس معلومات حقيقية عن دار جلوبال. في هذا السيناريو التجريبي تطور دار جلوبال مشروع خليج الأرز الخيالي في مدينة نور الوهمية. يقدم خليج الأرز فللاً خيالية على الواجهة البحرية وحديقة مجتمعية ومسارات للمشي. تاريخ الإنجاز المفترض هو 2030. لا تتضمن هذه البيانات أسعاراً حقيقية أو وحدات متاحة."),
        ("wasalt", "en", "https://wasalt.sa/en", "FICTIONAL · Wasalt example", "Fictional demonstration only, not real Wasalt information. In this test scenario Wasalt is a fictional property discovery platform. Its invented service Demo Match helps users explore example apartments and compare property types in the imaginary city of Noor. Users can filter by property type and fictional city. No real listings, prices, contact details or availability are included. The fictional Dar Global is a project developer; fictional Wasalt is a discovery platform."),
        ("wasalt", "ar", "https://wasalt.sa/ar", "خيالي · مثال وصلت", "عرض خيالي فقط، وليس معلومات حقيقية عن وصلت. في هذا السيناريو التجريبي وصلت منصة خيالية لاكتشاف العقارات. تساعد خدمة المطابقة التجريبية الوهمية المستخدمين على استكشاف شقق نموذجية ومقارنة أنواع العقارات في مدينة نور الخيالية. يمكن التصفية حسب نوع العقار والمدينة الوهمية. لا توجد إعلانات أو أسعار أو بيانات اتصال أو معلومات توافر حقيقية. دار جلوبال الخيالية مطور مشاريع، ووصلت الخيالية منصة اكتشاف عقارات."),
    ]
    target = Path("data/fixtures/corpus.jsonl")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(json.dumps({"company": company, "language": language,
        "url": url, "title": title, "text": text, "synthetic": True,
        "collected_at": "2026-10-23T00:00:00Z", "content_hash": hashlib.sha256(text.encode()).hexdigest()}, ensure_ascii=False)
        for company, language, url, title, text in records) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
