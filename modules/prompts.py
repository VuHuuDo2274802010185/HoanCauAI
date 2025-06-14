# modules/prompts.py

CV_EXTRACTION_PROMPT = (
    "Bạn là trợ lý AI chuyên trích xuất thông tin từ CV. "
    "Hãy trả về JSON với các khóa: ten, email, dien_thoai, hoc_van, kinh_nghiem. "
    "Ví dụ:\n"
    "```json\n"
    '{\n'
    '  "ten": "Nguyen Van A",\n'
    '  "email": "a.van.nguyen@example.com",\n'
    '  "dien_thoai": "+84 912345678",\n'
    '  "hoc_van": "Đại học Bách Khoa TP.HCM, CNTT",\n'
    '  "kinh_nghiem": "3 năm tại Công ty XYZ"\n'
    "}\n"
    "```"
)
