"""نماذج البيانات لأتمتة التسويق بالعمولة على أمازون."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Product:
    """نموذج بيانات المنتج."""

    name: str
    affiliate_link: str
    category: str = ""
    description: str = ""
    price: Optional[float] = None
    discount: Optional[int] = None
    use_case: str = ""


@dataclass
class Post:
    """نموذج بيانات المنشور."""

    content: str
    hashtags: list[str] = field(default_factory=list)
    language: str = "ar"
    scenario: str = "product_review"

    def full_text(self) -> str:
        """إرجاع النص الكامل للمنشور مع الهاشتاقات."""
        tags = " ".join(self.hashtags)
        if tags:
            return f"{self.content}\n\n{tags}"
        return self.content
